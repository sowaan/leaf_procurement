// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Day Setup", {
    set_due_date_min: function(frm) {
        if (frm.doc.date) {
            // Convert frappe date string (YYYY-MM-DD) to JavaScript Date object
            let parts = frm.doc.date.split('-'); // [YYYY, MM, DD]
            let jsDate = new Date(parts[0], parts[1] - 1, Number(parts[2]) + 1); // add 1 day

            frm.set_df_property('due_date', 'min_date', jsDate); // JS Date object
        } else {
            frm.set_df_property('due_date', 'min_date', null);
        }
    },
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
    date: function (frm) {
        frm.events.set_due_date_min(frm);

        // Compare with today's date
        let today = frappe.datetime.get_today();
        if (frm.doc.date !== today) {
            frappe.msgprint({
                title: __('Caution'),
                message: __('Selected date ({0}) is not today ({1}).', [frm.doc.date, today]),
                indicator: 'orange'
            });
        }        
    },    
    onload: function(frm) {
        frm.events.set_due_date_min(frm);
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
