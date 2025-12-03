# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from frappe.model.naming import make_autoname # type: ignore
from erpnext.stock.doctype.batch.batch import get_batch_qty # type: ignore
from frappe import _
from typing import List, Dict, Any

class GoodsReceivingNote(Document):
    def autoname(self):
        """Override the default method to set a custom name."""
        if getattr(self, "skip_autoname", False):
            # print("Skipping autoname for CustomSupplier", self.servername)
            self.name = self.servername
            return  
        
        from datetime import datetime

        year = datetime.today().strftime('%Y') 
        
        # settings = frappe.get_doc("Leaf Procurement Settings")
        # self.location_short_code = frappe.db.get_value(
        #     "Warehouse",
        #     #settings.get("location_warehouse"),
        #     self.location_warehouse,
        #     "custom_short_code"
        # )
        prefix = f"{self.location_shortcode or 'SAM'}-GRN-{year}-"

        self.name = make_autoname(prefix + ".######")
# inside leaf_consumption.py (DocType class methods)

    def before_submit(self):
        """
        Called before the document is submitted. We populate the bad_items child table
        with rows returned from the SE creation helper, so they are saved as part of submit.
        """
        try:
            result = create_stock_entry_from_gtn_auto_submit(self)
        except Exception as e:
            # In case the helper raises for unexpected reasons, log and re-raise to block submit
            frappe.log_error(title=f"create_stock_entry error for {self.name}", message=frappe.get_traceback())
            raise

        bad_items = result.get("bad_items", []) or []
        stock_entry_name = result.get("stock_entry")

        # Replace in-memory bad_items child table (so it will be saved as part of submit)
        # Use the correct child table field name on your GRN doctype (replace 'bad_items' if different)
        self.set("bad_items", [])  # clear existing
        for b in bad_items:
            # map keys to your child table fieldnames; adjust if necessary
            self.append("bad_items", {
                "batch_no": b.get("batch_no"),
                "item_code": b.get("item_code"),
                "found_qty": b.get("available_qty"),
                "expected_qty": b.get("requested_qty"),
                "reason": b.get("reason")
            })

        # Optionally set a field on parent to link the created stock entry
        if stock_entry_name:
            # keep a reference field like `created_stock_entry` on your GRN or use a custom field
            self.db_set("created_stock_entry", stock_entry_name)
            # Alternatively set in-memory so it gets saved on submit:
            # self.created_stock_entry = stock_entry_name

        # Do NOT call save() here — this is inside before_submit; the submit flow will persist these changes.

    def on_submit(self):
        # Do not modify child tables here.
        # If you want to inform the user, just show a message
        created_se = getattr(self, "created_stock_entry", None)
        if created_se:
            frappe.msgprint(_("Stock Entry {0} created successfully.").format(created_se))
        # maybe also show how many bad items:
        bad_count = len(self.get("bad_items") or [])
        if bad_count:
            frappe.msgprint(_("There are {0} bad item(s) recorded in the Bad Items table.").format(bad_count))

        

def get_warehouse_qty(item_code: str, warehouse: str, batch_no: str = None) -> float:
    """
    Return available qty for item in a warehouse.
    - Prefer Bin.actual_qty when available (fast).
    - If batch_no provided, try to sum Stock Ledger Entry for that batch/warehouse as fallback.
    Returns float (0.0 if nothing found).
    """
    try:
        if not item_code or not warehouse:
            return 0.0

        # Try Bin table (fast, recommended)
        qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty")
        if qty is not None:
            return float(qty or 0.0)

        # If batch_no is provided, try to sum actual_qty from Stock Ledger Entry for that batch + warehouse
        if batch_no:
            sle_sum = frappe.db.sql(
                """SELECT COALESCE(SUM(actual_qty), 0)
                   FROM `tabStock Ledger Entry`
                   WHERE batch_no = %s AND warehouse = %s AND is_cancelled = 0""",
                (batch_no, warehouse),
            )
            if sle_sum:
                return float(sle_sum[0][0] or 0.0)

        # Final fallback: try total across warehouses (without batch)
        total = frappe.db.sql(
            """SELECT COALESCE(SUM(actual_qty), 0)
               FROM `tabStock Ledger Entry`
               WHERE item_code = %s AND warehouse = %s AND is_cancelled = 0""",
            (item_code, warehouse),
        )
        if total:
            return float(total[0][0] or 0.0)

    except Exception as e:
        # don't break flow on helper errors; log for debugging
        frappe.log_error(title="get_warehouse_qty error", message=frappe.get_traceback())

    return 0.0


