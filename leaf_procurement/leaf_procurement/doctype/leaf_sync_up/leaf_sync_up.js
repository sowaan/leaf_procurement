// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leaf Sync Up", {
    refresh(frm) {
        update_sync_status_labels(frm);

        // Add Reload button
        frm.add_custom_button('🔄 Reload', () => {
            frm.reload_doc();
        });

        // Only show Sync Now if any checkbox is checked
        if (sync_up_checkboxes.some(field => frm.doc[field])) {
            const sync_btn = frm.add_custom_button("🚀 Sync Now", () => {
                // Prevent multiple clicks
                if (frm.sync_in_progress) return;

                frm.sync_in_progress = true;

                // Disable button + show spinner
                sync_btn.prop("disabled", true).html('🚀 Syncing... <span class="spinner-border spinner-border-sm ml-2" role="status" aria-hidden="true"></span>');

                // Start sync
                trigger_sync(frm, sync_btn);
            });
        }

        // Update select all/unselect label
        frm.fields_dict.sync_up_select_all.df.label = frm.doc.sync_up_select_all ? 'Unselect All' : 'Select All';
    },
    sync_up_select_all(frm) {
        const is_checked = frm.doc.sync_up_select_all;
        frm.fields_dict.sync_up_select_all.df.label = is_checked ? 'Unselect All' : 'Select All';

        is_bulk_update = true;

        sync_up_checkboxes.forEach(field => {
            frm.doc[field] = is_checked;
        });

        frm.refresh_fields(sync_up_checkboxes);

        is_bulk_update = false;
    },
    onload(frm) {
        // Filter out logs not from today
        frm.page.sidebar.toggle(false);
        if (frm.doc.sync_history && frm.doc.sync_history.length > 0) {
            const today = frappe.datetime.get_today();
            frm.doc.sync_history = frm.doc.sync_history.filter(row => {
                return frappe.datetime.obj_to_str(row.synced_at).startsWith(today);
            });
            frm.doc.sync_history.sort((a, b) => new Date(b.synced_at) - new Date(a.synced_at));

            frm.refresh_field("sync_history");
        }


    }
});

function trigger_sync(frm, btn) {
    const payload = {};
    let anyChecked = false;

    sync_up_checkboxes.forEach(field => {
        if (frm.doc[field]) {
            payload[field] = 1;
            anyChecked = true;
        }
    });

    if (!anyChecked) {
        frappe.msgprint("Please select at least one checkbox to sync.");
        if (btn) {
            btn.prop("disabled", false).text("🚀 Sync Now");
        }
        frm.sync_in_progress = false;
        return;
    }

    frappe.call({
        method: "leaf_procurement.leaf_procurement.utils.trigger_sync_up.trigger_sync_up",
        args: {
            values: JSON.stringify(payload)
        },
        freeze: true,
        freeze_message: "🚀 Syncing records in background...",
        callback: function (r) {
            frappe.show_alert("✅ Sync started. You will be notified when it's complete.");
        }
    });
}

// frappe.realtime.on("sync_complete", function(data) {
//     frappe.show_alert({
//         message: `✅ Sync for ${data.doctype} completed.`,
//         indicator: 'green'
//     });
// });
frappe.realtime.on("sync_complete", function (data) {
    frappe.show_alert({
        message: "🎉 Sync Complete!",
        indicator: "green"
    });

    const frm = frappe.active_form || cur_frm;

    if (frm) {
        frm.sync_in_progress = false;

        // Ensure the document exists and is saved
        if (!frm.is_new()) {
            frm.reload_doc();
        } else {
            frm.refresh();
        }
    }
});

const sync_up_checkboxes = [
    "supplier",
    "driver",
    "bale_audit",
    "bale_registration",
    "purchase_invoice",
    "goods_transfer_note",
    //"goods_receiving_note"
];

const doctype_map = {
    "supplier": "Supplier",
    "driver": "Driver",
    "bale_audit": "Bale Audit",
    "bale_registration": "Bale Registration",
    "purchase_invoice": "Purchase Invoice",
    "goods_transfer_note": "Goods Transfer Note",
    "goods_receiving_note": "Goods Receiving Note"
};

function update_sync_status_labels(frm) {
    sync_up_checkboxes.forEach(fieldname => {
        const label_field = `${fieldname}_label`;
        const is_checked = frm.doc[fieldname];

        // if (!is_checked) {
        //     update_label_html(frm, label_field, "press save", "blue");
        //     return;
        // }

        const doctype = doctype_map[fieldname];

        frappe.call({
            method: "frappe.client.get_count",
            args: {
                doctype: doctype,
                filters: {
                    custom_is_sync: 0,
                    docstatus: ["<", 2]
                }
            },
            callback: function (r) {
                if (!r.exc) {
                    const count = r.message;
                    const color = count > 0 ? "red" : "green";
                    const label = `${count} to sync`;
                    update_label_html(frm, label_field, label, color);
                }
            }
        });
    });
}

function update_label_html(frm, label_field, text, color) {
    const html = `<span style="color:${color}; font-weight:bold; margin:4px 0;">${text}</span>`;
    if (frm.fields_dict[label_field]) {
        frm.fields_dict[label_field].$wrapper.html(html);
    } else {
        console.log(`Label field ${label_field} not found in form.`);
    }
}
