// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt
let scaleReader = null;
let scalePort = null;
let lastWeight = null;
let stopReading = false;
let suppress_focus = false;
let active_weight_dialog = null; // global reference
let scaleConnected = 'Disconnected';

async function proceedWithBarcodeValidationAndGradeMainPage(frm, barcode) {
    const validBarcodes = frm.bale_registration_barcodes || [];
    const $barcode_input = frm.fields_dict.scan_barcode.$wrapper.find('input');

    if (!validBarcodes.includes(barcode)) {
        frappe.show_alert({
            message: __('Invalid Bale Barcode: {0}', [barcode]),
            indicator: 'red'
        });
        frm.set_value('scan_barcode', '');
        $barcode_input.focus();
        return;
    }

    const already_scanned = (frm.doc.detail_table || []).some(row => row.bale_barcode === barcode);
    if (already_scanned) {
        frappe.show_alert({
            message: __('⚠️ This Bale Barcode is already scanned: {0}', [barcode]),
            indicator: 'red'
        });
        frm.set_value('scan_barcode', '');
        //updateWeightDisplay("0.00");
        $barcode_input.focus();
        return;
    }
    is_grade_popup_open = true;
    frm.set_value('scan_barcode', barcode);
    open_grade_selector_popup(async function (grade, sub_grade, reclassification_grade) {
        frm.set_value('item_grade', grade);
        frm.set_value('item_sub_grade', sub_grade);
        frm.set_value('reclassification_grade', reclassification_grade);
        frappe.call({
            method: "leaf_procurement.leaf_procurement.doctype.item_grade_price.item_grade_price.get_item_grade_price",
            args: {
                company: frm.doc.company,
                location_warehouse: frm.doc.location_warehouse,
                item: frm.doc.item,
                item_grade: grade,
                item_sub_grade: sub_grade
            },
            callback: function (r) {
                if (r.message !== undefined) {
                    frm.set_value("price", r.message);
                }
                is_grade_popup_open = false;
            }
        });

        //await frm.events.update_bale_weight_details(frm, true);
    });
}
async function render_main_pending_bales_list(frm) {
    const container = frm.fields_dict.bale_list.$wrapper;
    container.empty();


    if (!frm.bale_registration_barcodes || frm.bale_registration_barcodes.length === 0) {
        container.html('<div>No bales available for this lot.</div>');
        return;
    }

    frappe.call({
        method: 'leaf_procurement.leaf_procurement.api.bale_weight_utils.get_processed_bale_barcodes',
        args: {
            parent_name: frm.doc.name
        },
        callback: function (r) {
            const processed_barcodes = (r.message || []).map(row => row.bale_barcode);
            const $header = $(`
                <div style="display: flex; font-weight: bold; padding-bottom: 6px; border-bottom: 1px solid #ccc;">
                    <div style="flex: 1 1 13ch; min-width: 13ch; font-family: monospace;">Bale Barcode</div>
                    <div style="flex: 0 0 8ch; text-align: center;">Status</div>
                </div>
            `);
            container.append($header);

            const pending_barcodes = frm.bale_registration_barcodes.filter(b => !processed_barcodes.includes(b));

            const message_label = frm.fields_dict.message_label.$wrapper;

            if (pending_barcodes.length === 2) {
                message_label.text('⚠️ The next bale is the last one for this lot!');
            } else {
                message_label.text('');
            }

            //message_label.html$('<div><h2>'+ message_label +'</h2></div>');
            frm.bale_registration_barcodes.forEach(barcode => {
                const is_processed = processed_barcodes.includes(barcode);
                const statusText = is_processed ? '✅' : '';
                const statusTextColor = is_processed ? '#155724' : '#856404';

                const $barcodeCell = $(`<div style="
                    flex: 1 1 13ch;
                    min-width: 13ch;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    font-family: monospace;
                    padding: 4px 6px;
                ">${barcode}</div>`);

                const $statusCell = $(`<div style="
                    flex: 0 0 8ch;
                    text-align: center;
                    font-weight: 700;
                    color: ${statusTextColor};
                    border-radius: 3px;
                    padding: 2px 4px;
                    user-select: none;
                    margin-left: 6px;
                ">${statusText}</div>`);

                const $row = $('<div style="display: flex; align-items: center; margin: 2px 0;"></div>');
                $row.append($barcodeCell, $statusCell);

                if (!is_processed) {
                    $row.css('cursor', 'pointer');
                    $row.on('click', async () => {

                        await proceedWithBarcodeValidationAndGradeMainPage(frm, barcode);
                    });
                } else {
                    $row.css('cursor', 'default');
                }

                container.append($row);
            });
        }
    });
}



