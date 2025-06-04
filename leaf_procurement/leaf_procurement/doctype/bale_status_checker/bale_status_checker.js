// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bale Status Checker", {
	refresh(frm) {

	},
    check_status(frm){
        if (!frm.doc.bale_barcode) {
            frappe.msgprint("Please enter a Bale Barcode");
            return;
        }

        frappe.call({
            method: "leaf_procurement.leaf_procurement.api.barcode.get_bale_record_status",
            args: {
                bale_barcode: frm.doc.bale_barcode
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value("in_bale_registration", r.message.in_bale_registration);
                    frm.set_value("bale_registration_name", r.message.bale_registration_name);
                    frm.set_value("in_bale_purchase", r.message.in_bale_purchase);
                    frm.set_value("bale_purchase_name", r.message.bale_purchase_name);
                    frm.set_value("in_bale_weight", r.message.in_bale_weight);
                    frm.set_value("bale_weight_info_name", r.message.bale_weight_info_name);
                    frm.set_value("in_purchase_invoice", r.message.in_purchase_invoice);
                    frm.set_value("purchase_invoice_name", r.message.purchase_invoice_name);
                    frm.set_value("in_gtn", r.message.in_gtn);
                    frm.set_value("goods_transfer_note_name", r.message.goods_transfer_note_name);
                    frm.set_value("in_grn", r.message.in_grn);
                    frm.set_value("goods_receiving_note_name", r.message.goods_receiving_note_name);
                }
            }
        });       
    }
});

