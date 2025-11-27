// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Goods Receiving Note", {
    onload(frm) {
        // Disable click on grid rows to prevent popup
        const grid = frm.fields_dict.detail_table?.grid;
        if (grid && grid.wrapper) {
            grid.wrapper.on('click', '.grid-row', function (e) {
                e.stopPropagation();
                e.preventDefault();
            });
        }

        frm.set_query('gtn_number', function () {
            return {
                query: 'leaf_procurement.leaf_procurement.api.bale_purchase_utils.get_free_gtn'
            };
        });


        if (!frm.is_new()) return;

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Leaf Procurement Settings',
                name: 'Leaf Procurement Settings'
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value('company', r.message.company_name);
                    frm.set_value('location_warehouse', r.message.location_warehouse);
                    frm.set_value('barcode_length', r.message.barcode_length);
                    frm.set_value('default_item', r.message.default_item);
                }
            }
        });
    },
    refresh(frm) {
        //hide_grid_controls(frm);
        // frm.set_df_property('detail_table', 'read_only', 1);
        frm.refresh_field('detail_table'); // important to apply read-only       
    },
    onload_post_render(frm) {
        //hide_grid_controls(frm);
    },
    scan_barcode(frm) {
        const barcode = frm.doc.scan_barcode;
        let expected_length = parseInt(frm.doc.barcode_length);

        if (!barcode) return;

        // Check if the barcode is numeric
        if (!/^\d+$/.test(barcode)) {
            frappe.msgprint(__('Barcode must be numeric.'));
            frm.set_value('scan_barcode', '');
            return;
        }

        if (expected_length && barcode.length !== expected_length) {
            //frappe.msgprint(__('Barcode must be exactly {0} digits.', [expected_length]));
            return;
        }


        // Check for duplicate barcode
        const exists = frm.doc.detail_table.some(row => row.bale_barcode === barcode);
        if (exists) {
            frappe.show_alert({
                message: `Barcode "${barcode}" is already scanned.`,
                indicator: 'red' // You can use 'orange', 'green', etc. based on severity
            });
        } else {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Goods Transfer Note',
                    name: frm.doc.gtn_number
                },
                callback: function (r) {
                    if (r.message) {
                        const hasbarcode = r.message.bale_registration_detail.filter(row => row.bale_barcode === barcode);
                        if (hasbarcode.length > 0) {
                            hasbarcode.forEach(item => {
                                const child = frm.add_child('detail_table');
                                child.bale_barcode = item.bale_barcode;
                                child.weight = item.weight;
                                child.rate = item.rate;
                                child.lot_number = item.lot_number;
                                child.item_grade = item.item_grade;
                                child.item_sub_grade = item.item_sub_grade;
                                child.reclassification_grade = item.reclassification_grade;
                            });
                            frm.refresh_field('detail_table');
                        } else {
                            frappe.show_alert({
                                message: `No details found for barcode "${barcode}" in GTN ${frm.doc.gtn_number}.`,
                                indicator: 'orange' // You can use 'green', 'red', 'blue', etc.
                            });
                        }
                    } else {
                        frappe.show_alert({
                            message: __('No details found for the provided GTN number.'),
                            indicator: 'orange' // Optional: color of the alert
                        });
                    }
                }
            });
        }
        frm.set_value('scan_barcode', '');  // Clear scan input
    },

    gtn_number(frm) {
        if (!frm.doc.gtn_number) return;

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Goods Transfer Note',
                name: frm.doc.gtn_number
            },
            callback: function (r) {
                if (!frm.doc.location_warehouse && r.message ) {
                    frm.set_value("location_warehouse", r.message.receiving_location);
                    frm.set_value("dispatch_location", r.message.location_warehouse);
                    frm.set_value("transit_location", r.message.transit_location);
                }
                if (r.message) {

                    frm.clear_table('detail_table');
                    r.message.bale_registration_detail.forEach(item => {
                        const child = frm.add_child('detail_table');
                        child.bale_barcode = item.bale_barcode;
                        child.weight = item.weight;
                        child.rate = item.rate;
                        child.lot_number = item.lot_number;
                        child.item_grade = item.item_grade;
                        child.item_sub_grade = item.item_sub_grade;
                        child.reclassification_grade = item.reclassification_grade;
                    });
                    frm.refresh_field('detail_table');
                } else {
                    frappe.msgprint(__('No details found for the provided GTN number.'));
                }
            }
        });
    }
});
frappe.ui.form.on('Goods Transfer Note Items', {
    delete_row(frm, cdt, cdn) {
        frappe.model.clear_doc(cdt, cdn);  // delete the row
        frm.refresh_field('detail_table');

        if (cur_dialog) {
            cur_dialog.hide();
        }

        // Remove any lingering modal backdrop
        $('.modal-backdrop').remove();
    }
});
