// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Item Grade Price", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Item Grade Price', {
    company(frm) {
        frm.set_value('location_warehouse', null);  // Clear field
        frm.set_query('location_warehouse', () => {
            return {
                filters: {
                    company: frm.doc.company
                }
            };
        });
    },    
    item_grade(frm) {
        frm.set_value('item_sub_grade', null);  // Clear field
        frm.set_query('item_sub_grade', () => {
            return {
                filters: {
                    item_grade: frm.doc.item_grade
                }
            };
        });
    }
});
