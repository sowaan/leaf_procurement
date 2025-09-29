# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from datetime import datetime
from erpnext.accounts.utils import get_fiscal_year # type: ignore
from frappe import _, ValidationError 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore

class LeafConsumption(Document):
	def autoname(self):
		date_str = str(self.date)  # or date_obj.strftime("%Y-%m-%d")
		today = datetime.strptime(date_str, "%Y-%m-%d")

		#today = datetime.strptime(self.date, "%Y-%m-%d")
		
		fy = get_fiscal_year(today)
		fy_start_year_short = fy[1].strftime("%y")
		fy_end_year_short = fy[2].strftime("%y")
		prefix = f"{self.location_short_code}-{fy_start_year_short}-{fy_end_year_short}-CON-"
		self.name = make_autoname(prefix + ".######")

	def on_submit(self):
		create_stock_entry_from_gtn(self)
	
def create_stock_entry_from_gtn(cons_doc):
    if not cons_doc.location:
        frappe.throw("Please provide Location to move stock.")

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Issue"
    stock_entry.to_warehouse = cons_doc.location

    stock_entry.posting_date = cons_doc.date 
    stock_entry.purpose = "Material Issue"
    stock_entry.set_posting_time = 1
    stock_entry.skip_future_date_validation = True

    for row in cons_doc.bale_registration_detail:

        stock_entry.append("items", {
            "item_code": cons_doc.default_item,
            "qty": row.weight,
            "basic_rate": row.rate,
            # "s_warehouse": cons_doc.location_warehouse,
            "t_warehouse": cons_doc.transit_location,
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
    stock_entry.submit()