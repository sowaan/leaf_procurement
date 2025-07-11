// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Change Abbr", {
	refresh(frm) {

	},
    change_abbr(frm){
        values = frm.doc;

        frappe.call({
            method: 'leaf_procurement.leaf_procurement.utils.change_abbr_util.change_abbr',
            args: {
                old_abbr: values.old_abbr,
                new_abbr: values.new_abbr
            },
            callback: function (r) {
                if (r.message) {
                    frappe.msgprint(r.message);
                }
            }
        });        
    }
});
