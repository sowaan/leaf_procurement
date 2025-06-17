// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bale Registration", {
    on_submit: function (frm) {
        frappe.msgprint({
            title: __('Success'),
            message: __('Record submitted successfully.'),
            indicator: 'green'
        });

        // Use frappe.new_doc in a safe callback
        setTimeout(() => {
            if (frm && frm.doc && frm.doc.doctype === 'Bale Registration') {
                frappe.new_doc('Bale Registration');
            }
        }, 1000); // Wait 1 second

    },
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.fields_dict['bale_registration_detail'].grid.update_docfield_property(
                'delete_row', 'hidden', 1
            );
        } else {
            if (!frm.doc.bale_status)
                frm.set_value('bale_status', 'In Registration');
        }
    },
    after_save(frm) {
        if (frm.doc.docstatus === 1) {
            frm.reload_doc();
        }
    },
    scan_barcode: function (frm) {
        let barcode = frm.doc.scan_barcode;
        let expected_length = parseInt(frm.doc.barcode_length);

        // Ensure barcode is present
        if (!barcode) return;



        // Check length
        if (expected_length && barcode.length !== expected_length) {
            //frappe.msgprint(__('Barcode must be exactly {0} digits.', [expected_length]));
            return;
        }

        // Check if the barcode is numeric
        if (!/^\d+$/.test(barcode)) {
            frappe.msgprint(__('Barcode must be numeric.'));
            frm.set_value('scan_barcode', '');
            return;
        }

        if (frm.doc.remaining_bales <= 0) {
            frappe.show_alert({ message: __('Cannot add more barcodes, Lot already completed.'), indicator: 'orange' });
            return;
        }
        // Check if barcode already exists in child table
        let exists = frm.doc.bale_registration_detail.some(row => row.bale_barcode === barcode);
        if (exists) {
            frappe.show_alert({ message: __('This barcode already exists.'), indicator: 'red' });
            return;
        } else {
            // Add new row to child table
            let row = frm.add_child('bale_registration_detail', {
                bale_barcode: barcode
            });
            frm.refresh_field('bale_registration_detail');
            recalculate_bale_counts(frm);

        }

        // Clear the input field
        frm.set_value('scan_barcode', '');

    },
    onload: function (frm) {
        frm.page.sidebar.toggle(false);
        if (frm.doc.docstatus === 1) {
            frm.fields_dict['bale_registration_detail'].grid.update_docfield_property(
                'delete_row', 'hidden', 1
            );
        }

        if (!frm.is_new()) return;
        if (frm.doc.date) {
            update_lot_counter(frm);
        }
        //validate_day_status(frm);        
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
                    frm.set_value('lot_size', r.message.lot_size || 0);
                    frm.set_value('bales_in_lot', frm.doc.bale_registration_detail.length || 0);
                    frm.set_value('remaining_bales', (r.message.lot_size || 0) - (frm.doc.bale_registration_detail.length || 0));
                    frm.set_value('item', r.message.default_item);
                    frm.set_value('barcode_length', r.message.barcode_length);

                }
            }
        });
        frm.set_value('bale_status', 'In Registration');
        

    },
    date: function (frm) {
        validate_day_status(frm);
        if (frm.doc.date) {
            update_lot_counter(frm);
        }
    },
    supplier_grower: function (frm) {
        if (frm.doc.supplier_grower) {
            frappe.db.get_value('Supplier', frm.doc.supplier_grower, 'custom_quota_allowed')
                .then(r => {
                    if (r && r.message) {
                        frm.set_value('remaining_weight', r.message.custom_quota_allowed);
                    }
                });
        }
    },
    bale_registration_detail_on_form_rendered: function (frm) {
        // trigger recalc when form is rendered
        recalculate_bale_counts(frm);
    },

    validate: function (frm) {
        recalculate_bale_counts(frm);
    },

    // recalculate_bale_counts: function(frm) {
    //     const balesCount = frm.doc.bale_registration_detail.length;
    //     const lotSize = frm.doc.lot_size || 0;

    //     frm.set_value('bales_in_lot', balesCount);
    //     frm.set_value('remaining_bales', lotSize - balesCount);
    // },

});

function update_lot_counter(frm) {
    frappe.call({
        method: "frappe.client.get_count",
        args: {
            doctype: "Bale Registration",
            filters: {
                date: frm.doc.date
            }
        },
        callback: function (r) {
            if (r.message !== undefined) {
                const count = r.message + 1;
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
                        Lot No: ${count}
                    </div>
                `;
                frm.set_df_property('lot_counter', 'options', html);
                frm.refresh_field('lot_counter');
            }
        }
    });
}
frappe.ui.form.on('Bale Registration Detail', {
    delete_row(frm, cdt, cdn) {
        frappe.model.clear_doc(cdt, cdn);  // delete the row
        frm.refresh_field('bale_registration_detail');

        if (cur_dialog) {
            cur_dialog.hide();
        }

        // Remove any lingering modal backdrop
        $('.modal-backdrop').remove();
    }
});


function validate_day_status(frm) {
    if (!frm.doc.date) return;

    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Day Setup",
            filters: {
                date: frm.doc.date,
                day_open_time: ["is", "set"],
                day_close_time: ["is", "not set"]
            },
            fields: ["name"]
        },
        callback: function (r) {
            const is_day_open = r.message && r.message.length > 0;
            frm.set_value('day_setup', is_day_open ? r.message[0].name : null);

            // Enable or disable fields based on day status
            //toggle_fields(frm, is_day_open);

            if (!is_day_open) {
                frappe.msgprint({
                    title: __("Day Not Open"),
                    message: __("⚠️ You cannot register bales because the day is either not opened or already closed."),
                    indicator: 'red'
                });
            }
        }
    });
}

function toggle_fields(frm, enable) {
    frm.toggle_display('bale_registration_detail', enable);
    frm.toggle_display('scan_barcode', enable);
    // Optionally, clear any error messages or refresh the field
    frm.refresh_field('bale_registration_detail');
    frm.refresh_field('scan_barcode');

}

function recalculate_bale_counts(frm) {
    const balesCount = frm.doc.bale_registration_detail.length;
    const lotSize = frm.doc.lot_size || 0;

    frm.set_value('bales_in_lot', balesCount);
    frm.set_value('remaining_bales', lotSize - balesCount);
}