function updateMainWeightDisplay(frm, weight) {
    // $weightDisplay.text(weight + " kg");
    frm.set_value('bale_weight', weight);

    let color = scaleConnected === "Connected" ? "#007bff" : "red";
    let html = `<h2 style="color: ${color}; font-weight: bold;">Scale: ${scaleConnected}<br />${weight}</h2>`;
    frm.fields_dict.scale_status.$wrapper.html(html);

}

// Define globally if not already defined
if (!window._scaleConnection) {
    window._scaleConnection = {
        port: null,
        reader: null,
        lastWeight: null,
        stopReading: false
    };
}
async function connectToScale(frm) {
    try {
        //const port = await navigator.serial.requestPort();
        let port;

        if (window.savedPort) {
            port = window.savedPort;
        } else {
            // Otherwise, prompt user to select one
            port = await navigator.serial.requestPort();
            window.savedPort = port;
        }


        await port.open({ baudRate: 9600 });

        //await port.open({ baudRate: 9600 });

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
                    updateMainWeightDisplayWeightDisplay(frm, window._scaleConnection.lastWeight);
                }
            }
        } catch (e) {
            console.error('Error while reading:', e);
            break;
        }
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

function addConnectButton(frm) {
    const connectBtn = $(`<button class="btn btn-secondary btn-sm ml-2">Connect Scale</button>`);
    frm.page.clear_primary_action();
    frm.page.set_primary_action('Submit', () => frm.save('Submit'));

    // Optional: place your button in the footer or toolbar
    frm.page.add_inner_button('Connect Scale', async function () {
        await connectToScale(frm);
    });
}


window.addEventListener('beforeunload', async () => {
    if (window._scaleConnection?.port) {
        try {
            await window._scaleConnection.reader?.cancel();
            await window._scaleConnection.port?.close();
        } catch (e) {
            console.warn("Error closing port on unload:", e);
        }
    }

});

async function validate_bale_data(frm) {
    const values = frm.doc;
    const weight = values.bale_weight;

    if (!values.scan_barcode) {
        frappe.show_alert({ message: __("Please scan a barcode before saving detail."), indicator: "orange" });
        return { valid: false };
    }

    const existing = values.detail_table.find(row => row.bale_barcode === values.scan_barcode);
    if (existing) {
        frappe.show_alert({
            message: `Bale with barcode ${values.scan_barcode} already exists in the table.`,
            indicator: 'red'
        });
        return { valid: false };
    }

    const r = await frappe.call({
        method: "leaf_procurement.leaf_procurement.doctype.bale_weight_info.bale_weight_info.quota_weight",
        args: { location: values.location_warehouse }
    });

    if (r.message) {
        const { bale_minimum_weight_kg, bal_maximum_weight_kg } = r.message;

        if (weight < bale_minimum_weight_kg || weight > bal_maximum_weight_kg) {
            frappe.show_alert({
                message: `The captured weight ${weight} kg is outside the allowed range of ${bale_minimum_weight_kg} kg to ${bal_maximum_weight_kg} kg for this location.`,
                indicator: 'red'
            });
            return { valid: false };
        }
    }

    if (!values.item_grade || !values.item_sub_grade || !values.reclassification_grade) {
        frappe.show_alert({
            message: `Please select Grade, Sub-Grade and Reclassification Grade to save weight information.`,
            indicator: 'red'
        });
        return { valid: false };
    }

    const validBarcodes = frm.bale_registration_barcodes || [];
    const $barcode_input = frm.fields_dict.scan_barcode.$wrapper.find('input');

    if (!validBarcodes.includes(values.scan_barcode)) {
        frappe.show_alert({
            message: __('Invalid Bale Barcode: {0}', [values.scan_barcode]),
            indicator: 'red'
        });
        frm.set_value('scan_barcode', '');
        $barcode_input.focus();
        return { valid: false };
    }
    return { valid: true };
}