def create_stock_entry_from_gtn_auto_submit(grn_doc):
    """
    Returns {"stock_entry": <name or None>, "bad_items": [ {batch_no, item_code, available_qty, requested_qty, reason}, ... ]}
    Does NOT raise on bad items; auto-submits only valid rows.
    """
    # Preconditions
    if not getattr(grn_doc, "location_warehouse", None) or not getattr(grn_doc, "transit_location", None):
        # Let calling code handle this; raise here if you prefer.
        frappe.throw(_("Dispatch and Receiving Warehouse must be set."))

    # Create SE doc
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Transfer"
    se.company = grn_doc.company
    se.add_to_transit = getattr(grn_doc, "add_to_transit", False) or False
    se.to_warehouse = grn_doc.location_warehouse
    # custom refs if used
    se.custom_gtn_number = grn_doc.name
    se.custom_reference_doctype = "Goods Receiving Note"
    se.custom_reference_name = grn_doc.name

    bad_items = []
    appended_any = False

    for row in getattr(grn_doc, "detail_table", []):
        item_code = grn_doc.default_item
        requested_qty = float(getattr(row, "weight", 0) or 0)

        # Determine source warehouse & available qty.
        # Replace get_batch_qty / get_warehouse_qty with your implementations.
        batch_info = None
        try:
            batch_info = get_batch_qty(batch_no=row.bale_barcode, item_code=item_code)
        except Exception:
            batch_info = None

        source_warehouse = grn_doc.transit_location  # fallback
        available_qty = 0.0

        if batch_info:
            info = batch_info[0] if isinstance(batch_info, (list, tuple)) and batch_info else batch_info
            # try to read warehouse and qty from info
            if isinstance(info, dict):
                source_warehouse = info.get("warehouse") or source_warehouse
                available_qty = float(info.get("available_qty") or info.get("qty") or 0.0)
            else:
                # unknown shape fallback to checking bin
                available_qty = get_warehouse_qty(item_code=item_code, warehouse=source_warehouse, batch_no=row.bale_barcode)
        else:
            available_qty = get_warehouse_qty(item_code=item_code, warehouse=grn_doc.transit_location, batch_no=row.bale_barcode)

        # IMPORTANT: treat negative available_qty as zero — do not append negative values
        if available_qty < 0:
            available_qty = 0.0

        if available_qty < requested_qty:
            bad_items.append({
                "batch_no": row.bale_barcode,
                "item_code": item_code,
                "available_qty": available_qty,
                "requested_qty": requested_qty,
                "reason": _("Insufficient stock in source warehouse")
            })
            # log for ops
            frappe.log_error(
                title=f"Insufficient qty for bale {row.bale_barcode}",
                message=f"GRN: {grn_doc.name}, Item: {item_code}, available: {available_qty}, requested: {requested_qty}, src_warehouse: {source_warehouse}"
            )
            continue

        # append valid item
        se.append("items", {
            "item_code": item_code,
            "qty": requested_qty,
            "basic_rate": getattr(row, "rate", 0) or 0,
            "s_warehouse": source_warehouse or grn_doc.transit_location,
            "t_warehouse": grn_doc.location_warehouse,
            "use_serial_batch_fields": 1,
            "batch_no": row.bale_barcode,
            "lot_number": getattr(row, "lot_number", None),
            "grade": getattr(row, "item_grade", None),
            "sub_grade": getattr(row, "item_sub_grade", None),
            "to_lot_number": getattr(row, "lot_number", None),
            "to_grade": getattr(row, "item_grade", None),
            "to_sub_grade": getattr(row, "item_sub_grade", None),
            "reclassification_grade": getattr(row, "reclassification_grade", None)
        })
        appended_any = True

    result = {"stock_entry": None, "bad_items": bad_items}

    if not appended_any:
        # nothing to submit — return bad_items; caller will persist bad_items into the GRN child table
        return result

    # Try to save & submit the SE with only valid items
    try:
        se.flags.ignore_mandatory = True
        se.save(ignore_permissions=True)
        se.reload()
        se.submit()
        result["stock_entry"] = se.name
        return result
    except Exception as exc:
        # If submit fails due to insufficient stock (possible if inventory changed between check and submit),
        # capture the error into bad_items and return rather than throwing
        err_text = str(exc)
        frappe.log_error(title="Error Creating/Submitting Stock Entry", message=f"Error submitting Stock Entry for GRN {grn_doc.name}: {err_text}\n{frappe.get_traceback()}")
        # if "needed in Warehouse" in err_text or "Insufficient" in err_text or "not enough" in err_text:
        #     bad_items.append({
        #         "batch_no": None,
        #         "item_code": None,
        #         "available_qty": None,
        #         "requested_qty": None,
        #         "reason": _("Submission failed due to insufficient stock: {0}").format(err_text)
        #     })
        result["bad_items"] = bad_items
        return result
        # re-raise for unexpected errors

