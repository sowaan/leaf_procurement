// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bale Weight Info", {
    bale_registration_code(frm) {
        if (!frm.doc.bale_registration_code) return;

        frappe.call({
            method: 'leaf_procurement.leaf_procurement.api.bale_purchase_utils.get_registered_bale_count',
            args: {
                bale_registration_code: frm.doc.bale_registration_code
            },
            callback(r) {
                if (r.message !== undefined) {
                    let count = parseInt(r.message); 
                    if (!isNaN(count)) {
                        frm.doc.total_bales = count;
                        frm.doc.remaining_bales = count;
                        frm.refresh_field('total_bales');
                        frm.refresh_field('remaining_bales');
        
                        frm.clear_table('detail_table'); // optional: clear before add
                        for (let i = 0; i < count; i++) {
                            let row = frm.add_child('detail_table');
                            row.index = i + 1;
                        }
                        frm.refresh_field('detail_table');
        
                        hide_grid_controls(frm);
                    } else {
                        frappe.msgprint("Returned value is not a number");
                    }                        
                }
            }
        });

           
    },        
    refresh: function(frm){
        hide_grid_controls(frm);

    },
    onload: function(frm) {
        
        //override bale_registration_code query to load 
        //bale registration codes with no purchase record
        frm.set_query('bale_registration_code', function() {
            return {
                query: 'leaf_procurement.leaf_procurement.api.bale_weight_utils.get_available_bale_registrations'
            };
        });
        
        // Set query filter for 'item_sub_grade' field in child table
        frm.fields_dict['detail_table'].grid.get_field('item_sub_grade').get_query = function(doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            return {
                filters: {
                    item_grade: child.item_grade
                }
            };
        };

        //get company and location records from settings
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
                    frm.set_value('item', r.message.default_item);    
                }
            }
        });            
    }        
});

frappe.ui.form.on("Bale Weight Detail", {
    refresh: function(frm){
        hide_grid_controls(frm);

    },    
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
    },
    bale_barcode(frm, cdt, cdn) {
        update_bale_counter(frm);
    },
    bale_purchase_detail_remove(frm) {
        update_bale_counter(frm);
    }        
});  

function hide_grid_controls(frm) {
    // Hide Add Row and Delete Rows buttons
    frm.fields_dict.detail_table.grid.wrapper
        .find('.grid-add-row, .grid-remove-rows, .btn-open-row')
        .hide();
}

function update_bale_counter(frm) {
    let total = frm.doc.total_bales;  // increment before recounting
    frm.doc.remaining_bales = total - (frm.doc.detail_table || []).length;
    frm.refresh_field('remaining_bales');
}


