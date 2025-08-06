// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("GTN Audit Sync Tool", {
    refresh(frm) {
        frm.add_custom_button("🔁 Sync Missing GTN in Audit", () => {
          //  frappe.show_progress("Syncing GTNs", 0, 100, "Starting...");

            frappe.call({
                method: "leaf_procurement.leaf_procurement.utils.sync_up.run_gtn_audit_sync_tool",
                freeze: true,
                freeze_message: "Please wait. Syncing GTN Audit...",
                callback: function (r) {
                    frappe.hide_progress();
                    if (!r.exc) {
                        frappe.msgprint("✅ Sync completed successfully.");
                        frm.reload_doc();
                    } else {
                        frappe.msgprint("❌ Sync failed. Check logs.");
                    }
                }
            });
        });
    }
    // refresh(frm) {
    //     frm.add_custom_button("🔁 Sync Missing GTN in Audit", () => {
    //         frappe.call({
    //             method: "leaf_procurement.leaf_procurement.utils.sync_up.run_gtn_audit_sync_tool",
    //             callback: function (r) {
    //                 if (!r.exc) {
    //                     frappe.msgprint("Sync completed successfully.");
    //                     frm.reload_doc();
    //                 }
    //             }
    //         });
    //     });
    // }
});
