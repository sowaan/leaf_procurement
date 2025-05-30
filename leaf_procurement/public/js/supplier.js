frappe.ui.form.on('Supplier', {
    //custom supplier client script
    onload: function(frm) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Leaf Procurement Settings',
                name: 'Leaf Procurement Settings'
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('custom_company', r.message.company_name);
                    frm.set_value('custom_location_warehouse', r.message.location_warehouse);
                }
            }
        });
    }
});
