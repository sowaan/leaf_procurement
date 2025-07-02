// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt
const sync_down_checkboxes = [
    "company_check",
    "fiscal_year",
    "warehouse",
    "quota_setup",
    "item",
    "item_grade",
    "item_sub_grade",
    "item_grade_price",
    "bale_status",
    "reclassification_grade",
    "transport_type"
];

frappe.ui.form.on("Leaf Sync Down", {
    refresh(frm) {
        // Add Sync Now button if any checkbox is checked
        if (sync_down_checkboxes.some(field => frm.doc[field])) {
            frm.add_custom_button("🚀 Sync Now", () => {
                trigger_sync(frm);
            }, "Actions");
        }
        frm.fields_dict.sync_down_select_all.df.label = frm.doc.sync_down_select_all ? 'Unselect All' : 'Select All';
    },
    sync_down_select_all(frm) {
        const is_checked = frm.doc.sync_down_select_all;
        frm.fields_dict.sync_down_select_all.df.label = is_checked ? 'Unselect All' : 'Select All';

        is_bulk_update = true;

        // Update all checkboxes without triggering events
        sync_down_checkboxes.forEach(field => {
            frm.doc[field] = is_checked;
        });

        // Refresh all checkbox fields at once
        frm.refresh_fields(sync_down_checkboxes);

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

function trigger_sync(frm) {
    const payload = {};
    let anyChecked = false;
    
    sync_down_checkboxes.forEach(field => {
        if (frm.doc[field]) {
            payload[field] = 1;
            anyChecked = true;
        }
    });

    if (!anyChecked) {
        frappe.msgprint("Please select at least one checkbox to sync.");
        return;
    }
    
    frappe.call({
        method: "leaf_procurement.leaf_procurement.utils.trigger_sync_up.trigger_sync_down",
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

frappe.realtime.on("sync_complete", function(data) {
    frappe.show_alert({
        message: `✅ Sync for ${data.doctype} completed.`,
        indicator: 'green'
    });
});
