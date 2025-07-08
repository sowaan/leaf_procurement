// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leaf Procurement Settings", {
	refresh(frm) {

	},
    company_name(frm) {
        frm.set_value('location_warehouse', null);  // Clear field
        frm.set_query('location_warehouse', () => {
            return {
                filters: {
                    company: frm.doc.company_name
                }
            };
        });
    },
    setup: function(frm) {
        // Only runs once on form load
        frm.set_query('rejected_invoice_item', () => {
            return {
                filters: {
                    item_group: 'Services'
                }
            };
        });
        frm.set_query('transport_charges_item', () => {
            return {
                filters: {
                    item_group: 'Services'
                }
            };
        });
        frm.set_query('default_item', () => {
            return {
                filters: {
                    item_group: 'Products'
                }
            };
        });        
    },    
    take_backup(frm) {
        frappe.call({
            method: 'leaf_procurement.backup_utils.take_backup_now',
            callback: function (r) {
                frappe.msgprint(r.message);
            }
        });
    }
});
