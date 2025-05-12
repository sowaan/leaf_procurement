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
    }    
});
