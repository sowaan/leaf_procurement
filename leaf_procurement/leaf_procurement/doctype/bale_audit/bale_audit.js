let scaleReader = null;
let scalePort = null;
let lastWeight = null;
let stopReading = false;
let suppress_focus = false;

frappe.ui.form.on("Bale Audit", {
    refresh(frm) {

    },
    onload: function (frm) {
        if (!frm.is_new) return;

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

                    frm.set_value('item', r.message.default_item);
                    frm.set_value('barcode_length', r.message.barcode_length);
                }
            }
        });
    },
    add_audit_weight: function (frm) {
        const d = new frappe.ui.Dialog({
            title: 'Capture Weight Information',
            fields: [
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'p_bale_barcode',
                    label: 'Bale BarCode',
                    fieldtype: 'Data',
                    reqd: 1,
                },

                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'p_weight',
                    label: 'Captured Weight',
                    fieldtype: 'Float',
                    reqd: 1,
                    read_only: 0
                },
                {
                    fieldtype: 'Section Break'
                }
            ],
            primary_action_label: 'Add Weight',
            primary_action: function (values) {
                const expectedLength = frm.doc.barcode_length || 0;
                if (values.p_bale_barcode.length != expectedLength)
                {
                    frappe.msgprint(__('Please enter a valid barcode of {0} digits.', [expectedLength]));
                    return;
                }

                frm.add_child('detail_table', {
                    bale_barcode: values.p_bale_barcode,
                    weight: values.p_weight,
                });

                frm.refresh_field('detail_table');

                // Reset fields
                d.set_value('p_bale_barcode', '');
                d.set_value('p_weight', '');

                // Reset weight display
                updateWeightDisplay("0.00");

                // Focus barcode field again
                setTimeout(() => {
                    suppress_focus = false;
                    const $barcode_input = d.fields_dict.p_bale_barcode.$wrapper.find('input');
                    $barcode_input.focus();

                }, 300);


            }

        });

        d.onhide = function () {
            //console.log('on hide');
            if (document.activeElement) {
                document.activeElement.blur();
            }
            cleanupSerial();
        };
        // Prevent Enter key from submitting dialog
        setTimeout(() => {
            const barcode_input = d.fields_dict.p_bale_barcode.$wrapper.find('input').get(0);
            if (barcode_input) {
                barcode_input.addEventListener('keydown', function (e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        e.stopPropagation();
                        // Optionally, you can trigger your add_weight logic here manually
                        // or just prevent Enter from submitting form on barcode input
                    }
                });
            }
        }, 100);


        d.show();

        const $barcode_input = d.fields_dict.p_bale_barcode.$wrapper.find('input');

        $barcode_input.on('keyup', function (e) {
            const barcode = $(this).val();
            const expectedLength = frm.doc.barcode_length || 0;

            if (e.key === 'Enter' || barcode.length === expectedLength) {
                //d.set_primary_action_state('enabled');

            }
            else{
               // d.set_primary_action_state('disabled');

            }
        });

        const $footer = d.$wrapper.find('.modal-footer');
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

        function updateWeightDisplay(weight) {
            $weightDisplay.text(weight + " kg");
            d.set_value('p_weight', weight);
        }

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
                            updateWeightDisplay(lastWeight);
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
    refresh: function(frm) {
        // frm is defined here
    },
    delete_row(frm, cdt, cdn) {
        frappe.model.clear_doc(cdt, cdn);  // delete the row
        frm.refresh_field('detail_table');

            if (cur_dialog) {
                cur_dialog.hide();
            }

            // Remove any lingering modal backdrop
            $('.modal-backdrop').remove();        
    },
    

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