// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Goods Transfer Note", {
	refresh(frm) {

	},
    scan_barcode: function(frm) {
        let barcode = frm.doc.scan_barcode;
        let itemcode = frm.doc.default_item
        let expected_length = parseInt(frm.doc.barcode_length);

        // Ensure barcode is present
        if (!barcode) return;

        // Check if the barcode is numeric
        if (!/^\d+$/.test(barcode)) {
            frappe.msgprint(__('Barcode must be numeric.'));
            frm.set_value('scan_barcode', '');
            return;
        }

        // Check length
        if (expected_length && barcode.length !== expected_length) {
            //frappe.msgprint(__('Barcode must be exactly {0} digits.', [expected_length]));
            return;
        }

    // Check if barcode already exists in child table
        let exists_in_grid = frm.doc.bale_registration_detail.some(row => row.bale_barcode === barcode);
        if (exists_in_grid) {
            frappe.msgprint(__('This barcode already exists in the grid.'));
            frm.set_value('scan_barcode', '');
            return;
        }

        // Now check if barcode already exists in Batch table (invoice generated)
        frappe.call({
            method: 'leaf_procurement.leaf_procurement.api.barcode.get_invoice_item_by_barcode',
            args: { itemcode: itemcode, barcode: barcode },
            callback: function(r) {
                if (r.message && r.message.exists ) {
                    let row = frm.add_child('bale_registration_detail', {
                        bale_barcode: barcode,
                        weight: r.message.qty,
                        rate: r.message.rate,
                        lot_number: r.message.lot_number,
                        item_grade: r.message.grade,
                        item_sub_grade: r.message.sub_grade
                    });
                    frm.refresh_field('bale_registration_detail');
                } else {
                    frappe.msgprint(__('This barcode has not been invoiced or has been rejected during invoice generation.'));
                }

                frm.set_value('scan_barcode', '');
            }
        });
    },        
    onload(frm) {
        // Disable click on grid rows to prevent popup
        const grid = frm.fields_dict.detail_table?.grid;
        if (grid && grid.wrapper) {
            grid.wrapper.on('click', '.grid-row', function (e) {
                e.stopPropagation();
                e.preventDefault();
            });
        }
        
        if (!frm.is_new()) return;

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
                    frm.set_value('barcode_length', r.message.barcode_length);
                    frm.set_value('default_item', r.message.default_item);
                }   
            }
        });                
    },
    company(frm) {
        frm.set_value('receiving_location', null);  // Clear field
        frm.set_query('receiving_location', () => {
            return {
                filters: {
                    company: frm.doc.company
                }
            };
        });
    }    
});
