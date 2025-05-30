// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt
let suppress_focus = false;

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
            dialog.hide();
            callback(selected_grade, selected_sub_grade);
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
                if(r.message){

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


frappe.ui.form.on("Bale Purchase", {
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
            fields: [
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'p_bale_registration_code',
                    label: 'Bale BarCode',
                    fieldtype: 'Data',
                    reqd: 1,
                },
                {
                    fieldname: 'p_item_sub_grade',
                    label: 'Item Sub Grade',
                    fieldtype: 'Link',
                    options: 'Item Sub Grade',
                    reqd: 1,
                    read_only:1,                    
                    // change: function () {
                    //     const grade = d.get_value('p_item_grade');
                    //     const sub_grade = d.get_value('p_item_sub_grade');
                    //     if (grade && sub_grade) {
                    //         frappe.call({
                    //             method: "leaf_procurement.leaf_procurement.doctype.item_grade_price.item_grade_price.get_item_grade_price",
                    //             args: {
                    //                 company: frm.doc.company,
                    //                 location_warehouse: frm.doc.location_warehouse,
                    //                 item: frm.doc.item,
                    //                 item_grade: grade,
                    //                 item_sub_grade: sub_grade
                    //             },
                    //             callback: function (r) {
                    //                 if (r.message !== undefined) {
                    //                     d.set_value("p_price", r.message);
                    //                 }
                    //             }
                    //         });

                    //     }
                    // }
                },

                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'p_item_grade',
                    label: 'Item Grade',
                    fieldtype: 'Link',
                    options: 'Item Grade',
                    reqd: 1,
                    read_only:1,
                    // change: function () {
                    //     d.set_value('p_item_sub_grade', null);
                    //     d.fields_dict.p_item_sub_grade.get_query = function () {
                    //         return {
                    //             filters: {
                    //                 item_grade: d.get_value('p_item_grade')
                    //             }
                    //         };
                    //     };
                    //     if (suppress_focus) return;
                    //     setTimeout(() => {
                    //         const $barcode_input = d.fields_dict.p_item_sub_grade.$wrapper.find('input');
                    //         $barcode_input.focus();
                    //     }, 20);
                    // }
                },
                {
                    fieldname: 'p_price',
                    label: 'Price',
                    fieldtype: 'Currency',
                    read_only: 1
                },
                {
                    fieldtype: 'Section Break'
                }
            ],
            primary_action_label: 'Add Item',
            primary_action: function (values) {
                // if (!values.p_weight) {
                //     frappe.msgprint(__('Please capture weight first.'));
                //     return;
                // }
                primary_action_function(frm, d, values);

            }

        });
        d.onhide = function () {
            //console.log('on hide');
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
    
        d.show();

        const $barcode_input = d.fields_dict.p_bale_registration_code.$wrapper.find('input');

$barcode_input.on('keyup', function (e) {
    const barcode = $(this).val();
    const expectedLength = frm.doc.barcode_length || 0;

    if (e.key === 'Enter' || barcode.length === expectedLength) {
        // If bale_registration_code already exists, skip fetching
        if (frm.doc.bale_registration_code) {
            proceedWithBarcodeValidationAndGrade(frm, barcode, d);
        } else {
            // Step 1: Get bale_registration_code using barcode
            frappe.call({
                method: 'leaf_procurement.leaf_procurement.api.bale_purchase_utils.get_bale_registration_code_by_barcode',
                args: { barcode: barcode },
                callback: function (r) {
                    if (r.message) {
                        const registration_code = r.message;

                        // Step 2: Set bale_registration_code and load barcodes
                        frm.set_value('bale_registration_code', registration_code);

                        frappe.call({
                            method: 'frappe.client.get',
                            args: {
                                doctype: 'Bale Registration',
                                name: registration_code
                            },
                            callback: function (res) {
                                if (res.message) {
                                    const details = res.message.bale_registration_detail || [];
                                    frm.bale_registration_barcodes = details
                                        .map(row => row.bale_barcode)
                                        .filter(barcode => !!barcode);

                                    // Step 3: Now validate
                                    proceedWithBarcodeValidationAndGrade(frm, barcode, d);
                                } else {
                                    frappe.msgprint(__('⚠️ No details found for Bale Registration {0}', [registration_code]));
                                }
                            }
                        });

                    } else {
                        frappe.msgprint(__('⚠️ Bale Registration not found for scanned barcode.'));
                        d.set_value('p_bale_registration_code', '');
                        $barcode_input.focus();
                    }
                }
            });
        }
    }
});

    },
