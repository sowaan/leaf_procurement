// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bale Weight Info", {
    bale_registration_code(frm) {
        if (!frm.doc.bale_registration_code) return;

        validate_day_status(frm);
        let count = parseInt(frm.doc.total_bales);
        frm.clear_table('detail_table'); // optional: clear before add
        for (let i = 0; i < count; i++) {
            let row = frm.add_child('detail_table');
            row.index = i + 1;
        }
        frm.refresh_field('detail_table');

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Bale Registration',
                name: frm.doc.bale_registration_code
            },
            callback: function (r) {
                if (r.message) {
                    const details = r.message.bale_registration_detail || [];
                    // Store barcodes in a temporary variable
                    frm.bale_registration_barcodes = details.map(row => row.bale_barcode);
                }
            }
        });
    },
    refresh: function (frm) {
        if (!frm.is_new() && frm.doc.docstatus === 1 && !frm.doc.purchase_receipt_created) {
            frm.add_custom_button(__('Create Purchase Invoice'), function () {
                frappe.call({
                    method: 'leaf_procurement.leaf_procurement.api.bale_weight_utils.create_purchase_invoice',
                    args: {
                        bale_weight_info_name: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint(__('Purchase Invoice {0} created.', [r.message]));
                            frm.reload_doc();
                        }
                    }
                });
            });
        }
    },
    date: function (frm) {
        validate_day_status(frm);
    },
    onload: function (frm) {
        //override bale_registration_code query to load 
        //bale registration codes with no purchase record
        frm.set_query('bale_registration_code', function () {
            return {
                query: 'leaf_procurement.leaf_procurement.api.bale_weight_utils.get_available_bale_registrations'
            };
        });

        // Set query filter for 'item_sub_grade' field in child table
        frm.fields_dict['detail_table'].grid.get_field('item_sub_grade').get_query = function (doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            return {
                filters: {
                    item_grade: child.item_grade
                }
            };
        };

        //get company and location records from settings
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
                    frm.set_value('rejected_item_location', r.message.rejected_location_warehouse);

                    frm.set_value('item', r.message.default_item);
                    frm.set_value('rejected_item_grade', r.message.rejected_item_grade);
                    frm.set_value('rejected_item_sub_grade', r.message.rejected_item_sub_grade);
                    frm.set_value('transport_charges_item', r.message.transport_charges_item);
                }
            }
        });
        hide_grid_controls(frm);
    }
});
let scaleReader = null;
let scalePort = null;
let lastWeight = null;
let stopReading = false;
frappe.ui.form.on("Bale Weight Detail", {
get_weight_btn: function (frm, cdt, cdn) {
    const row = locals[cdt][cdn];

    const d = new frappe.ui.Dialog({
        title: 'Get Weight from Scale',
        fields: [
            {
                fieldname: 'p_item_grade',
                label: 'Item Grade',
                fieldtype: 'Data',
                default: row.item_grade,
                read_only: 1
            },
            {
                fieldname: 'p_item_sub_grade',
                label: 'Item Sub Grade',
                fieldtype: 'Data',
                default: row.item_sub_grade,
                read_only: 1
            },
            {
                fieldname: 'p_weight',
                label: 'Captured Weight',
                fieldtype: 'Float',
                reqd: 1,
                description: 'Connect to the device and press Get Weight'
            }
        ],
        primary_action_label: 'Capture Weight',
        primary_action: async function (values) {
            stopReading = true;
            await cleanupSerial();
            setTimeout(() => {
                if (lastWeight) {
                    frappe.model.set_value(cdt, cdn, 'weight', lastWeight);
                    d.hide();
                }
            }, 500);
        }
    });

    d.show();

    // Add big prominent weight display box above footer
    const $footer = d.$wrapper.find('.modal-footer');
    const $weightDisplay = $(`
        <div style="
            font-size: 70px;
            font-weight: bold;
            color: #007bff;
            text-align: center;
            padding: 20px;
            margin-bottom: 15px;
            border: 2px solid #007bff;
            border-radius: 10px;
        ">
        0.00 kg
        </div>
    `);
    $footer.before($weightDisplay);

    // Helper to update big weight display
    function updateWeightDisplay(weight) {
        $weightDisplay.text(weight + " kg");
    }

    // Style small p_weight field normally (optional)
    const weightField = d.fields_dict.p_weight.$wrapper;
    weightField.css({
        'font-size': '16px',
        'font-weight': 'normal',
        'color': '#000',
        'text-align': 'center',
        'padding': '5px 10px',
        'border-radius': '4px',
        'margin-top': '10px'
    });

    const footer = d.$wrapper.find('.modal-footer');
    const connectBtn = $(`<button class="btn btn-secondary btn-sm ml-2">Connect Scale</button>`);
    footer.prepend(connectBtn);

    connectBtn.on('click', async () => {
        try {
            scalePort = await navigator.serial.requestPort();
            await scalePort.open({ baudRate: 9600 });

            const textDecoder = new TextDecoderStream();
            const readableStreamClosed = scalePort.readable.pipeTo(textDecoder.writable);
            const reader = textDecoder.readable.getReader();

            scaleReader = reader;
            window._readableStreamClosed = readableStreamClosed;  // save for cleanup

            stopReading = false;
            //frappe.msgprint(__('Connected to scale. Waiting for stable weight...'));

            while (!stopReading) {
                const { value, done } = await reader.read();
                if (done || stopReading) break;
                if (value) {
                    const weight = parseFloat(value.trim());
                    if (!isNaN(weight)) {
                        lastWeight = weight.toFixed(2);
                        d.set_value('p_weight', lastWeight);
                        updateWeightDisplay(lastWeight);
                    }
                }
            }

            await cleanupSerial();
            console.log('Disconnected from scale.');
        } catch (err) {
            console.error('Serial error:', err);
            frappe.msgprint(__('Failed to connect or read from scale.'));
            await cleanupSerial();
        }
    });
}
    ,

    refresh: function (frm) {
        hide_grid_controls(frm);

    },

    item_grade(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, 'item_sub_grade', '');
    },
    item_sub_grade: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.item_grade && row.item_sub_grade) {
            frappe.call({
                method: "leaf_procurement.leaf_procurement.doctype.item_grade_price.item_grade_price.get_item_grade_price",
                args: {
                    company: frm.doc.company,
                    location_warehouse: frm.doc.location_warehouse,
                    item: frm.doc.item,
                    item_grade: row.item_grade,
                    item_sub_grade: row.item_sub_grade
                },
                callback: function (r) {
                    if (r.message !== undefined) {
                        frappe.model.set_value(cdt, cdn, "rate", r.message);
                    }
                }
            });
        }
    },
    bale_barcode: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const valid_barcodes = frm.bale_registration_barcodes || [];

        if (!valid_barcodes.includes(row.bale_barcode)) {
            frappe.msgprint(__('Invalid Bale Barcode: {0}', [row.bale_barcode]));
            frappe.model.set_value(cdt, cdn, 'bale_barcode', '');
        }
    },
    // bale_barcode(frm, cdt, cdn) {
    //     update_bale_counter(frm);
    // },
    // bale_purchase_detail_remove(frm) {
    //     update_bale_counter(frm);
    // }        
});
async function cleanupSerial() {
    try {
        if (scaleReader) {
            await scaleReader.cancel();  // triggers done
            scaleReader.releaseLock();   // unlocks stream
            scaleReader = null;
        }
    } catch (e) {
        console.warn('Reader cleanup error:', e);
    }

    try {
        if (window._readableStreamClosed) {
            await window._readableStreamClosed;
            window._readableStreamClosed = null;
        }
    } catch (e) {
        console.warn('Readable stream close error:', e);
    }

    try {
        if (scalePort) {
            await scalePort.close();
            scalePort = null;
        }
    } catch (e) {
        console.warn('Port close error:', e);
    }
}