frappe.ui.form.on("Bale Weight Info", {
    save_weight: async function (frm) {
        const result = await validate_bale_data(frm);
        if (!result.valid) {
            frappe.validated = false;
            return;
        }
        await frm.events.update_bale_weight_details(frm, true);
    },
    after_save: function (frm) {
        render_main_pending_bales_list(frm);
        frm.toggle_enable('bale_registration_code', frm.is_new());
        setTimeout(() => {
            const $input = frm.fields_dict.scan_barcode.$wrapper.find('input');
            if ($input.length) {
                $input.focus();
            }
        }, 100);
    },
    validate: async function (frm) {

        const result = await validate_bale_data(frm);
        if (!result.valid) {
            frappe.validated = false;
            return;
        }
        const values = frm.doc;
        frm.doc.detail_table.push({
            bale_barcode: values.scan_barcode,
            item_grade: values.item_grade,
            item_sub_grade: values.item_sub_grade,
            weight: values.bale_weight,
            rate: values.price,
            reclassification_grade: values.reclassification_grade
        });
        // frm.add_child("detail_table", {
        //     bale_barcode: values.scan_barcode,
        //     item_grade: values.item_grade,
        //     item_sub_grade: values.item_sub_grade,
        //     weight: values.bale_weight,
        //     rate: values.price,
        //     reclassification_grade: values.reclassification_grade
        // });
    },

    // Call this after grade popup closes too
    update_bale_weight_details: async function (frm, reload = true) {
        frm.save();
        // try {
        // const values = frm.doc;

        // const insert_response = await frappe.call({
        //     method: "frappe.client.insert",
        //     args: {
        //         doc: {
        //             doctype: "Bale Weight Detail",
        //             parent: frm.doc.name,
        //             parenttype: "Bale Weight Info",
        //             parentfield: "detail_table",
        //             bale_barcode: values.scan_barcode,
        //             item_grade: values.item_grade,
        //             item_sub_grade: values.item_sub_grade,
        //             weight: values.bale_weight,
        //             rate: values.price,
        //             reclassification_grade: values.reclassification_grade
        //         }
        //     }
        // });


        // if (insert_response && !insert_response.exc && reload) {
        //     await frm.reload_doc();  // Refresh to show updated child table
        // }



        // } catch (error) {
        //     console.error("Error updating bale details:", error);
        //     frappe.msgprint(__('An error occurred while saving Bale Weight Detail.'));
        // }
    },

    scan_barcode: async function (frm) {
        const barcode = frm.doc.scan_barcode;
        const $barcode_input = frm.fields_dict.scan_barcode.$wrapper.find('input');

        if (barcode && barcode.length == frm.doc.barcode_length) {
            if (frm.doc.bale_registration_code) {
                if (!is_grade_popup_open) await proceedWithBarcodeValidationAndGradeMainPage(frm, barcode);
            } else {
                frappe.call({
                    method: 'leaf_procurement.leaf_procurement.api.bale_weight_utils.get_bale_registration_code_by_barcode',
                    args: { barcode: barcode },
                    callback: function (r) {
                        if (r.message) {
                            const registration_code = r.message;

                            frm.set_value('bale_registration_code', registration_code);

                            frappe.call({
                                method: 'frappe.client.get',
                                args: {
                                    doctype: 'Bale Registration',
                                    name: registration_code
                                },
                                callback: async function (res) {
                                    if (res.message) {
                                        const details = res.message.bale_registration_detail || [];
                                        frm.bale_registration_barcodes = details
                                            .map(row => row.bale_barcode)
                                            .filter(b => !!b);

                                        if (typeof is_grade_popup_open === 'undefined' || !is_grade_popup_open) {
                                            if (!is_grade_popup_open) await proceedWithBarcodeValidationAndGradeMainPage(frm, barcode);
                                        }
                                    } else {
                                        frappe.show_alert({
                                            message: `⚠️ No details found for Bale Registration ${registration_code}`,
                                            indicator: 'orange'
                                        });
                                        frm.set_value('bale_registration_code', '');
                                    }
                                }
                            });
                        } else {
                            frappe.show_alert({
                                message: '⚠️ Bale Registration not found for scanned barcode.',
                                indicator: 'red'
                            });
                            frm.set_value('bale_registration_code', '');
                            frm.set_value('scan_barcode', '');
                            setTimeout(() => {
                                const $input = frm.fields_dict.scan_barcode.$wrapper.find('input');
                                if ($input.length) {
                                    $input.focus();
                                }
                            }, 100);


                        }
                    }
                });
            }
        } else if (barcode && barcode.length > frm.barcode_length) {
            frappe.show_alert({
                message: '⚠️ Invalid barcode length.',
                indicator: 'red'
            });
            frm.set_value('scan_barcode', '');
        }
    }
    ,

    bale_registration_code: function (frm) {
        validate_day_status(frm);
        load_bale_barcodes(frm);
    },
    refresh: function (frm) {
        if (frm.doc.docstatus === 1) {
            frm.fields_dict['detail_table'].grid.update_docfield_property(
                'delete_row', 'hidden', 1
            );
        }

        // frm.set_value('scan_barcode', '');
        // frm.set_value('item_grade', '');
        // frm.set_value('item_sub_grade', '');
        // frm.set_value('reclassification_grade', '');
        // frm.set_value('price', '');        

    },
    date: function (frm) {
        validate_day_status(frm);

    },
    onUnload: function (frm) {
        // Optional: if you want to close on leaving the module
        cleanupSerial(frm);
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


        if (!frm.is_new()) {
            frm.set_df_property('bale_registration_code', 'read_only', 1);
        } else {
            frm.set_df_property('bale_registration_code', 'read_only', 0);
        }

        //scaleConnected = "Disconnected";
        updateScaleStatus(frm, scaleConnected);

        if (scaleConnected == 'Connected') {
            frm.fields_dict.connect_scale.$wrapper.hide();
            frm.fields_dict.disconnect_scale.$wrapper.show();
        }
        else {
            frm.fields_dict.connect_scale.$wrapper.show();
            frm.fields_dict.disconnect_scale.$wrapper.hide();
        }

        if (frm.doc.docstatus === 1) {
            frm.fields_dict['detail_table'].grid.update_docfield_property(
                'delete_row', 'hidden', 1
            );
        }

        load_bale_barcodes(frm);
        //console.log('before: ',frm);
        setTimeout(() => {
            const $input = frm.fields_dict.scan_barcode.$wrapper.find('input');
            if ($input.length) {
                $input.focus();
            }
        }, 100);

        if (!frm.is_new()) return;

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

        //to load lot number in the dropdown
        // frappe.call({
        //     method: 'leaf_procurement.leaf_procurement.api.bale_weight_utils.get_available_bale_registrations',
        //     args: {
        //         doctype: 'Bale Registration',
        //         txt: '',
        //         searchfield: 'name',
        //         start: 0,
        //         page_len: 1,
        //         filters: {}
        //     },
        //     callback: function (r) {
        //         if (r.message && r.message.length > 0) {
        //             frm.set_value('bale_registration_code', r.message[0][0]);
        //         }
        //     }
        // });


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
                    frm.set_value('barcode_length', r.message.barcode_length);
                }
            }
        });


    }
});

