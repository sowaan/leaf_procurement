# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from datetime import datetime
from erpnext.accounts.utils import get_fiscal_year # type: ignore
from frappe import _, ValidationError 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore
from leaf_procurement.leaf_manufacturing.utils.barcode_utils import get_invoice_item_by_barcode
from frappe.utils import flt
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
		create_stock_entry(self)
	
def create_stock_entry(cons_doc):

    if not cons_doc.location:
        frappe.throw("Please provide Location to move stock.")

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Issue"
    stock_entry.to_warehouse = cons_doc.location

    stock_entry.posting_date = cons_doc.date 
    stock_entry.posting_time = "20:00:00"
    stock_entry.purpose = "Material Issue"
    stock_entry.set_posting_time = 1
    stock_entry.skip_future_date_validation = True
    stock_entry.custom_receiving_warehouse = cons_doc.location
    for row in cons_doc.consumption_detail:
        
        warehouse = get_current_batch_location(row.bale_barcode)
        if not warehouse:
            frappe.throw(f"Batch {row.bale_barcode} not found in any warehouse")

        details = get_invoice_item_by_barcode(cons_doc.item, row.bale_barcode)
        if not details:
            frappe.throw(f"Batch {row.bale_barcode} not found in any Purchase Invoice for item {cons_doc.item}")
        
        rate = details.get("rate")
        lot_number = details.get("lot_number")
        grade = details.get("grade")
        sub_grade = details.get("sub_grade")
        reclassification_grade = details.get("reclassification_grade")
        invoice_qty = details.get("qty")

        precision = 3  # or use frappe.db.get_default("float_precision")
        if flt(row.purchase_weight, precision) != flt(invoice_qty, precision):
            frappe.throw(
                f"Quantity mismatch for Batch {row.bale_barcode}. "
                f"Expected: {flt(invoice_qty, precision)}, Found: {flt(row.purchase_weight, precision)}"
            )
        if reclassification_grade and reclassification_grade!=row.internal_grade:
            frappe.throw(f"Reclassification Grade mismatch for Batch {row.bale_barcode}. Expected: {reclassification_grade}, Found: {row.internal_grade}")

        stock_entry.append("items", {
            "item_code": cons_doc.item,
            "qty": row.purchase_weight,
            "s_warehouse": warehouse,

            "use_serial_batch_fields": 1,
            "batch_no": row.bale_barcode,
            "reclassification_grade": row.internal_grade,
            "process_order": cons_doc.process_order,
            "lot_number": lot_number,
            "grade": grade,
            "sub_grade": sub_grade,
            "to_lot_number": lot_number,
            "to_grade": grade,
            "to_sub_grade": sub_grade,
            "basic_rate": rate,
            "basic_amount": rate * invoice_qty
		})

    stock_entry.insert()
    stock_entry.submit()



def get_current_batch_location(batch_no: str) -> str | None:
    """
    Get the current warehouse (location) of a given batch_no.
    Returns the warehouse name or None if not found.
    """
    if not batch_no:
        frappe.throw("Batch No is required")

    result = frappe.db.sql("""
        SELECT sb.warehouse
        FROM `tabSerial and Batch Bundle` sb
        INNER JOIN `tabSerial and Batch Entry` sbe
            ON sbe.parent = sb.name
        WHERE sbe.batch_no = %s
          AND sb.docstatus = 1 AND sbe.is_outward = 0
        ORDER BY sb.posting_date DESC, sb.posting_time DESC, sb.modified DESC
        LIMIT 1
    """, (batch_no,), as_dict=True)

    if result:
        return result[0].warehouse
    return None