bale_registration_code(frm) {
    if (!frm.doc.bale_registration_code) {
        frm.bale_registration_barcodes = [];  // Clear any old data
        return;
    }

    validate_day_status(frm);  // Optional validation if needed

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
}
,       
    refresh: function(frm) {
        hide_grid_controls(frm);
    },
    date: function(frm) {
        validate_day_status(frm);
    },    
    onload: function(frm) {
        //override bale_registration_code query to load 
        //bale registration codes with no purchase record
        frm.set_query('bale_registration_code', function() {
            return {
                query: 'leaf_procurement.leaf_procurement.api.bale_purchase_utils.get_available_bale_registrations'
            };
        });
        
        // Set query filter for 'item_sub_grade' field in child table
        frm.fields_dict['detail_table'].grid.get_field('item_sub_grade').get_query = function(doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            return {
                filters: {
                    item_grade: child.item_grade
                }
            };
        };

        if (!frm.is_new) return;
    
        //get company and location records from settings
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Leaf Procurement Settings',
                name: 'Leaf Procurement Settings'
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('company', r.message.company_name);
                    frm.set_value('location_warehouse', r.message.location_warehouse);    
                    frm.set_value('item', r.message.default_item);    
                    frm.set_value('barcode_length',r.message.barcode_length)                
                }
            }
        });            
    }        
});
function proceedWithBarcodeValidationAndGrade(frm, barcode, d) {
    const validBarcodes = frm.bale_registration_barcodes || [];

    if (!validBarcodes.includes(barcode)) {
        frappe.msgprint(__('❌ Invalid Bale Barcode: {0}', [barcode]));
        d.set_value('p_bale_registration_code', '');
         $barcode_input.focus();
        return;
    }

    const already_scanned = (frm.doc.detail_table || []).some(row => row.bale_barcode === barcode);
    if (already_scanned) {
        frappe.msgprint(__('⚠️ This Bale Barcode is already scanned: {0}', [barcode]));
        d.set_value('p_bale_registration_code', '');
        updateWeightDisplay("0.00");
        $barcode_input.focus();
        return;
    }

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
                    setTimeout(() => {
                        primary_action_function(frm,d,d.get_values());
                    }, 100);                    
                    
                    
                }
            }

            
            
        });
    });
}

frappe.ui.form.on("Bale Purchase Detail", {
    delete_row(frm, cdt, cdn) {
        frappe.model.clear_doc(cdt, cdn);  // delete the row
        frm.refresh_field('detail_table');

            if (cur_dialog) {
                cur_dialog.hide();
            }

            // Remove any lingering modal backdrop
            $('.modal-backdrop').remove();        
    },    
    refresh: function(frm){
        hide_grid_controls(frm);
    },
    item_grade(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, 'item_sub_grade', '');
    },
    item_sub_grade: function(frm, cdt, cdn) {
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
                callback: function(r) {
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
        callback: function(r) {
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

function primary_action_function(frm,d,values)
{
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

function hide_grid_controls(frm) {
    const grid_field = frm.fields_dict.detail_table;
    if (grid_field && grid_field.grid && grid_field.grid.wrapper) {
        grid_field.grid.wrapper
            .find('.grid-add-row,  .btn-open-row')
            .hide();
    }
}