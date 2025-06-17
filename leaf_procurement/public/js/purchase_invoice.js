

frappe.ui.form.on('Purchase Invoice', {
    refresh(frm) {
        // hide print button
        // frm.page.set_inner_btn_group_as_primary('print');
        $('[data-original-title="Print"]').hide();
        if (frm.doc.docstatus === 1) {
            if (!frm.doc.custom_stationary) {
                frm.add_custom_button(__('Print Voucher'), async () => {
                    const { value } = await frappe.prompt([
                        {
                            fieldname: 'stationery',
                            label: 'Stationery',
                            fieldtype: 'Data',
                            reqd: 1
                        }
                    ],
                        (values) => {
                            // Save stationery to the current doc or linked doc
                            frappe.call({
                                method: 'frappe.client.set_value',
                                args: {
                                    doctype: frm.doc.doctype,
                                    name: frm.doc.name,
                                    fieldname: {
                                        'custom_stationary': values.stationery,
                                        'status': 'Printed'
                                    }
                                },
                                freeze: true,
                                freeze_message: __('Print Voucher...'),
                                callback: function (response) {
                                    // After saving, open print view
                                    const docname = frm.doc.name; // or hardcode if needed
                                    const route = `/app/print/Purchase Invoice/${encodeURIComponent(docname)}`;
                                    window.open(route, '_blank');
                                }
                            });
                        },
                        __('Enter Stationery'), __('Save'));
                })
                frm.set_df_property('custom_re_print', 'hidden', 1);
            } else if (!frm.doc.custom_reprint_reason) {
                frm.set_df_property('custom_re_print', 'hidden', 0);
            }
            if (frm.doc.custom_stationary && frm.doc.custom_re_print) {

                frm.add_custom_button(__('Reprint Voucher'), async () => {
                    const { value } = await frappe.prompt([
                        {
                            fieldname: 'stationery',
                            label: 'Stationery',
                            fieldtype: 'Data',
                            reqd: 1
                        },
                        {
                            fieldname: 'reason',
                            label: 'Reason',
                            fieldtype: 'Small Text',
                            reqd: 1
                        }
                    ],
                        (values) => {
                            frappe.call({
                                method: 'frappe.client.set_value',
                                args: {
                                    doctype: frm.doc.doctype,
                                    name: frm.doc.name,
                                    fieldname: {
                                        'custom_stationary': values.stationery,
                                        'custom_re_print': 0,
                                        'custom_reprint_reason': values.reason,
                                        'status': 'Re-Printed'
                                    },
                                    freeze: true,
                                },
                                callback: function (response) {
                                    // After saving, open print view
                                    frm.set_df_property('custom_re_print', 'hidden', 1);
                                    const docname = frm.doc.name; // or hardcode if needed
                                    const route = `/app/print/Purchase Invoice/${encodeURIComponent(docname)}`;
                                    window.open(route, '_blank');
                                }
                            });
                        },
                        __('Enter Stationery'), __('Save'));
                });
            }
        }
    }
});