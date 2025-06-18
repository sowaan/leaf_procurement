// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt
let suppress_focus = false;
let is_grade_popup_open = false;
let is_rendering_main_pending_bales = false;

function open_grade_selector_popup(callback) {
    let selected_grade = null;
    let selected_sub_grade = null;

    const dialog = new frappe.ui.Dialog({
        title: 'Select Item Grade & Sub Grade',
        fields: [
            {
                fieldname: 'grade_html',
                fieldtype: 'HTML',
                options: '<div id="grade-buttons" style="margin-bottom: 1rem;"></div>'
            },
            {
                fieldtype: 'HTML',
                options: `<hr style="margin: 0.5rem 0; border-top: 1px solid #ddd;">`
            },
            {
                fieldname: 'sub_grade_html',
                fieldtype: 'HTML',
                options: '<div id="sub-grade-buttons"></div>'
            }
        ],

        primary_action_label: 'Select',
        primary_action: function () {

            if (!selected_grade || !selected_sub_grade) {
                frappe.msgprint('Please select both grade and sub grade');
                return;
            }

            callback(selected_grade, selected_sub_grade);

            dialog.hide();
        }
    });
    dialog.onhide = function () {
        is_grade_popup_open = false;
    };
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
                            selected_grade = grade.name;
                            selected_sub_grade = null;
                            render_sub_grade_buttons(grade.name);
                            $('.grade-btn').removeClass('btn-success').addClass('btn-primary');
                            $(this).removeClass('btn-primary').addClass('btn-success');
                        });
                        container.append($btn);
                    });
                }
            }
        });
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
                    });
                    container.append($btn);
                });
            }
        });
    }

    dialog.show();
    render_grade_buttons();
}

