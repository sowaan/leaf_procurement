// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Change Barcode", {
	refresh(frm) {

	},
    change_barcode(frm){
        values = frm.doc;

        frappe.call({
            method: 'leaf_procurement.leaf_procurement.utils.change_barcode_util.change_barcode',
            args: {
                old_barcode: values.old_barcode,
                new_barcode: values.new_barcode
            },
            callback: function (r) {
                if (r.message) {
                    frappe.msgprint(r.message);
                }
            }
        });              
    }
});
