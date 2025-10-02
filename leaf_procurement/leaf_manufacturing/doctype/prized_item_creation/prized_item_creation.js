// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Prized Item Creation", {
    refresh(frm) {
        frm.page.sidebar.hide();
    },
    onload: function (frm) {

        frm.page.sidebar.hide();

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Leaf Procurement Settings',
                name: 'Leaf Procurement Settings'
            },
            callback: function (r) {
                if (r.message) {
                    frm.set_value('item', r.message.processed_item);
                } else {
                    reject("Could not fetch settings");
                }
            }
        });

    },
    process_order: function(frm) {
        if (frm.doc.process_order) {
            frappe.call({
                method: "leaf_procurement.leaf_manufacturing.doctype.prized_item_creation.prized_item_creation.get_process_order_output",
                args: {
                    process_order: frm.doc.process_order
                },
                callback: function(r) {
                    console.log('value of r', r);
                    if (r.message) {
                        frm.set_value("total_output", r.message);
                    }
                    else{
                        frm.set_value("total_output", 0);
                    }
                }
            });
        }
    }
});


/*
    * Update average when quantity or kgs changes
*/
frappe.ui.form.on("Prized Item Creation Entry", {
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