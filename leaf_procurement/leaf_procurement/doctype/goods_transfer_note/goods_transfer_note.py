# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore



class GoodsTransferNote(Document):
	def on_submit(self):
		create_stock_entry_from_gtn(self)
    # def on_update(self):
    #     create_stock_entry_from_gtn(self)
        
def create_stock_entry_from_gtn(gtn_doc):
    if not gtn_doc.location_warehouse or not gtn_doc.receiving_location:
        frappe.throw("Dispatch and Receiving Warehouse must be set.")

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"
    stock_entry.company = gtn_doc.company
    stock_entry.add_to_transit = True
    stock_entry.from_warehouse = gtn_doc.location_warehouse
    stock_entry.to_warehouse = gtn_doc.transit_location
    stock_entry.custom_receiving_warehouse = gtn_doc.receiving_location

    stock_entry.purpose = "Material Transfer"
    stock_entry.custom_gtn_number = gtn_doc.name  # custom field if needed

    for row in gtn_doc.bale_registration_detail:

        stock_entry.append("items", {
            "item_code": gtn_doc.default_item,
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
		})

    stock_entry.insert()
    #stock_entry.submit()


