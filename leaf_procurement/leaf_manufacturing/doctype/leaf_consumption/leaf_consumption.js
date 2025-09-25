// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt
let scaleReader = null;
let scalePort = null;
let lastWeight = null;
let stopReading = false;
let suppress_focus = false;
let scaleConnected = 'Disconnected';
let updateWeightOnForm = true;

frappe.ui.form.on("Leaf Consumption", {
    refresh(frm) {
        frm.page.sidebar.hide();
        update_consumption_display(frm);
    },
    connect_scale: async function (frm) {
        if (!window._scaleConnection.port) {
            await connectToScale(frm);
        } else {
            frappe.msgprint(__('Scale already connected.'));
        }
    },
    disconnect_scale: async function (frm) {
        await cleanupSerial(frm);
        //frappe.msgprint(__('Scale disconnected.'));
    },
    onload: function (frm) {
        frm.page.sidebar.hide();
        if (scaleConnected == 'Connected') {
            frm.fields_dict.connect_scale.$wrapper.hide();
            frm.fields_dict.disconnect_scale.$wrapper.show();
        }
        else {
            frm.fields_dict.connect_scale.$wrapper.show();
            frm.fields_dict.disconnect_scale.$wrapper.hide();
        }
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
    add_bale(frm) {
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


        const existing = values.consumption_detail.find(row => row.bale_barcode === values.scan_barcode);
        if (existing) {
            // ✅ Update weight instead of blocking
            existing.reweight = weight;
            existing.gain_loss = Number((weight - existing.purchase_weight).toFixed(2));

            frappe.show_alert({
                message: `Weight updated for existing bale ${values.scan_barcode}.`,
                indicator: 'green'
            });
        } else {
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
                            gain_loss: Number((weight - r.message.qty).toFixed(2)),

                        });
                        console.log("pushing data", r.message);
                    } else {
                        frappe.show_alert({ message: __('Invalid barcode, voucher has not been generated for this bale or the bale has been rejected.'), indicator: 'orange' });
                        //frappe.msgprint(__('This barcode has not been invoiced or has been rejected during invoice generation.'));
                    }

                }
            });
        }
        // console.log("Row count:", frm.doc.consumption_detail.length);
        // Reset fields
        frm.set_value('scan_barcode', '');
        // frm.set_value('weight', '');
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

function update_consumption_display(frm) {
    frm.fields_dict["consumption_detail"].grid.wrapper.find('.grid-add-row').hide();
   
    let total_purchase_weight = 0;
    let total_reweight = 0;
    let total_bales = 0;
    let total_difference = 0;
    frm.doc.consumption_detail.forEach(row => {
        total_reweight += flt(row.reweight);
        total_purchase_weight += flt(row.purchase_weight);
        total_bales += 1;
    });

    total_difference = total_reweight - total_purchase_weight;

    if (total_purchase_weight >= frm.doc.estimated_input)
        updateWeightOnForm = false;
    else
        updateWeightOnForm = true;
    // Delay until child table is ready
    setTimeout(() => {
        const total_items = frm.doc.consumption_detail.length;


        let html = `
    <div style="padding: 10px; font-size: 18px;">
        <b>Scanned Bales: 
        <span style="color: green;">${total_bales}</span> <br>
        <b>ReWeight:
        <span style="color: green;">${total_reweight.toFixed(2)} kg  </span></b><br>
        <b>Purchase Weight:
        <span style="color: green;">${total_purchase_weight.toFixed(2)} kg </span></b><br>
        <b>Difference in Table:
        <span style="color: blue;">${total_difference.toFixed(2)}</span></b>
    </div>
`;
        frm.set_df_property("audit_display", "options", html);
        frm.refresh_field("audit_display");

    }, 300); // Wait for grid to initialize

}
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
    const weight = values.weight;

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
            doc_status: 1,
        }
    });

    if (response.message === true) {
        frappe.show_alert({
            message: __('Bale barcode already exists in another Consumption record.'),
            indicator: 'red'
        });
        return { valid: false };
    }


    if (weight <= 0) {
        frappe.show_alert({ message: __("Please enter weight information to continue."), indicator: "red" });
        return { valid: false };
    }


    return { valid: true };

}


