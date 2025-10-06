# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe # type: ignore
from frappe.model.document import Document # type: ignore

from erpnext.accounts.utils import get_fiscal_year # type: ignore
from frappe import _, ValidationError 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore

class TobaccoShipment(Document):
    def autoname(self):
        date_str = str(self.date)  # or date_obj.strftime("%Y-%m-%d")
        today = datetime.strptime(date_str, "%Y-%m-%d")

        #today = datetime.strptime(self.date, "%Y-%m-%d")
        
        fy = get_fiscal_year(today)
        fy_start_year_short = fy[1].strftime("%y")
        fy_end_year_short = fy[2].strftime("%y")
        prefix = f"{self.location_from_short_code}-{fy_start_year_short}-{fy_end_year_short}-TSP-"
        self.name = make_autoname(prefix + ".######")

    def on_submit(self):
        create_stock_entry(self)
        
def create_stock_entry(doc):
    settings = frappe.get_single("Leaf Procurement Settings")
    item =  settings.processed_item

    if not item:
        frappe.throw("Please set Processed Item in Leaf Procurement Settings.")

    if not doc.location_from or not doc.location_to:
        frappe.throw("Please provide From and To Locations to move stock.")

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"
    stock_entry.from_warehouse = doc.location_from
    stock_entry.to_warehouse = doc.location_to

    stock_entry.posting_date = doc.date 
    stock_entry.posting_time = "20:40:00"
    stock_entry.purpose = "Material Transfer"
    stock_entry.set_posting_time = 1
    stock_entry.skip_future_date_validation = True
    stock_entry.remarks = "TSA No:" + doc.tsa_number
    for row in doc.detail_table:
                
        stock_entry.append("items", {
            "item_code": item,
            "qty": row.kgs,
            "use_serial_batch_fields": 1,
            "prized_grade": row.prized_grade,
            "basic_rate": row.standard_rate,
            "valuation_rate": row.standard_rate,
            "basic_amount": row.amount,
            "custom_packing_quantity": row.quantity,
            "custom_packing_type": row.packing_type,
            "uom": "Kg",
            "conversion_factor": 1,
        })

    # ✅ Save as draft first — so ERPNext processes the valuation properly
    stock_entry.insert(ignore_permissions=True)

    # ✅ Submit (GL entries will now be created)
    stock_entry.submit()

