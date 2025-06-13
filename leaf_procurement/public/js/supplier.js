frappe.ui.form.on('Supplier', {
    //custom supplier client script
    onload: function (frm) {
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Leaf Procurement Settings',
                name: 'Leaf Procurement Settings'
            },
            callback: function (r) {
                if (r.message) {
                    console.log('here supplier');
                    frm.set_value('custom_company', r.message.company_name);
                    frm.set_value('custom_location_warehouse', r.message.location_warehouse);
                }
            }
        });
    },
    validate: function (frm) {
        const cnic = frm.doc.custom_nic_number;
        const cnic_regex = /^\d{5}-\d{7}-\d{1}$/;

        if (cnic && !cnic_regex.test(cnic)) {
            frappe.throw(__('CNIC must be in the format xxxxx-xxxxxxx-x'));
        }
    }
});
