// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt
function update_gtn_counter(frm) {
    frappe.call({
        method: "frappe.client.get_count",
        args: {
            doctype: "Goods Transfer Note",
            filters: {
                date: frm.doc.date
            }
        },
        callback: function(r) {
            if (r.message !== undefined) {
                const count = r.message+1;
                const html = `
                    <div style="
                        font-size: 16px;
                        font-weight: bold;
                        color: #1F7C83;
                        background-color: #E6F9FB;
                        padding: 20px;
                        text-align: center;
                        border-radius: 10px;
                        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
                    ">
                        GTN No: ${count}
                    </div>
                `;
                frm.set_df_property('gtn_counter', 'options', html);
                frm.refresh_field('gtn_counter');
            }
        }
    });
}

async function get_latest_open_day() {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Day Setup",
                filters: {
                    day_open_time: ["is", "set"],
                    day_close_time: ["is", "not set"]
                },
                fields: ["name", "date"],
                order_by: "date desc",
                limit_page_length: 1
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    resolve(r.message[0].date);
                } else {
                    resolve(null);  // No open day
                }
            },
            error: function (err) {
                reject(err);
            }
        });
    });
}

frappe.ui.form.on("Goods Transfer Note", {
    validate: async function (frm)
    {
        const open_day_date = await get_latest_open_day();
        if (!open_day_date) {
            frappe.throw(__("⚠️ You cannot save because the day is not opened."));
        }
    
        
    },
    date:function (frm){
        update_gtn_counter(frm);
    },
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.fields_dict['bale_registration_detail'].grid.update_docfield_property(
                'delete_row', 'hidden', 1
            );
        }
    },
    scan_barcode: function (frm) {
        let barcode = frm.doc.scan_barcode;
        let itemcode = frm.doc.default_item
        let expected_length = parseInt(frm.doc.barcode_length);

        // Ensure barcode is present
        if (!barcode) return;

        // Check if the barcode is numeric
        if (!/^\d+$/.test(barcode)) {
            frappe.msgprint(__('Barcode must be numeric.'));
            frm.set_value('scan_barcode', '');
            return;
        }

        // Check length
        if (expected_length && barcode.length !== expected_length) {
            //frappe.msgprint(__('Barcode must be exactly {0} digits.', [expected_length]));
            return;
        }

        // Check if barcode already exists in child table
        let exists_in_grid = frm.doc.bale_registration_detail.some(row => row.bale_barcode === barcode);
        if (exists_in_grid) {
            frappe.show_alert({ message: __('This Bale Barcode is already scanned'), indicator: 'orange' });
            frm.set_value('scan_barcode', '');
            return;
        }


        // Now check if barcode already exists in Batch table (invoice generated)
        frappe.call({
            method: 'leaf_procurement.leaf_procurement.api.barcode.get_invoice_item_by_barcode',
            args: { itemcode: itemcode, barcode: barcode },
            callback: function (r) {

                if (r.message && r.message.exists) {
                    let row = frm.add_child('bale_registration_detail', {
                        bale_barcode: barcode,
                        weight: r.message.qty,
                        rate: r.message.rate,
                        lot_number: r.message.lot_number,
                        item_grade: r.message.grade,
                        item_sub_grade: r.message.sub_grade
                    });
                    frm.refresh_field('bale_registration_detail');
                } else {
                    frappe.show_alert({ message: __('This barcode has not been invoiced or has been rejected during invoice generation.'), indicator: 'orange' });
                    //frappe.msgprint(__('This barcode has not been invoiced or has been rejected during invoice generation.'));
                }

                frm.set_value('scan_barcode', '');
            }
        });
    },
    onload: async function (frm) {
        if (frm.doc.docstatus === 1) {
            frm.fields_dict['bale_registration_detail'].grid.update_docfield_property(
                'delete_row', 'hidden', 1
            );
        }
        if (!frm.is_new()) return;

        const open_day_date = await get_latest_open_day();
        if (open_day_date) {
            frm.set_value('date', open_day_date);
        } else {
            frappe.show_alert({
                message: __("⚠️ No open day found."),
                indicator: 'red'
            });
        }

        update_gtn_counter(frm);

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
                    frm.set_value('default_item', r.message.default_item);
                    frm.set_value('barcode_length', r.message.barcode_length);
                }
            }
        });



    },
    company(frm) {
        frm.set_value('receiving_location', null);  // Clear field
        frm.set_query('receiving_location', () => {
            return {
                filters: {
                    company: frm.doc.company
                }
            };
        });
        frm.set_value('transit_location', null);  // Clear field
        frm.set_query('transit_location', () => {
            return {
                filters: {
                    company: frm.doc.company
                }
            };
        });
    }
});
