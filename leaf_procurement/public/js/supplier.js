frappe.ui.form.on('Supplier', {
    //custom supplier client script
    onload: function (frm) {
        $('div[data-fieldname="naming_series"]').hide();
        if (!frm.doc.custom_nic_number || !frm.doc.custom_location_warehouse) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Leaf Procurement Settings',
                    name: 'Leaf Procurement Settings'
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('custom_company', r.message.company_name);
                        frm.set_value('custom_location_warehouse', r.message.location_warehouse);
                    }
                }
            });
        }
    },
    validate: function (frm) {
        let cnic = frm.doc.custom_nic_number;
        const cnic_regex = /^\d{5}-\d{7}-\d{1}$/;
        if (cnic) {
            cnic = cnic.replace(/\D/g, '');

            if (cnic.length > 13) {
                cnic = cnic.slice(0, 13);
            }

            if (cnic.length === 13) {
                cnic = `${cnic.slice(0, 5)}-${cnic.slice(5, 12)}-${cnic.slice(12)}`;
            }
            frm.set_value('custom_nic_number', cnic);

            if (cnic && !cnic_regex.test(cnic)) {
                frappe.throw(__('CNIC must be in the format xxxxx-xxxxxxx-x'));
            }
        }
    },
    custom_nic_number: function (frm) {
        let cnic = frm.doc.custom_nic_number;

        if (cnic) {
            // Remove all non-digit characters
            cnic = cnic.replace(/\D/g, '');


            // Limit to 13 digits only
            if (cnic.length > 13) {
                cnic = cnic.slice(0, 13);
            }

            // Auto-format if 13 digits
            if (cnic.length === 13) {
                cnic = `${cnic.slice(0, 5)}-${cnic.slice(5, 12)}-${cnic.slice(12)}`;
            }

            frm.set_value('custom_nic_number', cnic);
        }
    }
});