let is_grade_popup_open = false;
function proceedWithBarcodeValidationAndGrade(frm, barcode, d) {
    const validBarcodes = frm.bale_registration_barcodes || [];
    const $barcode_input = frm.fields_dict.scan_barcode.$wrapper.find('input');

    if (!validBarcodes.includes(barcode)) {
        frappe.show_alert({
            message: __('❌ Invalid Bale Barcode: {0}', [barcode]),
            indicator: 'red'
        });
        d.set_value('scan_barcode', '');
        $barcode_input.focus();
        return;
    }

    const already_scanned = (frm.doc.detail_table || []).some(row => row.bale_barcode === barcode);
    if (already_scanned) {
        frappe.show_alert({
            message: __('⚠️ This Bale Barcode is already scanned: {0}', [barcode]),
            indicator: 'red'
        });
        d.set_value('scan_barcode', '');
        //updateWeightDisplay("0.00");
        $barcode_input.focus();
        return;
    }
    is_grade_popup_open = true;

    open_grade_selector_popup(function (grade, sub_grade) {
        d.set_value('p_item_grade', grade);
        d.set_value('p_item_sub_grade', sub_grade);

        frappe.call({
            method: "leaf_procurement.leaf_procurement.doctype.item_grade_price.item_grade_price.get_item_grade_price",
            args: {
                company: frm.doc.company,
                location_warehouse: frm.doc.location_warehouse,
                item: frm.doc.item,
                item_grade: grade,
                item_sub_grade: sub_grade
            },
            callback: function (r) {
                if (r.message !== undefined) {
                    d.set_value("p_price", r.message);
                }
                is_grade_popup_open = false;
            }
        });
    });
}


