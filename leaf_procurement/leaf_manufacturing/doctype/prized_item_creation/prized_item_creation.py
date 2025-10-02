# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe # type: ignore
from frappe.model.document import Document # type: ignore

from erpnext.accounts.utils import get_fiscal_year # type: ignore
from frappe import _, ValidationError 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore

class PrizedItemCreation(Document):
    def autoname(self):
        date_str = str(self.date)  # or date_obj.strftime("%Y-%m-%d")
        today = datetime.strptime(date_str, "%Y-%m-%d")

        #today = datetime.strptime(self.date, "%Y-%m-%d")
        
        fy = get_fiscal_year(today)
        fy_start_year_short = fy[1].strftime("%y")
        fy_end_year_short = fy[2].strftime("%y")
        prefix = f"{self.location_short_code}-{fy_start_year_short}-{fy_end_year_short}-PIC-"
        self.name = make_autoname(prefix + ".######")
            
    # def before_save(self):
    #     self.total_output = "after save"
    #     self.total_output = get_process_order_output(self.process_order)


    def on_submit(self):
        create_stock_entry(self)

@frappe.whitelist()
def get_process_order_output(process_order):
    # Get all Prized Item Creation docs linked to this process_order
    records = frappe.get_all(
        "Prized Item Creation",
        filters={"process_order": process_order, "docstatus": 1},
        fields=["name"]
    )

    total_output = 0

    for rec in records:
        doc = frappe.get_doc("Prized Item Creation", rec.name)
        for row in doc.detail_table:   # assuming child table fieldname = items
            total_output += row.kgs

    return total_output

def create_stock_entry(doc):
    settings = frappe.get_single("Leaf Procurement Settings")
    item =  settings.processed_item

    if not item:
        frappe.throw("Please set Processed Item in Leaf Procurement Settings.")

    if not doc.location:
        frappe.throw("Please provide Location to move stock.")

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Receipt"
    stock_entry.to_warehouse = doc.location

    stock_entry.posting_date = doc.date 
    stock_entry.posting_time = "20:30:00"
    stock_entry.purpose = "Material Receipt"
    stock_entry.set_posting_time = 1
    stock_entry.skip_future_date_validation = True
    stock_entry.custom_receiving_warehouse = doc.location
    for row in doc.detail_table:
                
        stock_entry.append("items", {
            "item_code": item,
            "qty": row.kgs,
            "target_warehouse": doc.location,
            "use_serial_batch_fields": 1,
            "prized_grade": row.prized_grade,
            "process_order": doc.process_order,
            "basic_rate": row.standard_rate,
            "basic_amount": row.amount,
            "custom_packing_quantity": row.quantity,
            "custom_packing_type": row.packing_type,
        })

    stock_entry.insert()
    stock_entry.submit()
