    // Copyright (c) 2025, Sowaan and contributors
    // For license information, please see license.txt

    frappe.ui.form.on("Bale Purchase", {
        onload: function(frm) {
            // Set query filter for 'item_sub_grade' field in child table
            frm.fields_dict['detail_table'].grid.get_field('item_sub_grade').get_query = function(doc, cdt, cdn) {
                let child = locals[cdt][cdn];
                return {
                    filters: {
                        item_grade: child.item_grade
                    }
                };
            };
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
                        // frm.set_value('lot_size', r.message.lot_size || 0);
                        // frm.set_value('bales_in_lot', frm.doc.bale_registration_detail.length || 0);
                        // frm.set_value('remaining_bales', (r.message.lot_size || 0) - (frm.doc.bale_registration_detail.length || 0));
    
                    }
                }
            });            
        }        
    });

    frappe.ui.form.on("Bale Purchase Detail", {
        item_grade(frm, cdt, cdn) {
            frappe.model.set_value(cdt, cdn, 'item_sub_grade', '');
        },
        item_sub_grade: function(frm, cdt, cdn) {
            let row = locals[cdt][cdn];
    
            if (row.item_grade && row.item_sub_grade) {
                frappe.call({
                    method: "leaf_procurement.leaf_procurement.doctype.item_grade_price.item_grade_price.get_item_grade_price",
                    args: {
                        item_grade: row.item_grade,
                        item_sub_grade: row.item_sub_grade
                    },
                    callback: function(r) {
                        if (r.message !== undefined) {
                            frappe.model.set_value(cdt, cdn, "rate", r.message);
                        }
                    }
                });
            }
        }        
    });    




