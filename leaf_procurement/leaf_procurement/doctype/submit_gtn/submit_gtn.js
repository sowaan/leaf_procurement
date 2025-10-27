// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Submit GTN", {
    refresh: function(frm) {
        // Only show button if doc is saved but not submitted
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Force Submit'), function() {
                frappe.confirm(
                    __('Are you sure you want to force submit this document?'),
                    function() {
                        // YES clicked
                        frappe.call({
                            method: 'leaf_procurement.leaf_procurement.utils.gtn_util.force_submit_gtn',
                            args: { gtn_name: frm.doc.gtn_number,
                                skip_stock_entry: frm.doc.skip_stock_entry
                             },
                            freeze: true,
                            freeze_message: __('Submitting...'),
                            callback: function(r) {
                                console.log("Response:", r);
                                if (!r.exc) {
                                    frappe.show_alert({ message: r.message, indicator: 'green' });
                                    frm.reload_doc();
                                }
                            }
                        });
                    },
                    function() {
                        frappe.show_alert({ message: __('Submission cancelled'), indicator: 'orange' });
                    }
                );
            }, __('Actions')); // Adds button under "Actions" group
        }
    }
});
