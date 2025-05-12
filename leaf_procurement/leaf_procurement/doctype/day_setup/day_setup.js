// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Day Setup", {
	refresh(frm) {
        frm.clear_custom_buttons();

        if (!frm.doc.day_open_time) {
            // Show Day Open button only if day_open_time is not set
            frm.add_custom_button(__('Day Open'), function() {
                const now = frappe.datetime.now_datetime();
                frm.set_value('day_open_time', now);

                frm.save().then(() => {
                    frappe.msgprint(__('Day opened at: ') + now);
                    frm.reload_doc();  // ensure buttons refresh
                });
            }, __('Actions'));
        }

        if (frm.doc.day_open_time && !frm.doc.day_close_time) {
            // Show Day Close button only if day is open and not yet closed
            frm.add_custom_button(__('Day Close'), function() {
                const now = frappe.datetime.now_datetime();
                frm.set_value('day_close_time', now);

                frm.save().then(() => {
                    frappe.msgprint(__('Day closed at: ') + now);
                    frm.reload_doc();
                });
            }, __('Actions'));
        }
	},
    onload: function(frm) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Leaf Procurement Settings',
                name: 'Leaf Procurement Settings'
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('company', r.message.company_name);
                    frm.set_value('location_warehouse', r.message.location_warehouse);
                }
            }
        });
    }    
});
