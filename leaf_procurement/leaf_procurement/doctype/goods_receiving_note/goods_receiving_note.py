# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore

class GoodsReceivingNote(Document):
    def on_submit(self):
        create_stock_entry_from_gtn(self)

        
def create_stock_entry_from_gtn(grn_doc):
    if not grn_doc.location_warehouse or not grn_doc.transit_location:
        frappe.throw("Dispatch and Receiving Warehouse must be set.")

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"
    stock_entry.company = grn_doc.company
    stock_entry.add_to_transit = False
    stock_entry.to_warehouse = grn_doc.location_warehouse
    stock_entry.from_warehouse = grn_doc.transit_location
    stock_entry.custom_receiving_warehouse = grn_doc.dispatch_location

    stock_entry.purpose = "Material Transfer"
    stock_entry.custom_gtn_number = grn_doc.name  # custom field if needed

    for row in grn_doc.detail_table:
        item = {
            "item_code": grn_doc.default_item,
            "qty": row.weight,
            "basic_rate": row.rate,
            # "s_warehouse": gtn_doc.location_warehouse,
            # "t_warehouse": gtn_doc.receiving_location,
            "use_serial_batch_fields": 1,
            "batch_no": row.bale_barcode,
			"lot_number": row.lot_number,
			"grade": row.item_grade,
			"sub_grade": row.item_sub_grade,            
			"to_lot_number": row.lot_number,
			"to_grade": row.item_grade,
			"to_sub_grade": row.item_sub_grade,   
            "doctype": "Stock Entry Detail",
            "parentfield": "items",
            "parenttype": "Stock Entry"
		}
        stock_entry.append("items", item)
    stock_entry.flags.ignore_mandatory = True
    stock_entry.insert()
    #stock_entry.submit()
