// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bale Audit Change", {
	refresh(frm) {
        $(".layout-side-section").hide();   // hide sidebar
        $(".sidebar-toggle-btn").hide();    // hide toggle
	},
    bale_barcode(frm) {
        frm.set_value("new_bale_barcode", frm.doc.bale_barcode);
    },
    change_weight(frm) {
        if (frm.is_new()) {
            frappe.msgprint("⚠️ Please save the record first before changing weight.");
            return;
        }
        if (!frm.doc.bale_barcode || !frm.doc.new_bale_barcode || !frm.doc.new_weight) {
            frappe.throw("❌ Bale Barcode, New Bale Barcode and New Weight are required.");
        }
        let values = frm.doc;

        frappe.call({
            method: 'leaf_procurement.leaf_procurement.utils.audit_utility.change_audit_weight',
            args: {
                parent: frm.doc.name,              // valid docname after save
                barcode: values.bale_barcode,
                new_barcode: values.new_bale_barcode,
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
