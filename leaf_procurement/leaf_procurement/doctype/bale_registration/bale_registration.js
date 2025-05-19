// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bale Registration", {
	refresh(frm) {
        
	},

    scan_barcode: function(frm) {
        let barcode = frm.doc.scan_barcode;
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
        let exists = frm.doc.bale_registration_detail.some(row => row.bale_barcode === barcode);
        if (exists) {
            frappe.msgprint(__('This barcode already exists.'));
        } else {
            // Add new row to child table
            let row = frm.add_child('bale_registration_detail', {
                bale_barcode: barcode
            });
            frm.refresh_field('bale_registration_detail');
        }

        // Clear the input field
        frm.set_value('scan_barcode', '');
    },    
    onload: function(frm) {
        //validate_day_status(frm);        
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Leaf Procurement Settings',
                name: 'Leaf Procurement Settings'
            },
            callback: function(r) {
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


    },
    date: function(frm) {
        validate_day_status(frm);
    },    
    supplier_grower: function(frm) {
        if (frm.doc.supplier_grower) {
            frappe.db.get_value('Supplier', frm.doc.supplier_grower, 'custom_quota_allowed')
                .then(r => {
                    if (r && r.message) {
                        frm.set_value('remaining_weight', r.message.custom_quota_allowed);
                    }
                });
        }
    },    
    bale_registration_detail_on_form_rendered: function(frm) {
        // trigger recalc when form is rendered
        frm.trigger("recalculate_bale_counts");
    },

    validate: function(frm) {
        frm.trigger("recalculate_bale_counts");
    },

    recalculate_bale_counts: function(frm) {
        const balesCount = frm.doc.bale_registration_detail.length;
        const lotSize = frm.doc.lot_size || 0;

        frm.set_value('bales_in_lot', balesCount);
        frm.set_value('remaining_bales', lotSize - balesCount);
    },

});

function validate_day_status(frm) {
    console.log('here i am ');
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
        callback: function(r) {
            const is_day_open = r.message && r.message.length > 0;

            // Enable or disable fields based on day status
            toggle_fields(frm, is_day_open);

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
    hide_grid_controls(frm);
}
function hide_grid_controls(frm) {
    const grid_field = frm.fields_dict.bale_registration_detail;
    if (grid_field && grid_field.grid && grid_field.grid.wrapper) {
        grid_field.grid.wrapper
            .find('.grid-add-row, .grid-remove-rows, .btn-open-row')
            .hide();
    }
}
