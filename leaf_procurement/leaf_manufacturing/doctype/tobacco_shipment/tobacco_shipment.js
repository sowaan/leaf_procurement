// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tobacco Shipment", {
	refresh(frm) {
        frm.page.sidebar.hide();
	},
    onload: function (frm) {
        frm.page.sidebar.hide();
    },
});

frappe.ui.form.on("Tobacco Shipment Detail", {
    refresh(frm) {

    },
    quantity: function (frm, cdt, cdn) {
        update_average(cdt, cdn);
    },
    kgs: function (frm, cdt, cdn) {
        update_average(cdt, cdn);
        update_amount(cdt, cdn);
    },
    standard_rate: function (frm, cdt, cdn) {
        update_amount(cdt, cdn);
    }
});

function update_average(cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (row.quantity && row.kgs) {
        row.average = flt(row.kgs) / flt(row.quantity);
    } else {
        row.average = 0;
    }
    frappe.model.set_value(cdt, cdn, "average", row.average);
}

function update_amount(cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (row.standard_rate && row.kgs) {
        row.amount = flt(row.standard_rate) * flt(row.kgs);
    }
}
function update_average(cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (row.quantity && row.kgs) {
        row.average = flt(row.kgs) / flt(row.quantity);
    } else {
        row.average = 0;
    }
    frappe.model.set_value(cdt, cdn, "average", row.average);
}