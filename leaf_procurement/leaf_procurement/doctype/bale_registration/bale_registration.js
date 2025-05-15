// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bale Registration", {
	refresh(frm) {

	},
    scan_barcode: function(frm) {
        let barcode = frm.doc.scan_barcode;
        let expected_length = parseInt(frm.doc.barcode_length);
    
        if (barcode && expected_length && barcode.length === expected_length)  {
            // Check if barcode already exists in the child table
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
        }
    },    
    onload: function(frm) {
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
