// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leaf Consumption", {
    refresh(frm) {

    },
    onload: function (frm) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Leaf Procurement Settings',
                    name: 'Leaf Procurement Settings'
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('item', r.message.default_item);
                        frm.set_value('barcode_length', r.message.barcode_length);
                        resolve(r.message);  // ✅ pass settings forward
                    } else {
                        reject("Could not fetch settings");
                    }
                }
            });
        });
    },
    add_bale(frm){
        if (!frm.doc.scan_barcode) {
            frappe.show_alert({
                message: __('Please enter a valid barcode to add audit information.'),
                indicator: "red"
            });
            return;
        };
        frm.save();
    },
    validate: async function (frm) {
        const result = await validate_bale_data(frm);
        if (!result.valid) {
            frappe.validated = false;
            setTimeout(() => {
                frm.set_value('scan_barcode', '');
            }, 3000);

            return;
        }
        const values = frm.doc


        const weight = values.weight;
        if (!values.scan_barcode) return;

        itemcode = frm.doc.item || "Tobacco";

        await frappe.call({
            method: 'leaf_procurement.leaf_manufacturing.utils.barcode_utils.get_invoice_item_by_barcode',
            args: { itemcode: itemcode, barcode: values.scan_barcode },
            callback: function (r) {
                if (r.message && r.message.exists) {
                    if (r.message.qty <= 0) {
                        frappe.show_alert({ message: __('The bale has been rejected during purchase / weight.'), indicator: 'orange' });
                        return;
                    }
                   
                    frm.doc.consumption_detail.push({
                        bale_barcode: values.scan_barcode,
                        purchase_weight: r.message.qty,
                        internal_grade: r.message.reclassification_grade,
                        reweight: weight,
                         gain_loss: Number((r.message.qty - weight).toFixed(2)),

                    });
                    console.log("pushing data", r.message);
                } else {
                    frappe.show_alert({ message: __('Invalid barcode, voucher has not been generated for this bale or the bale has been rejected.'), indicator: 'orange' });
                    //frappe.msgprint(__('This barcode has not been invoiced or has been rejected during invoice generation.'));
                }

            }
        }) ;
        console.log("Row count:", frm.doc.consumption_detail.length);
        // Reset fields
        frm.set_value('scan_barcode', '');
        // frm.set_value('captured_weight', '');
        frm.set_value('weight', '');
        // Reset weight display


        // Focus barcode field again
        setTimeout(() => {
            suppress_focus = false;
            const $barcode_input = frm.fields_dict.scan_barcode.$wrapper.find('input');
            $barcode_input.focus();

        }, 300);
    },    
    onload_post_render(frm) {
        setTimeout(() => {
            const $input = frm.get_field('scan_barcode')?.$wrapper.find('input');

            if ($input && $input.length) {
                // Restrict to max 11 characters
                $input.attr('maxlength', frm.doc.barcode_length || 11);

                $input.on('input', function () {
                    if (this.value.length > 11) {
                        this.value = this.value.slice(0, 11);
                    }
                });

                // Handle Enter key press
                $input.on('keydown', function (e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        e.stopPropagation();

                        // Move focus to add_audit_weight button
                        const nextField = frm.get_field('weight');
                        if (nextField) {
                            nextField.$wrapper.find('input').focus();
                        }
                    }
                });
            }
        }, 300); // Delay to ensure DOM elements are rendered

        setTimeout(() => {
            const $input = frm.get_field('weight')?.$wrapper.find('input');

            if ($input && $input.length) {
                
                // Handle Enter key press
                $input.on('keydown', function (e) {
                    
                    if (e.key === 'Enter') {

                        e.preventDefault();
                        e.stopPropagation();

                        // Move focus to add_audit_weight button
                        const nextField = frm.get_field('add_bale');
                        if (nextField) {
                            nextField.$wrapper.find('button').focus();
                        }
                    }
                });
            }
        }, 300); // Delay to ensure DOM elements are rendered

        setTimeout(() => {
            const $btn = frm.get_field('add_bale')?.$wrapper.find('button');

            if ($btn && $btn.length) {
                // Handle Enter key to trigger click
                $btn.on('keydown', function (e) {
                    if (e.key === 'Enter') {
                        console.log("Enter key pressed on button");
                        e.preventDefault();
                        e.stopPropagation();
                        $btn.trigger('click');
                    }
                });

                // Change color on focus
                $btn.on('focus', function () {
                    $(this).css({
                        'background-color': '#007bff',
                        'color': '#fff',
                        'border-color': '#007bff'
                    });
                });

                // Revert color on blur
                $btn.on('blur', function () {
                    $(this).css({
                        'background-color': '',
                        'color': '',
                        'border-color': ''
                    });
                });
            }
        }, 300);        
    }
});

async function validate_bale_data(frm) {
    if (!frm.doc.scan_barcode && frm.doc.consumption_detail.length === 0) {
        frappe.show_alert({
            message: __('You must add at least one row in the Detail Table before saving.'),
            indicator: "red"
        });
        return { valid: false };

    }

    if (!frm.doc.scan_barcode) return { valid: true };

    const values = frm.doc;
    const weight = values.captured_weight;

    if (frm.doc.scan_barcode && !/^\d+$/.test(frm.doc.scan_barcode)) {
        frappe.show_alert({
            message: __('Barcode must contain only numbers.'),
            indicator: "red"
        });
        return { valid: false };

    }

    const expectedLength = frm.doc.barcode_length || 0;
    
    if (values.scan_barcode.length != expectedLength) {
        frappe.show_alert({
            message: __('Please enter a valid barcode of {0} digits.', [expectedLength]),
            indicator: "red"
        });
        const input = frm.fields_dict.scan_barcode.$wrapper.find('input')[0];
        if (input) {
            input.focus();
            input.select();
        }
        return { valid: false };
    }
    const response = await frappe.call({
        method: "leaf_procurement.leaf_manufacturing.utils.barcode_utils.check_bale_barcode_exists",
        args: {
            bale_barcode: values.scan_barcode,
        }
    });

    if (response.message === true) {
        frappe.show_alert({
            message: __('Bale barcode already exists in another Consumption record.'),
            indicator: 'red'
        });
        return { valid: false };
    }

    const existing = values.consumption_detail.find(row => row.bale_barcode === values.scan_barcode);
    if (existing) {
        frappe.show_alert({
            message: `Bale with barcode ${values.scan_barcode} already exists in the table.`,
            indicator: 'red'
        });
        frappe.validated = false;
        return;
    }
    if (weight <= 0) {
        frappe.show_alert({ message: __("Please enter weight information to continue."), indicator: "red" });
        return { valid: false };
    }


    return { valid: true };

}