function update_bale_counter(frm) {
    let total = frm.doc.total_bales;  // increment before recounting
    frm.doc.remaining_bales = total - (frm.doc.detail_table || []).length;
    frm.refresh_field('remaining_bales');
}

function validate_day_status(frm) {
    if (!frm.doc.date) return;

    // If registration_date is set, validate it matches doc.date
    if (frm.doc.registration_date) {
        if (frm.doc.date !== frm.doc.registration_date) {
            frappe.msgprint({
                title: __("Date Mismatch"),
                message: __("⚠️ The selected Bale Registration was created on <b>{0}</b>, which does not match this document's date <b>{1}</b>.")
                    .replace('{0}', frm.doc.registration_date)
                    .replace('{1}', frm.doc.date),
                indicator: 'red'
            });
            toggle_fields(frm, false);
            return;
        }
    }
    // Proceed to check if the day is open
    check_day_open_status(frm);
}
function check_day_open_status(frm) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Day Setup",
            filters: {
                date: frm.doc.date,
                day_open_time: ["is", "set"],
                day_close_time: ["is", "not set"]
            },
            fields: ["name"]
        },
        callback: function (r) {
            const is_day_open = r.message && r.message.length > 0;

            toggle_fields(frm, is_day_open);

            if (!is_day_open) {
                frappe.msgprint({
                    title: __("Day Not Open"),
                    message: __("⚠️ You cannot register or purchase bales because the day is either not opened or already closed."),
                    indicator: 'red'
                });
            }
        }
    });
}


function toggle_fields(frm, enable) {
    // Replace 'bale_purchase_detail' with your actual child table fieldname
    frm.toggle_display('detail_table', enable);

    // Optionally, clear any error messages or refresh the field
    frm.refresh_field('detail_table');
    hide_grid_controls(frm);
}

function hide_grid_controls(frm) {

    const grid_field = frm.fields_dict.detail_table;
    if (grid_field && grid_field.grid && grid_field.grid.wrapper) {
        grid_field.grid.wrapper
            .find('.grid-add-row, .grid-remove-rows, .btn-open-row')
            .hide();
    }
}
