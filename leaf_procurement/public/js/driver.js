frappe.ui.form.on('Driver', {
    //custom driver client script
    onload: function (frm) {
        frm.set_df_property('naming_series', 'hidden', 1);
        if (!frm.doc.custom_location_warehouse) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Leaf Procurement Settings',
                    name: 'Leaf Procurement Settings'
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('custom_location', r.message.location_warehouse);
                    }
                }
            });
        }
    },
});