function update_grade_box(frm)
{
        //if (frm.doc.supplier_grower && frm.doc.item_grade && frm.doc.item_sub_grade) {
            let html = `
                <div style="
                    background-color: #f0f8ff;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    font-family: sans-serif;
                ">
                    <div style="font-size: 24px; font-weight: bold; color: #2c3e50;">
                        ${frm.doc.supplier_grower || ''}
                    </div>
                    <div style="font-size: 20px; margin-top: 10px; color: #16a085;">
                        Grade: ${frm.doc.item_grade || ''}
                    </div>
                    <div style="font-size: 18px; margin-top: 5px; color: #8e44ad;">
                        Sub-grade: ${frm.doc.item_sub_grade || ''}
                    </div>
                    <div style="font-size: 20px; margin-top: 10px; color: #16a085;">
                        Price: ${frm.doc.price || ''}
                    </div>          
                    </div>
            `;
            frm.fields_dict.grade_list.$wrapper.html(html);    
}
async function validate_bale_data(frm) {
    const values = frm.doc;
    const weight = values.bale_weight;

    if (!values.bale_barcode) {
        frappe.show_alert({ message: __("Please scan a barcode before saving detail."), indicator: "orange" });
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

    if (!values.item_grade || !values.item_sub_grade) {
        frappe.show_alert({
            message: `Please select Grade and Sub-Grade to save weight information.`,
            indicator: 'red'
        });
        return { valid: false };
    }

    const validBarcodes = frm.bale_registration_barcodes || [];
    const $barcode_input = frm.fields_dict.bale_barcode.$wrapper.find('input');

    if (!validBarcodes.includes(values.bale_barcode)) {
        frappe.show_alert({
            message: __('Invalid Bale Barcode: {0}', [values.bale_barcode]),
            indicator: 'red'
        });
        frm.set_value('bale_barcode', '');
        $barcode_input.focus();
        return { valid: false };
    }    
    return { valid: true };
}


frappe.ui.form.on("Bale Purchase", {
    on_submit: function(frm) {
        frappe.msgprint({
            title: __('Success'),
            message: __('Record submitted successfully.'),
            indicator: 'green'
        });

        // Use frappe.new_doc in a safe callback
        setTimeout(() => {
            if (frm && frm.doc && frm.doc.doctype === 'Bale Purchase') {
                frappe.new_doc('Bale Purchase');
            }
        }, 1000); // Wait 1 second
            
    },    
    

    save_weight: async function (frm) {
        // const result = await validate_bale_data(frm);
        // if (!result.valid) {
        //     frappe.validated = false;
        //     return;
        // }
        await frm.events.update_bale_weight_details(frm, true);
    },

    after_save: function (frm) {
        //render_main_pending_bales_list(frm);
                setTimeout(() => {
            const $input = frm.fields_dict.bale_barcode.$wrapper.find('input');
            if ($input.length) {
                $input.focus();
            }
        }, 100);
    },
    validate: async function (frm) {
        if(!frm.doc.bale_barcode) return;

        const result = await validate_bale_data(frm);
        if (!result.valid) {
            frappe.validated = false;
            return;
        }
        const values = frm.doc;
        frm.doc.detail_table.push({
            bale_barcode: values.bale_barcode,
            item_grade: values.item_grade,
            item_sub_grade: values.item_sub_grade,
            weight: values.bale_weight,
            rate: values.price,
            reclassification_grade: values.reclassification_grade
        });
 
    },

    update_bale_weight_details: async function (frm, reload = true) {
    frm.save();
    },

    add_grades: function (frm) {

        const total = cint(frm.doc.total_bales || 0);
        const scanned = (frm.doc.detail_table || []).length;

        // Only apply this validation if bale_registration_code is set
        if (frm.doc.bale_registration_code && scanned >= total) {
            frappe.msgprint(__('⚠️ Purchase completed for all bales in this lot, please remove a bale and press try again if you need to update a record.'));
            return false;  // Prevent further action (e.g. opening popup)
        }

        const d = new frappe.ui.Dialog({
            title: 'Capture Grade Information',
            size: 'extra-large',
            fields: [
                { fieldtype: 'Section Break' },
                { fieldtype: 'Column Break' }, // Left column
                // Grade label
                {
                    fieldname: 'p_message_label',
                    fieldtype: 'HTML',
                    options: `<div style="font-size: 1.0rem; font-weight: 500; color:rgb(240, 132, 8); margin-bottom: 8px;">
                <span id="message-label"></span>
            </div>`
                },
                {
                    fieldname: 'p_bale_registration_code',
                    label: 'Bale Barcode',
                    fieldtype: 'Data',
                    reqd: 1,
                },
                {
                    fieldname: 'p_item_grade',
                    label: 'Item Grade',
                    fieldtype: 'Link',
                    options: 'Item Grade',
                    reqd: 1,
                    read_only: 1,
                },
                {
                    fieldname: 'p_item_sub_grade',
                    label: 'Item Sub Grade',
                    fieldtype: 'Link',
                    options: 'Item Sub Grade',
                    reqd: 1,
                    read_only: 1,
                },
                {
                    fieldname: 'p_price',
                    label: 'Price',
                    fieldtype: 'Currency',
                    read_only: 1,
                },

                { fieldtype: 'Column Break' }, // Middle column
                {
                    fieldname: 'pending_bales_html',
                    fieldtype: 'HTML',
                    label: 'Pending Bales',
                    options: `<div id="pending-bales-container" 
                style="max-height: 350px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; font-family: monospace; border-radius: 10px;"></div>`
                },
                { fieldtype: 'Column Break' }, // Right column
                // Grade label
                {
                    fieldname: 'p_grade_label',
                    fieldtype: 'HTML',
                    options: `<div style="font-size: 2.5rem; font-weight: 700; color: #28a745; margin-bottom: 16px;">
                                Grade: <span id="grade-label">-</span>
                            </div>`
                },
                // Sub Grade label
                {
                    fieldname: 'p_subgrade_label',
                    fieldtype: 'HTML',
                    options: `<div style="font-size: 2.5rem; font-weight: 700; color: #28a745; margin-bottom: 16px;">
                                Sub-Grade: <span id="subgrade-label">-</span>
                            </div>`
                },
                // Price label
                {
                    fieldname: 'p_price_label',
                    fieldtype: 'HTML',
                    options: `<div style="font-size: 2.5rem; font-weight: 700; color: #007bff; margin-bottom: 8px;">
                                Price: <span id="price-label">-</span>
                            </div>`
                },
            ],
            primary_action_label: 'Add Item',
            primary_action: function (values) {
                frm.save();
                primary_action_function(frm, d, values);
                //ding_bales_list();
                $('#price-label').text('');
                $('#grade-label').text('');
                $('#subgrade-label').text('');


            }
        });
        d.onhide = function () {
            //console.log('on hide');
            is_grade_popup_open = false;
            if (document.activeElement) {
                document.activeElement.blur();
            }

        };

        setTimeout(() => {
            const barcode_input = d.fields_dict.p_bale_registration_code.$wrapper.find('input').get(0);
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
        is_grade_popup_open = false;


        async function render_pending_bales_list() {
            //console.log('this is also running....');
            const container = d.fields_dict.pending_bales.$wrapper.find('#pending-bales-container');
            container.empty();

            if (!frm.bale_registration_barcodes || frm.bale_registration_barcodes.length === 0) {
                container.html('<div>No bales available for this lot.</div>');
                return;
            }

            if (frm.bale_registration_barcodes.length === frm.doc.total_bales) return;

            // Header row with two columns: Barcode and Status
            const $header = $(`
                <div style="display: flex; font-weight: bold; padding-bottom: 6px; border-bottom: 1px solid #ccc;">
                    <div style="flex: 1 1 13ch; min-width: 13ch; font-family: monospace;">Bale Barcode</div>
                    <div style="flex: 0 0 8ch; text-align: center;">Status</div>
                </div>
            `);
            container.append($header);
            const processed_barcodes = (frm.doc.detail_table || [])
                .map(row => row.bale_barcode)
                .filter(barcode => !!barcode);

            const pending_barcodes = frm.bale_registration_barcodes.filter(b => !processed_barcodes.includes(b));

            //const message_label = d.fields_dict.p_message_label.$wrapper.find('#message-label');
const message_label = frm.fields_dict.message_label.$wrapper;
// console.log('here...');
// console.log('check', pending_barcodes.length);
            if (pending_barcodes.length == 2) {
                message_label.text('⚠️ The next bale is the last one for this lot!');
            } else {
                message_label.text('');
            }

            Array.from(new Set(frm.bale_registration_barcodes)).forEach(barcode => {
                const is_processed = processed_barcodes.includes(barcode);
                const statusText = is_processed ? '✅' : '';
                const statusBgColor = is_processed ? '#d4edda' : '#fff3cd';
                const statusTextColor = is_processed ? '#155724' : '#856404';

                // Barcode cell
                const $barcodeCell = $(`<div style="
                                        flex: 1 1 13ch;
                                        min-width: 13ch;
                                        white-space: nowrap;
                                        overflow: hidden;
                                        text-overflow: ellipsis;
                                        font-family: monospace;
                                        padding: 4px 6px;
                                    ">${barcode}</div>`);

                // Status cell
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

                // Row container
                const $row = $('<div style="display: flex; align-items: center; margin: 2px 0;"></div>');
                $row.append($barcodeCell, $statusCell);

                if (!is_processed) {
                    $row.css('cursor', 'pointer');

                    $row.on('click', () => {
                        d.set_value('p_bale_registration_code', barcode);
                        proceedWithBarcodeValidationAndGrade(frm, barcode, d);

                    });
                } else {
                    $row.css('cursor', 'default');
                }

                container.append($row);
            });
        }



        const $barcode_input = d.fields_dict.p_bale_registration_code.$wrapper.find('input');

        $barcode_input.on('keyup', function (e) {
            const barcode = $(this).val();
            const expectedLength = parseInt(frm.doc.barcode_length || 0, 10);
            if (e.key === 'Enter' || barcode.length === expectedLength) {
                // If bale_registration_code already exists, skip fetching
                if (!frm.doc.bale_registration_code) {
                    // Step 1: Get bale_registration_code using barcode
                    frappe.call({
                        method: 'leaf_procurement.leaf_procurement.api.bale_purchase_utils.get_bale_registration_code_by_barcode',
                        args: { barcode: barcode },
                        callback: function (r) {
                            if (r.message) {
                                frm.set_value('bale_registration_code', r.message);


                                setTimeout(() => {

                                    //if (!is_grade_popup_open)

                                    proceedWithBarcodeValidationAndGrade(frm, barcode, d);
                                
                                    //$barcode_input.focus();
                                }, 300);
                            }
                            else {

                                frappe.msgprint(__('⚠️ Bale Registration not found for scanned barcode.'));
                                d.set_value('p_bale_registration_code', '');
                                // $barcode_input.focus();

                            }
                        }
                    });
                }
                else {
                    //if (!is_grade_popup_open)
                    proceedWithBarcodeValidationAndGrade(frm, barcode, d);
                }

            }

        })

    },
    bale_registration_code: function(frm) {
        validate_day_status(frm);  // Optional validation if needed
        load_bale_barcodes(frm);

    },

    bale_barcode: async function (frm) {
        if (suppress_focus) return;  // Prevent focus if suppress is active
        const barcode = frm.doc.bale_barcode;
        if (barcode && barcode.length == frm.doc.barcode_length) {
            if (frm.doc.bale_registration_code) {
                if (!is_grade_popup_open) await proceedWithBarcodeValidationAndGrade(frm, barcode);
            }
            else{
               const barcode = frm.doc.bale_barcode;

    
            frappe.call({
                method: 'leaf_procurement.leaf_procurement.api.bale_weight_utils.get_bale_registration_code_by_barcode',
                args: { barcode: barcode },
                callback: async function (r) {
                    if (r.message) {
                        const registration_code = r.message;

                        frm.set_value('bale_registration_code', registration_code);

                        setTimeout(() => {
                            proceedWithBarcodeValidationAndGrade(frm, barcode);
                        }, 300)
                    }
                }
            });
            
                            
            }
        }

    },

    refresh: function (frm) {
        if (frm.doc.docstatus === 1) {
            frm.fields_dict['detail_table'].grid.update_docfield_property(
                'delete_row', 'hidden', 1
            );
        }
        hide_grid_controls(frm);
    
        load_bale_barcodes(frm);

        //update_grade_box(frm);
        // } else {
        //     frm.fields_dict.grade_list.$wrapper.html(`<p style="color:gray;">Grade details not available</p>`);
        // }
                //load_bale_barcodes(frm);
    },
    date: function (frm) {
        validate_day_status(frm);
    },
    onload: function (frm) {
        frm.page.sidebar.toggle(false);
        if (frm.doc.docstatus === 1) {
            frm.fields_dict['detail_table'].grid.update_docfield_property(
                'delete_row', 'hidden', 1
            );
        }
        //override bale_registration_code query to load 
        //bale registration codes with no purchase record

        // Set query filter for 'item_sub_grade' field in child table
        frm.fields_dict['detail_table'].grid.get_field('item_sub_grade').get_query = function (doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            return {
                filters: {
                    item_grade: child.item_grade
                }
            };
        };

        setTimeout(() => {
            const $input = frm.fields_dict.bale_barcode.$wrapper.find('input');
            if ($input.length) {
                $input.focus();
            }
        }, 100);

                  
                update_grade_box(frm);
      
        if (!frm.is_new) return;
        frm.set_query('bale_registration_code', function () {
            return {
                query: 'leaf_procurement.leaf_procurement.api.bale_purchase_utils.get_available_bale_registrations'
            };
        });
        //get company and location records from settings
        if (frm.is_new()) {
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
                        frm.set_value('barcode_length', r.message.barcode_length)
                    }
                }
            });
        }
    }
});