if (!window._scaleConnection) {
    window._scaleConnection = {
        port: null,
        reader: null,
        lastWeight: null,
        stopReading: false
    };
}

function updateMainWeightDisplay(frm, weight) {
    let color = scaleConnected === "Connected" ? "#007bff" : "red";
    let html = `<h2 style="color: ${color}; font-weight: bold;">Scale: ${scaleConnected}<br />${weight}</h2>`;
    if (updateWeightOnForm) {
        frm.set_value('weight', weight);
        frm.fields_dict.scale_status.$wrapper.html(html);
    }
}

function updateScaleStatus(frm, status) {
    let color = status === "Connected" ? "#007bff" : "red";
    let html = `<h2 style="color: ${color}; font-weight: bold;">Scale: ${status}</h2>`;
    frm.fields_dict.scale_status.$wrapper.html(html);
}

async function readScaleContinuously(frm) {
    const { reader } = window._scaleConnection;
    while (!window._scaleConnection.stopReading) {
        try {
            const { value, done } = await reader.read();
            if (done || window._scaleConnection.stopReading) break;
            if (value) {
                const weight = parseFloat(value.trim());
                if (!isNaN(weight)) {
                    window._scaleConnection.lastWeight = weight.toFixed(2);
                    updateMainWeightDisplay(frm, window._scaleConnection.lastWeight);
                }
            }
        } catch (e) {
            console.error('Error while reading:', e);
            break;
        }
    }
}

async function connectToScale(frm) {
    try {
        let port;
        if (window.savedPort) {
            port = window.savedPort;
        } else {
            // Otherwise, prompt user to select one
            port = await navigator.serial.requestPort();
            window.savedPort = port;
        }

        await port.open({ baudRate: 9600 });

        const textDecoder = new TextDecoderStream();
        const readableStreamClosed = port.readable.pipeTo(textDecoder.writable);
        const reader = textDecoder.readable.getReader();

        window._scaleConnection = {
            port,
            reader,
            readableStreamClosed,
            stopReading: false,
            lastWeight: null
        };

        scaleConnected = "Connected";

        // 👇 Hide connect, show disconnect
        frm.fields_dict.connect_scale.$wrapper.hide();
        frm.fields_dict.disconnect_scale.$wrapper.show();
        updateScaleStatus(frm, "Connected");

        // Begin reading data
        while (!window._scaleConnection.stopReading) {
            const { value, done } = await reader.read();
            if (done || window._scaleConnection.stopReading) break;
            if (value) {
                const weight = parseFloat(value.trim());
                if (!isNaN(weight)) {
                    window._scaleConnection.lastWeight = weight.toFixed(2);
                    updateMainWeightDisplay(frm, weight.toFixed(2)); // Your custom method
                }
            }
        }

    } catch (err) {
        console.error('Serial connection failed:', err);
        frappe.msgprint(__('Failed to connect to the weighing scale.'));
        await cleanupSerial(frm);
    }
}

async function cleanupSerial(frm) {
    try {
        if (window._scaleConnection?.reader) {
            try {
                await window._scaleConnection.reader.cancel();
                await window._scaleConnection.readableStreamClosed;
            } catch (err) {
                console.warn("Error while cancelling reader or closing stream:", err);
            }
        }

        if (window._scaleConnection?.port && window._scaleConnection.port.readable) {
            try {
                await window._scaleConnection.port.close();
                console.log("Serial port closed.");
            } catch (err) {
                console.warn("Error while closing port:", err);
            }
        }

        window._scaleConnection = {
            port: null,
            reader: null,
            readableStreamClosed: null,
            stopReading: true,
            lastWeight: null
        };

        scaleConnected = "Disconnected";

        // Show connect, hide disconnect

        frm.fields_dict.connect_scale.$wrapper.show();
        frm.fields_dict.disconnect_scale.$wrapper.hide();
        updateScaleStatus(frm, "Disconnected");

    } catch (e) {
        console.error("Error during serial cleanup:", e);
    }
}