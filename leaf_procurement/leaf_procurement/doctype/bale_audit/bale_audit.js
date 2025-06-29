let scaleReader = null;
let scalePort = null;
let lastWeight = null;
let stopReading = false;
let suppress_focus = false;
let scaleConnected = 'Disconnected';
let updateWeightOnForm = true;
if (!window._scaleConnection) {
    window._scaleConnection = {
        port: null,
        reader: null,
        lastWeight: null,
        stopReading: false
    };
}
function updateMainWeightDisplay(frm, weight) {
    if (updateWeightOnForm) {
        frm.set_value('captured_weight', weight);
    }
    let color = scaleConnected === "Connected" ? "#007bff" : "red";
    let html = `<h2 style="color: ${color}; font-weight: bold;">Scale: ${scaleConnected}<br />${weight}</h2>`;
    frm.fields_dict.scale_status.$wrapper.html(html);
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

    function update_audit_display(frm) {
        let total_bales = frm.doc.detail_table.length;
        let total_weight = 0;

        frm.doc.detail_table.forEach(row => {
            if (row.weight) {
                total_weight += flt(row.weight);
            }
        });

        let html = `
            <div style="padding: 10px; font-size: 14px;">
                <b>Total Scanned Bales:</b> ${total_bales} <br>
                <b>Total Weight:</b> ${total_weight} kg
            </div>
        `;

        frm.set_df_property("audit_display", "options", html);
        frm.refresh_field("audit_display");
    }
    async function validate_bale_data(frm) {
        if (!frm.doc.bale_barcode && frm.doc.detail_table.length === 0) 
        {
            frappe.show_alert({ 
                message: __('You must add at least one row in the Detail Table before saving.'), 
                indicator: "red" 
            });            
            return { valid: false };            
      
        }
            
        if (!frm.doc.bale_barcode)return{valid:true};

        const values = frm.doc;
        const weight = values.captured_weight;

        const expectedLength = frm.doc.barcode_length || 0;
        if (frm.doc.bale_barcode.length != expectedLength) {
            frappe.show_alert({ 
                message: __('Please enter a valid barcode of {0} digits.', [expectedLength]), 
                indicator: "red" 
            });
            return { valid: false };
        }

    
        const existing = values.detail_table.find(row => row.bale_barcode === values.bale_barcode);
        if (existing) {
            frappe.show_alert({
                message: `Bale with barcode ${values.bale_barcode} already exists in the table.`,
                indicator: 'red'
            });
            return { valid: false };
        }

        if(weight<=0){
            frappe.show_alert({ message: __("Please enter weight information to continue."), indicator: "red" });
            return { valid: false };
        }

        return {valid:true};

    }
frappe.ui.form.on("Bale Audit", {
    onUnload: function (frm) {
        // Optional: if you want to close on leaving the module
        cleanupSerial(frm);
    },
    location_warehouse: async function(frm){
        const open_day = await get_open_day_date(frm.doc.location_warehouse);  // ✅ Use value directly
        if (open_day) {
            frm.set_value('date', open_day.date);
            frm.set_value('day_setup', open_day.name);
        } else {
            frappe.msgprint(__('There is no open audit day, you cannot add audit records.'));
        }

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
    onload: async function (frm) {
        update_audit_display(frm);
        frm.page.sidebar.toggle(false);
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

        setTimeout(() => {
            const $input = frm.fields_dict.bale_barcode.$wrapper.find('input');
            if ($input.length) {
                $input.focus();
            }
        }, 100);

        if (!frm.is_new()) return;
    const settings = await new Promise((resolve, reject) => {
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
    after_save: async function (frm){
            update_audit_display(frm);


    },
    validate: async function (frm) {
        const result = await validate_bale_data(frm);
        if (!result.valid) {
            frappe.validated = false;
            return;
        }
        
        const values = frm.doc;
        const weight = values.captured_weight;
        if(!values.bale_barcode) return;
       // console.log('is rejected:', is_rejected_grade);
        frm.doc.detail_table.push({
            bale_barcode: values.bale_barcode,
            weight: weight,
            bale_remarks: values.bale_comments,
        });        

                // Reset fields
        frm.set_value('bale_barcode', '');
        frm.set_value('captured_weight', '');
        frm.set_value('bale_comments', '');
        // Reset weight display


        // Focus barcode field again
        setTimeout(() => {
            suppress_focus = false;
            const $barcode_input = frm.fields_dict.bale_barcode.$wrapper.find('input');
            $barcode_input.focus();

        }, 300);
    },
    add_audit_weight: async function (frm) {

        if (!frm.doc.bale_barcode) {
            frappe.show_alert({ 
                message: __('Please enter a valid barcode to add audit information.'), 
                indicator: "red" 
            });        
            return;
        };

        const result = await validate_bale_data(frm);

        if (!result.valid) {
            return;
        }

        frm.add_child('detail_table', {
            bale_barcode: frm.doc.bale_barcode,
            weight: frm.doc.captured_weight,
            bale_remarks: frm.doc.bale_comments
        });

        frm.refresh_field('detail_table');

        // Reset fields
        frm.set_value('bale_barcode', '');
        frm.set_value('captured_weight', '');
        frm.set_value('bale_comments', '');
        // Reset weight display
        updateMainWeightDisplay(frm, "0.00");

        // Focus barcode field again
        setTimeout(() => {
            suppress_focus = false;
            update_audit_display(frm);
            const $barcode_input = frm.fields_dict.bale_barcode.$wrapper.find('input');
            $barcode_input.focus();

        }, 300);
        const $barcode_input = frm.fields_dict.bale_barcode.$wrapper.find('input');

        $barcode_input.on('keyup', function (e) {
            const barcode = $(this).val();
            const expectedLength = frm.doc.barcode_length || 0;

            if (e.key === 'Enter' || barcode.length === expectedLength) {
                //d.set_primary_action_state('enabled');

            }
            else {
                // d.set_primary_action_state('disabled');

            }
        });

        const $footer = frm.$wrapper.find('.modal-footer');
        const $weightDisplay = $(`
            <div style="
                font-size: 50px;
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



        const connectBtn = $(`<button class="btn btn-secondary btn-sm ml-2">Connect Scale</button>`);
        $footer.prepend(connectBtn);

        connectBtn.on('click', async () => {
            try {
                scalePort = await navigator.serial.requestPort();
                await scalePort.open({ baudRate: 9600 });

                const textDecoder = new TextDecoderStream();
                const readableStreamClosed = scalePort.readable.pipeTo(textDecoder.writable);
                const reader = textDecoder.readable.getReader();

                scaleReader = reader;
                window._readableStreamClosed = readableStreamClosed;
                stopReading = false;

                while (!stopReading) {
                    const { value, done } = await reader.read();
                    if (done || stopReading) break;
                    if (value) {
                        const weight = parseFloat(value.trim());
                        if (!isNaN(weight)) {
                            lastWeight = weight.toFixed(2);
                            updateMainWeightDisplay(lastWeight);
                        }
                    }
                }


            } catch (err) {
                console.error('Serial error:', err);
                frappe.msgprint(__('Failed to connect or read from scale.'));
                await cleanupSerial();
            }
        });
    }

});

frappe.ui.form.on("Bale Audit Detail", {
    refresh: function (frm) {
        // frm is defined here
        update_audit_display(frm);
    },
delete_row: function(frm, cdt, cdn) {
    const row = locals[cdt][cdn];

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

                        // Fully remove the row from locals and doc
                        frappe.model.clear_doc(cdt, cdn);

                        // Remove from doc.detail_table (redundant but safe)
                        frm.doc.detail_table = frm.doc.detail_table.filter(r => r.name !== row.name);

                        // Refresh field & mark dirty
                        frm.refresh_field('detail_table');
                        frm.dirty(); // OR frm.set_dirty();

                        frm.trigger("update_audit_display");

                        if (cur_dialog) cur_dialog.hide();
                        $('.modal-backdrop').remove();
                    }
                }
            });
        }
    );
}



});
async function get_open_day_date(location_name) {
    console.log('location: ', location_name);
    return new Promise((resolve, reject) => {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Audit Day Setup",
                filters: {
                    status: "Opened",
                    location_warehouse: location_name
                },
                fields: ["name", "date"],
                limit_page_length: 1,
                order_by: "date desc"
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    console.log('message: ', r.message);
                    resolve({
                        date: r.message[0].date,
                        name: r.message[0].name
                    });
                } else {
                    resolve(null);
                }
            },
            error: function (err) {
                reject(err);
            }
        });
    });
}
