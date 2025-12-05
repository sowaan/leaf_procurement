# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe 	#type: ignore
from frappe.model.document import Document 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore
from erpnext.accounts.utils import get_fiscal_year # type: ignore
from datetime import datetime
from frappe import _, ValidationError 	#type: ignore
from leaf_procurement.leaf_procurement.api.config import get_cached_prefix
import re

class BaleCreation(Document):
    def autoname(self):
        if not self.location_shortcode:
            frappe.throw(_("Location Shortcode is required to generate name"))

        # Ensure self.date exists
        if not self.date:
            frappe.throw("Date is required for generating name")

        # Format date
        doc_date = datetime.strptime(str(self.date), "%Y-%m-%d")
        date_part = doc_date.strftime("%Y%m%d")

        # Build prefix
        prefix = f"{self.location_shortcode}-CB-{date_part}-"


        # Normal autoname
        self.name = make_autoname(prefix + ".######")
        # self._update_series_from_name()

    def validate(self):
        settings = frappe.get_single("Leaf Procurement Settings")
        item =  settings.default_item
        existing_batches = []
        invalid_batches = []

        for row in self.detail_table:
            barcode = row.bale_barcode.strip()

            if batch_exists(barcode, item):
                existing_batches.append(barcode)         

            # Pattern: 1 letter + 10 digits
            pattern = r'^[A-Za-z][0-9]{10}$'

            if not re.match(pattern, barcode):
                invalid_batches.append(barcode)

        if existing_batches:
            frappe.throw(_("⚠️ The following bale barcodes already exist as batches:<br><br>{0}")
                .format("<br>".join(existing_batches)))

        if invalid_batches:
            frappe.throw(_("⚠️ The following bale barcodes are invalid (barcode must start with alphabet and should contain 10 digits):<br><br>{0}")
                .format("<br>".join(invalid_batches)))
            
    def on_submit(self):
        settings = frappe.get_single("Leaf Procurement Settings")
        item =  settings.default_item
        existing_batches = []
        invalid_batches = []

        for row in self.detail_table:
            barcode = row.bale_barcode.strip()

            if batch_exists(barcode, item):
                existing_batches.append(barcode)         

            # Pattern: 1 letter + 11 digits
            pattern = r'^[A-Za-z][0-9]{10}$'

            if not re.match(pattern, barcode):
                invalid_batches.append(barcode)

        if existing_batches:
            frappe.throw(_("⚠️ The following bale barcodes already exist as batches:<br><br>{0}")
                .format("<br>".join(existing_batches)))

        if invalid_batches:
            frappe.throw(_("⚠️ The following bale barcodes are invalid (barcode must start with alphabet and should contain 10 digits):<br><br>{0}")
                .format("<br>".join(invalid_batches)))
        
        create_stock_entry(self, item)

def batch_exists(batch_no: str, item_code: str) -> bool:
    """
    Ensures that a Batch record exists for the given barcode and item.
    Creates one if it does not exist.

    Args:
        batch_no (str): The barcode (Batch ID).
        item_code (str): The item code.
        batch_qty (float): The quantity associated with the batch.
    """
    if frappe.db.exists("Batch", {"batch_id": batch_no, "item": item_code}):
        return True
    else:
        return False
    

def create_stock_entry(doc, item):
    if not item:
        frappe.throw("Please set Item in Leaf Procurement Settings.")

    if not doc.location:
        frappe.throw("Please provide Location to create stock.")

    
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Receipt"
    stock_entry.to_warehouse = doc.location

    stock_entry.posting_date = doc.date 
    stock_entry.posting_time = "18:30:00"
    stock_entry.purpose = "Material Receipt"
    stock_entry.set_posting_time = 1
    stock_entry.skip_future_date_validation = True
    stock_entry.custom_receiving_warehouse = doc.location
    for row in doc.detail_table:
        ensure_batch_exists(row.bale_barcode, item, row.weight)        
        stock_entry.append("items", {
            "item_code": item,
            "qty": row.weight,
            "target_warehouse": doc.location,
            "use_serial_batch_fields": 1,
            "grade": row.item_grade,
            "sub_grade": row.item_sub_grade,
            "reclassification_grade": row.reclassification_grade,
            "batch_no": row.bale_barcode,
            "basic_rate": row.rate,
            "uom": "Kg",
            "conversion_factor": 1,
        })

    # ✅ Must call these controller methods BEFORE insert/submit
    stock_entry.set_missing_values()
    stock_entry.calculate_rate_and_amount()

    # ✅ Save as draft first — so ERPNext processes the valuation properly
    stock_entry.save(ignore_permissions=True)

    # ✅ Now reload (to simulate UI reload)
    stock_entry.reload()

    # ✅ Submit (GL entries will now be created)
    stock_entry.submit()

    frappe.db.commit()

def ensure_batch_exists(batch_no: str, item_code: str, batch_qty: float) -> None:
    """
    Ensures that a Batch record exists for the given barcode and item.
    Creates one if it does not exist.

    Args:
        batch_no (str): The barcode (Batch ID).
        item_code (str): The item code.
        batch_qty (float): The quantity associated with the batch.
    """
    if not frappe.db.exists("Batch", {"batch_id": batch_no, "item": item_code}):
        # Create new batch if it doesn't exist  
        batch = frappe.new_doc("Batch")
        batch.batch_id = batch_no
        batch.item = item_code
        batch.batch_qty = batch_qty
        batch.save()
        print("Batch:", batch_no, item_code, batch_qty)
    else:
        # Update existing batch quantity
        batch = frappe.get_doc("Batch", {"batch_id": batch_no, "item": item_code})
        batch.batch_qty = batch_qty  # Add to existing quantity
        batch.save()