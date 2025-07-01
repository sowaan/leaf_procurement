// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leaf Sync Up", {
	refresh(frm) {
        sync_up_status_update(frm)
	},
});

const sync_up_checkboxes = [
    "supplier",
    "driver",
    //"bale_audit",
    "bale_registration",
    "purchase_invoice",
    "goods_transfer_note",
    //"goods_receiving_note"
];

function sync_up_status_update(frm)
{
    // Mapping checkboxes to Doctypes
    const doctype_map = {
        "supplier": "Supplier",
        "driver": "Driver",
        "bale_audit": "Bale Audit",
        "bale_registration": "Bale Registration",
        "purchase_invoice": "Purchase Invoice",
        "goods_transfer_note": "Goods Transfer Note",
        "goods_receiving_note": "Goods Receiving Note"
    };

    sync_up_checkboxes.forEach(fieldname => {
        if (frm.doc[fieldname]) {
            const doctype = doctype_map[fieldname];
            frappe.call({
                method: "frappe.client.get_count",
                args: {
                    doctype: doctype,
                    filters: {
                        "custom_is_sync": 0,
                        "docstatus": ["<", 2]
                    }
                },
                callback: function (r) {
                    if (!r.exc) {
                        const label_field = fieldname + "_label";
                        console.log(label_field, " : ", r.message);
                        let count = r.message;
                        let color = count > 0 ? "red" : "green";
                        let html = `<span style="color:${color}; font-weight: bold;margin-top:1px; margin-bottom:10px">${count} to sync</span>`;

                        frm.fields_dict[label_field].$wrapper.html(html);
                    }

                }
            });
        }
        else{
                const label_field = fieldname + "_label";
            console.log(label_field);
                    let color = "blue";
                let html = `<span style="color:${color}; font-weight: bold;margin-top:1px; margin-bottom:10px">press save</span>`;

                frm.fields_dict[label_field].$wrapper.html(html);
        }


    });
}