async function proceedWithBarcodeValidationAndGrade(frm, barcode) {
    const validBarcodes = frm.bale_registration_barcodes || []; // Ensure uniqueness
    const $barcode_input = frm.fields_dict.bale_barcode.$wrapper.find('input');

    if (!validBarcodes.includes(barcode)) {
        frappe.show_alert({ message: __('This Bale Barcode is not part of this lot.'), indicator: 'orange' });
        frm.set_value('bale_barcode', '');
        $barcode_input.focus();
        return;
    }

    const already_scanned = (frm.doc.detail_table || []).some(row => row.bale_barcode === barcode);


    if (already_scanned) {
        frappe.show_alert({
            message: __('⚠️ This Bale Barcode is already scanned: {0}', [barcode]),
            indicator: 'red'
        });
        frm.set_value('bale_barcode', '');
        $barcode_input.focus();
        return;
    }

    is_grade_popup_open = true;
    frm.set_value('bale_barcode', barcode);
    open_grade_selector_popup(async function (grade, sub_grade) {
        frm.set_value('item_grade', grade);
        frm.set_value('item_sub_grade', sub_grade);

        const r = await frappe.call({
            method: "leaf_procurement.leaf_procurement.doctype.item_grade_price.item_grade_price.get_item_grade_price",
            args: {
                company: frm.doc.company,
                location_warehouse: frm.doc.location_warehouse,
                item: frm.doc.item,
                item_grade: grade,
                item_sub_grade: sub_grade
            }
        });

        if (r.message !== undefined) {
            frm.set_value("price", r.message);
            setTimeout(() => {
                update_grade_box(frm);
            }, 100);
        }
        is_grade_popup_open = false;

    });
}


