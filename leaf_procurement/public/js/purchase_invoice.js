
function update_registration_status(frm) {
    const purchase_invoice = frm.doc.name;

    // Step 1: Find Bale Weight Info using purchase_invoice
    frappe.call({
        method: 'leaf_procurement.api_functions.update_bale_status',
        args: {
            purchase_invoice: purchase_invoice
        },
        callback: function (res) {
            if (res.message && res.message.status === 'success') {
                frappe.msgprint(`Bale status updated for: ${res.message.updated}`);
            } else {
                frappe.msgprint('No matching bale found.');
            }
        }
    });

}
function check_day_open_status(frm) {
    return new Promise((resolve) => {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Day Setup",
                filters: {
                    date: frm.doc.posting_date,
                    day_open_time: ["is", "set"],
                    day_close_time: ["is", "not set"]
                },
                fields: ["name"]
            },
            callback: function (r) {
                const is_day_open = r.message && r.message.length > 0;

                resolve(is_day_open); // ✅ Now resolves with true or false
            }
        });
    });
}


frappe.ui.form.on('Purchase Invoice', {
    async refresh(frm) {
        // hide print button
        // frm.page.set_inner_btn_group_as_primary('print');
        // $('[data-original-title="Print"]').hide();

        // Mubashir: Hide Print button from the menu
        const printButton = document.querySelector('button[data-original-title="Print"]');
        if (printButton) {
            printButton.remove();
        }
        const printItem = document.querySelector('li .menu-item-label[data-label="Print"]');
        if (printItem) {
            printItem.closest('li').remove();
        }
        //END Mubashir


        if (frm.doc.docstatus === 1) {
            if (!frm.doc.custom_barcode_base64) {
                await frappe.call({
                    method: 'leaf_procurement.leaf_procurement.api.barcode.ensure_barcode_base64',
                    args: {
                        doctype: frm.doc.doctype,
                        name: frm.doc.name
                    },
                    callback: (r) => {
                        if (r.message && r.message.custom_barcode_base64) {
                            frm.set_value('custom_barcode_base64', r.message.custom_barcode_base64);
                        }
                    }
                });
            }
            if (!frm.doc.custom_stationary) {
                frm.add_custom_button(__('Print Voucher'), async () => {
                    const day_is_open = await check_day_open_status(frm);

                    if (!day_is_open) {
                        frappe.msgprint(__('Voucher cannot be printed for a closed day.'));
                        return;
                    }
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

                                    update_registration_status(frm);
                                    frappe.set_route(
                                        "print",
                                        "Purchase Invoice",
                                        frm.doc.name
                                    );
                                    // After saving, open print view
                                    // const docname = frm.doc.name; // or hardcode if needed
                                    // const route = `/app/print/Purchase Invoice/${encodeURIComponent(docname)}`;
                                    // window.open(route, '_blank');
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
                    const day_is_open = await check_day_open_status(frm);

                    if (!day_is_open) {
                        frappe.msgprint(__('Voucher cannot be printed for a closed day.'));
                        return;
                    }


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
                                    // frm.set_df_property('custom_re_print', 'hidden', 1);
                                    // const docname = frm.doc.name; // or hardcode if needed
                                    // const route = `/app/print/Purchase Invoice/${encodeURIComponent(docname)}`;
                                    // window.open(route, '_blank');

                                    frappe.set_route(
                                        "print",
                                        "Purchase Invoice",
                                        frm.doc.name
                                    );
                                }
                            });
                        },
                        __('Enter Stationery'), __('Save'));
                });
            }
        }
    }

});