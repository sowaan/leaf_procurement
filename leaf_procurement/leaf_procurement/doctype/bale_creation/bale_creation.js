// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bale Creation", {
	refresh(frm) {

	},
});

frappe.ui.form.on('Bale Creation Detail', {
    // bale_brcode: function(frm, cdt, cdn) {
    //     // you can leave this empty — we’ll generate it on add
    //     console.log("Bale Barcode field triggered from bale_barcode function");
    // },
    // form_render: function(frm) {
    //     // optional – only runs when table is rendered
    //     console.log("Bale Barcode field triggered from form_render function");
    // },
    // detail_table_add: function(frm, cdt, cdn) {
    //     // console.log("Bale Barcode field triggered from bale_creation_detail_add function");
    //     let row = locals[cdt][cdn];

    //     // ✅ Generate unique barcode — example using timestamp
    //     let timestamp = new Date().getTime();
    //     let prefix = "BRC-"; // Optional prefix
    //     row.bale_brcode = prefix + timestamp;

    //     // Refresh the field in UI
    //     frm.refresh_field("detail_table");
    // },

});