frappe.ui.form.on("Bale Purchase Detail", {
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
        console.log('hhhhh....');
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
    bale_purchase_detail_remove(frm) {
        update_bale_counter(frm);
    }
});

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
                frappe.msgprint({
                    title: __("Day Not Open"),
                    message: __("⚠️ You cannot register or purchase bales because the day is either not opened or already closed."),
                    indicator: 'red'
                });
            }
        }
    });
}

function primary_action_function(frm, d, values) {
    frm.add_child('detail_table', {
        bale_barcode: values.p_bale_registration_code,
        item_grade: values.p_item_grade,
        item_sub_grade: values.p_item_sub_grade,
        rate: values.p_price,
    });

    frm.refresh_field('detail_table');


    hide_grid_controls(frm);

    if (frm.doc.total_bales <= frm.doc.detail_table.length) {
        if (document.activeElement) {
            document.activeElement.blur();
        }
        d.hide();
    }

    // Reset fields
    d.set_value('p_bale_registration_code', '');
    d.set_value('p_item_grade', '');
    d.set_value('p_item_sub_grade', '');
    d.set_value('p_price', '');


    // Focus barcode field again
    setTimeout(() => {
        suppress_focus = false;
        const $barcode_input = d.fields_dict.p_bale_registration_code.$wrapper.find('input');
        $barcode_input.focus();

    }, 300);
}
async function load_bale_barcodes(frm) {
    is_rendering_main_pending_bales = false;
    setTimeout(() => {
        render_main_pending_bales_list(frm);
    }, 300);
    if (!frm.doc.bale_registration_code) {
        frm.bale_registration_barcodes = [];  // Clear any old data

        return;
    }
       
    const r = await frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Bale Registration',
            name: frm.doc.bale_registration_code
        },
    });

    if (r.message) {
        const details = r.message.bale_registration_detail || [];
        // Extract bale barcodes and store them in a custom property on the form
        frm.bale_registration_barcodes = details
            .map(row => row.bale_barcode)
            .filter(barcode => !!barcode);  // Filter out any empty/null values


    } else {
        frm.bale_registration_barcodes = [];
        frappe.msgprint(__('⚠️ No details found for this Bale Registration.'));
    }

}