frappe.ui.form.on("Bale Weight Detail", {

    delete_row(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        // Ask for confirmation before deleting
        frappe.confirm(
            `Are you sure you want to delete this row: ${row.bale_barcode}?`,
            function () {
                // Call server method to delete the child record
                frappe.call({
                    method: "frappe.client.delete",
                    args: {
                        doctype: row.doctype,
                        name: row.name
                    },
                    callback: function (response) {
                        if (!response.exc) {
                            frappe.msgprint(__("Row deleted successfully"));

                            // Remove from form UI
                            frappe.model.clear_doc(cdt, cdn);
                            frm.refresh_field('detail_table');

                            if (cur_dialog) {
                                cur_dialog.hide();
                            }
                            $('.modal-backdrop').remove();
                            frm.reload_doc();
                        }
                    }
                });
            }
        );
    },


    refresh: function (frm) {
        frm.toggle_enable('bale_registration_code', frm.is_new());
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


function open_grade_selector_popup(callback) {
    let selected_grade = null;
    let selected_sub_grade = null;
    let selected_reclassification_grade = null;
    let is_rejected_grade = false;

    const dialog = new frappe.ui.Dialog({
        title: 'Select Item Grade & Sub Grade',
        fields: [
            // Start of the section
            { fieldtype: 'Section Break' },

            // Column 0: Grade & Sub Grade
            { fieldtype: 'Column Break' },
            {
                fieldtype: 'HTML',
                options: `<h4 style="margin-top:0;">Grade</h4>`
            },
            {
                fieldname: 'grade_html',
                fieldtype: 'HTML',
                options: '<div id="grade-buttons" style="margin-bottom: 1rem;"></div>'
            },
            {
                fieldtype: 'HTML',
                options: `<h4 style="margin-top:20px;">Sub Grade</h4>`
            },
            {
                fieldname: 'sub_grade_html',
                fieldtype: 'HTML',
                options: '<div id="sub-grade-buttons" style="margin-bottom: 1rem;"></div>'
            },

            // Column 1: Reclassification Grade
            { fieldtype: 'Column Break' },
            {
                fieldtype: 'HTML',
                options: `<h4 style="margin-top:0;">Reclassification Grade</h4>`
            },
            {
                fieldname: 'reclassification_grade_html',
                fieldtype: 'HTML',
                options: '<div id="reclassification-grade-buttons" style="margin-bottom: 1rem;"></div>'
            },

            {
                fieldname: 'selected_summary_html',
                fieldtype: 'HTML',
                options: `
        <div style="border: 1px solid var(--gray-300); border-radius: 4px; margin-top: 20px; padding: 12px;">
            <h4 class="mb-3">Selected:</h4>
            <p><strong>Grade:</strong>
                <span id="selected-grade"
                      class="indicator-pill green"
                      style="font-size: 1.2em; padding: 4px 12px; border-radius: 12px;">
                </span>
            </p>
            <p><strong>Sub Grade:</strong>
                <span id="selected-sub-grade"
                      class="indicator-pill orange"
                      style="font-size: 1.2em; padding: 4px 12px; border-radius: 12px;">
                </span>
            </p>
            <p><strong>Reclassification Grade:</strong>
                <span id="selected-reclassification-grade"
                      class="indicator-pill blue"
                      style="font-size: 1.2em; padding: 4px 12px; border-radius: 12px;">
                </span>
            </p>
        </div>
    `
            }




        ],
        primary_action_label: 'Select',
        primary_action: function () {
            if (!selected_grade || !selected_sub_grade || !selected_reclassification_grade) {
                frappe.msgprint('Please select grade, sub grade and reclassification grade');
                return;
            }
            dialog.hide();
            callback(selected_grade, selected_sub_grade, selected_reclassification_grade);
        }
    });

    function render_grade_buttons() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Item Grade',
                fields: ['name', 'rejected_grade']
            },
            callback: function (r) {
                if (r.message) {

                    const sortedGrades = r.message.sort((a, b) => {
                        return a.rejected_grade - b.rejected_grade;
                    });
                    const container = dialog.fields_dict.grade_html.$wrapper;
                    container.empty();

                    sortedGrades.forEach(grade => {
                        const colorClass = grade.rejected_grade ? 'indicator-pill red' : 'indicator-pill green';
                        const $btn = $(`
                            <button class="btn btn-sm grade-btn m-1 ${colorClass}" style="
                                min-width: 98px;
                                text-align: center;
                            ">${grade.name}</button>
                        `);
                        $btn.on('click', function () {
                            if (grade.rejected_grade)
                                is_rejected_grade = true;
                            else
                                is_rejected_grade = false;

                            selected_grade = grade.name;
                            selected_sub_grade = null;
                            render_sub_grade_buttons(grade.name);
                            $('.grade-btn').removeClass('btn-success').addClass('btn-primary');
                            $(this).removeClass('btn-primary').addClass('btn-success');
                            update_selected_summary();

                        });
                        container.append($btn);
                    });
                }
            }
        });
    }
    function update_selected_summary() {
        const $grade = dialog.$wrapper.find('#selected-grade');
        const $subGrade = dialog.$wrapper.find('#selected-sub-grade');
        const $reGrade = dialog.$wrapper.find('#selected-reclassification-grade');

        // Handle Grade with rejection suffix
        if (selected_grade && is_rejected_grade) {

            $grade
                .text(selected_grade)
                .removeClass('red')
                .removeClass('green')
                .addClass('red');
        } else {
            $grade
                .text(selected_grade)
                .removeClass('green')
                .removeClass('red')
                .addClass('green');
        }

        // Sub Grade (assume always green)
        $subGrade
            .text(selected_sub_grade || '')
            .removeClass('red blue')
            .addClass('green');

        // Reclassification Grade (assume blue)
        $reGrade
            .text(selected_reclassification_grade || '')
            .removeClass('red green')
            .addClass('blue');
    }


    function render_sub_grade_buttons(grade) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Item Sub Grade',
                fields: ['name'],
                filters: { item_grade: grade }
            },
            callback: function (r) {
                const container = dialog.fields_dict.sub_grade_html.$wrapper;
                container.empty();
                r.message.forEach(sub_grade => {
                    const $btn = $(`
                        <button class="btn btn-sm indicator-pill orange m-1 sub-grade-btn" style="
                            min-width: 100px;
                            text-align: center;
                        ">${sub_grade.name}</button>
                    `);
                    $btn.on('click', function () {
                        selected_sub_grade = sub_grade.name;
                        $('.sub-grade-btn').removeClass('btn-success').addClass('btn-outline-secondary');
                        $(this).removeClass('btn-outline-secondary').addClass('btn-success');
                        update_selected_summary();
                    });
                    container.append($btn);
                });
            }
        });
    }
    function render_reclassification_grade_buttons() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Reclassification Grade',
                fields: ['name']
            },
            callback: function (r) {
                if (r.message) {

                    const sortedGrades = r.message.sort((a, b) => a.name.localeCompare(b.name));

                    const container = dialog.fields_dict.reclassification_grade_html.$wrapper;
                    container.empty();

                    sortedGrades.forEach(grade => {
                        const colorClass = 'indicator-pill blue';
                        const $btn = $(`
                        <button class="btn btn-sm reclassification-grade-btn m-1 ${colorClass}" style="
                            min-width: 98px;
                            text-align: center;
                        ">${grade.name}</button>
                    `);
                        $btn.on('click', function () {
                            selected_reclassification_grade = grade.name;
                            $('.reclassification-grade-btn').removeClass('btn-success').addClass('btn-primary');
                            $(this).removeClass('btn-primary').addClass('btn-success');
                            update_selected_summary();
                        });
                        container.append($btn);
                    });
                }
            }
        });
    }
    dialog.show();
    is_grade_popup_open = true;
    render_grade_buttons();
    render_reclassification_grade_buttons();
}


