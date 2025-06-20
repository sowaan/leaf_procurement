// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

const sync_down_checkboxes = [
    "company_check",
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

const sync_up_checkboxes = [
    "supplier",
    "driver",
    "bale_audit",
    "bale_registration",
    "purchase_invoice",
    "goods_receiving_note",
    "goods_transfer_note"
];

let is_bulk_update = false;

frappe.ui.form.on("Leaf Procurement Sync Tool", {
    refresh(frm) {
        frm.fields_dict.sync_down_select_all.df.label = frm.doc.sync_down_select_all ? 'Unselect All' : 'Select All';
        frm.fields_dict.sync_up_select_all.df.label = frm.doc.sync_up_select_all ? 'Unselect All' : 'Select All';
    },

    sync_down(frm) {
        frappe.call({
            method: "leaf_procurement.leaf_procurement.doctype.leaf_procurement_sync_tool.leaf_procurement_sync_tool.sync_down",
            freeze: true,
            freeze_message: __('Syncing down data...'),
            callback: function (r) {
                if (r.message) {
                    frappe.show_alert({
                        message: __('Sync down completed successfully.'),
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: __('No data to sync down.'),
                        indicator: 'orange'
                    });
                }
            }
        });
    },

    sync_up(frm) {
        frappe.call({
            method: "leaf_procurement.leaf_procurement.doctype.leaf_procurement_sync_tool.leaf_procurement_sync_tool.sync_up",
            freeze: true,
            freeze_message: __('Syncing up data...'),
            callback: function (r) {
                if (r.message) {
                    frappe.show_alert({
                        message: __('Sync up completed successfully.'),
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: __('No data to sync up.'),
                        indicator: 'orange'
                    });
                }
            }
        });
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


    // Individual sync_down checkbox handlers
    // ...Object.fromEntries(
    //     sync_down_checkboxes.map(field => [
    //         field,
    //         function (frm) {
    //             if (is_bulk_update) return;

    //             if (!frm.doc[field]) {
    //                 frm.set_value('sync_down_select_all', 0);
    //                 frm.fields_dict.sync_down_select_all.df.label = 'Select All';
    //             } else if (sync_down_checkboxes.every(f => frm.doc[f])) {
    //                 frm.set_value('sync_down_select_all', 1);
    //                 frm.fields_dict.sync_down_select_all.df.label = 'Unselect All';
    //             }
    //         }
    //     ])
    // ),

    // // Individual sync_up checkbox handlers
    // ...Object.fromEntries(
    //     sync_up_checkboxes.map(field => [
    //         field,
    //         function (frm) {
    //             if (is_bulk_update) return;

    //             if (!frm.doc[field]) {
    //                 frm.set_value('sync_up_select_all', 0);
    //                 frm.fields_dict.sync_up_select_all.df.label = 'Select All';
    //             } else if (sync_up_checkboxes.every(f => frm.doc[f])) {
    //                 frm.set_value('sync_up_select_all', 1);
    //                 frm.fields_dict.sync_up_select_all.df.label = 'Unselect All';
    //             }
    //         }
    //     ])
    // )
});