async function render_main_pending_bales_list(frm) {
    if (is_rendering_main_pending_bales) return;
    is_rendering_main_pending_bales = true;
    const container = frm.fields_dict.pending_bales.$wrapper;
    container.empty();
    
    if (!frm.bale_registration_barcodes || frm.bale_registration_barcodes.length === 0) {
        container.html('<div>No bales available for this lot.</div>');
        return;
    }

    if (frm.bale_registration_barcodes.length === frm.doc.total_bales) return;


    // Header row with two columns: Barcode and Status
const $header = $(`
    <div style="display: flex; font-weight: bold; padding-bottom: 6px; border-bottom: 1px solid #ccc;">
        <div style="flex: 1 1 13ch; min-width: 13ch; font-family: monospace;">Bale Barcode</div>
        <div style="flex: 1 1 10ch; text-align: center;">Grade</div>
        <div style="flex: 0 0 8ch; text-align: center;">Status</div>
    </div>
`);
    container.append($header);
    let already_processed = [];
    already_processed = await already_processed_bale(frm);
    const detail_barcodes = (frm.doc.detail_table || [])
        .map(row => row.bale_barcode)
        .filter(barcode => !!barcode);


    const processed_barcodes = Array.from(new Set([...detail_barcodes, ...already_processed]));

    const pending_barcodes = frm.bale_registration_barcodes.filter(b => !processed_barcodes.includes(b));

const message_label = frm.fields_dict.message_label.$wrapper;
    if (pending_barcodes.length === 1) {
        message_label.text('⚠️ The next bale is the last one for this lot!');
    } else {
        message_label.text('');
    }

const barcodeToGrade = {};
(frm.doc.detail_table || []).forEach(row => {
    if (row.bale_barcode) {
        barcodeToGrade[row.bale_barcode] = row.item_grade || "";
    }
});

for (const barcode of Array.from(new Set(frm.bale_registration_barcodes))) {
    const is_processed = processed_barcodes.includes(barcode);
    const statusText = is_processed ? '✅' : '';
    const statusTextColor = is_processed ? '#155724' : '#856404';

    const grade = barcodeToGrade[barcode] || "-";

    const $barcodeCell = $(`<div style="flex: 1 1 13ch; min-width: 13ch; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-family: monospace; padding: 4px 6px;">${barcode}</div>`);

    const $gradeCell = $(`<div style="flex: 1 1 10ch; text-align: center; font-family: monospace; padding: 4px 6px;">${grade}</div>`);

    const $statusCell = $(`<div style="flex: 0 0 8ch; text-align: center; font-weight: 700; color: ${statusTextColor}; border-radius: 3px; padding: 2px 4px; user-select: none; margin-left: 6px;">${statusText}</div>`);

    const $row = $('<div style="display: flex; align-items: center; margin: 2px 0;"></div>');
    $row.append($barcodeCell, $gradeCell, $statusCell);

    if (!is_processed) {
        $row.css('cursor', 'pointer');
        $row.on('click', () => {
            frm.set_value('bale_barcode', barcode);
            proceedWithBarcodeValidationAndGrade(frm, barcode);
        });
    } else {
        $row.css('cursor', 'default');
    }

    container.append($row);
}

}

function hide_grid_controls(frm) {
    const grid_field = frm.fields_dict.detail_table;
    if (grid_field && grid_field.grid && grid_field.grid.wrapper) {
        grid_field.grid.wrapper
            .find('.grid-add-row,  .btn-open-row')
            .hide();
    }
}
function update_price_grade_labels(d, grade, subgrade, price) {
    d.fields_dict.p_grade_label.$wrapper.find('#grade-label').text(grade || '-');
    d.fields_dict.p_subgrade_label.$wrapper.find('#subgrade-label').text(subgrade || '-');
    d.fields_dict.p_price_label.$wrapper.find('#price-label').text(flt(price || 0).toFixed(2));
}


async function already_processed_bale(frm) {
    const response = await frappe.call({
        method: "leaf_procurement.leaf_procurement.doctype.bale_purchase.bale_purchase.get_purchase_bales",
        args: {
            name: frm.doc.bale_registration_code
        },
    });

    if (response && response.message) {
        return await response.message.filter(barcode => !!barcode) || [];
    }

    return [];
}