function update_bale_counter(frm) {
    let total = frm.doc.total_bales;  // increment before recounting
    frm.doc.remaining_bales = total - (frm.doc.detail_table || []).length;
    frm.refresh_field('remaining_bales');
}

function validate_day_status(frm) {
    if (!frm.doc.date) return;
    if (!frm.doc.bale_registration_code) return;
    // If registration_date is set, validate it matches doc.date
    if (frm.doc.registration_date) {
        if (frm.doc.date !== frm.doc.registration_date) {
            let baleDate = '2025-06-01';
            let docDate = '2025-06-06';

            frappe.show_alert({
                message: __('The selected Bale Registration was created on <b>{0}</b>, which does not match this document\'s date <b>{1}</b>', [frm.doc.registration_date, frm.doc.date]),
                indicator: 'orange'
            }, 5);

            // frappe.msgprint({
            //     title: __("Date Mismatch"),
            //     message: __("⚠️ The selected Bale Registration was created on <b>{0}</b>, which does not match this document's date <b>{1}</b>.")
            //         .replace('{0}', frm.doc.registration_date)
            //         .replace('{1}', frm.doc.date),
            //     indicator: 'red'
            // });
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


            if (!is_day_open) {
                frappe.show_alert({
                    message: 'Day is not open for selected date.',
                    indicator: 'orange'
                }, 5);
                // frappe.msgprint({
                //     title: __("Day Not Open"),
                //     message: __("⚠️ You cannot register or purchase bales because the day is either not opened or already closed."),
                //     indicator: 'red'
                // });
            }
        }
    });
}

