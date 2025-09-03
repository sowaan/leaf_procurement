// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bale Audit Change", {
	refresh(frm) {

	},
    change_weight(frm) {
        if (frm.is_new()) {
            frappe.msgprint("⚠️ Please save the record first before changing weight.");
            return;
        }

        let values = frm.doc;

        frappe.call({
            method: 'leaf_procurement.leaf_procurement.utils.audit_utility.change_audit_weight',
            args: {
                parent: frm.doc.name,              // valid docname after save
                barcode: values.bale_barcode,
                new_weight: values.new_weight
            },
            callback: function (r) {
                if (!r.exc) {
                    frappe.msgprint(r.message || "✅ Weight updated successfully.");
                    frm.reload_doc();
                }
            }
        });
    }   
});
