// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Audit Day Setup", {
    refresh(frm) {
        frm.clear_custom_buttons();

        if (!frm.doc.day_open_time) {
            // Show Day Open button only if day_open_time is not set
            frm.add_custom_button(__('Day Open'), function () {
                const now = frappe.datetime.now_datetime();
                frm.set_value('day_open_time', now);
                frm.set_value('status', "Opened");

                frm.save().then(() => {
                    frappe.msgprint(__('Day opened at: ') + now);
                    frm.reload_doc();  // ensure buttons refresh
                });
            });
        }

        if (frm.doc.day_open_time && !frm.doc.day_close_time) {
            frm.add_custom_button(__('Day Close'), async function () {
                try {


                    // No mismatches, proceed with day close
                    frappe.confirm(
                        __("Are you sure you want to close the day?"),
                        async function () {
                            const now = frappe.datetime.now_datetime();
                            frm.set_value('day_close_time', now);
                            frm.set_value('status', "Closed");

                            await frm.save();
                            frappe.show_alert({
                                message: __('Day has been closed.', now),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        },
                        function () {
                            frappe.show_alert({
                                message: __('Day close cancelled.'),
                                indicator: 'orange'
                            });
                        }
                    );

                } catch (err) {
                    frappe.msgprint(__('Error checking GTN and grade differences.'));
                    console.error(err);
                }
            });

        }

        if (!frm.is_new()) {
            frm.fields.forEach(function (field) {
                frm.set_df_property(field.df.fieldname, 'read_only', 1);
            });
            frm.refresh_fields();
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
    onload: function (frm) {
        if (frm.is_new()) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Leaf Procurement Settings',
                    name: 'Leaf Procurement Settings'
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('company', r.message.company_name);
                        frm.set_value('location_warehouse', r.message.location_warehouse);
                        frm.set_value('allow_sunday_open', r.message.allow_sunday_open)
                    }
                }
            });
        }
    }    
});