function load_bale_barcodes(frm) {
    if (!frm.doc.bale_registration_code) {
        frm.bale_registration_barcodes = [];  // Clear any old data
        return;
    }



    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Bale Registration',
            name: frm.doc.bale_registration_code
        },
        callback: function (r) {
            if (r.message) {
                const details = r.message.bale_registration_detail || [];

                // Extract bale barcodes and store them in a custom property on the form
                frm.bale_registration_barcodes = details
                    .map(row => row.bale_barcode)
                    .filter(barcode => !!barcode);  // Filter out any empty/null values

                //console.log("✅ Loaded Barcodes:", frm.bale_registration_barcodes);
            } else {
                frm.bale_registration_barcodes = [];
                frappe.msgprint(__('⚠️ No details found for this Bale Registration.'));
            }
        }
    });
    setTimeout(() => {
        render_main_pending_bales_list(frm);
    }, 300);
}



// function hide_grid_controls(frm) {

//     const grid_field = frm.fields_dict.detail_table;
//     if (grid_field && grid_field.grid && grid_field.grid.wrapper) {
//         grid_field.grid.wrapper
//             .find('.grid-add-row,  .btn-open-row')
//             //.find('.grid-add-row, .grid-remove-rows, .btn-open-row')
//             .hide();
//     }
// }
