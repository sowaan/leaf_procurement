# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from datetime import datetime
from erpnext.accounts.utils import get_fiscal_year # type: ignore
from frappe import _, ValidationError 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore
from leaf_procurement.leaf_manufacturing.utils.barcode_utils import get_invoice_item_by_barcode
from frappe.utils import flt # type: ignore
from erpnext.stock.doctype.batch.batch import get_batch_qty # type: ignore



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

    def before_submit(self):
        """
        Create Stock Entry for valid rows, collect bad_items and attach them to the doc
        BEFORE submit so updates are persisted as part of the submit transaction.
        """
        try:
            result = create_stock_entry(self)
        except Exception as e:
            # if helper raises, block submit with a clear message (optional)
            frappe.log_error(title=f"create_stock_entry error for {self.name}", message=frappe.get_traceback())
            frappe.throw(_("Error creating Stock Entry: {0}").format(str(e)))

        bad_items = result.get("bad_items", []) or []
        stock_entry_name = result.get("stock_entry")

        # replace in-memory bad_items so they persist on submit
        self.set("bad_items", [])
        for b in bad_items:
            self.append("bad_items", {
                "batch_no": b.get("batch_no"),
                "item_code": b.get("item_code"),
                "reason": b.get("reason"),
                "expected_qty": b.get("expected_qty"),
                "found_qty": b.get("found_qty"),
                "detailed_reason": b.get("detailed_reason")
            })

        # store the created stock entry reference on a field (create created_stock_entry in doctype)
        # If you don't have a field, you can create one (Data) or skip this line.
        if stock_entry_name:
            # set in-memory so it persists on submit
            self.created_stock_entry = stock_entry_name

    def on_submit(self):
        # do not change child tables here
        created_se = getattr(self, "created_stock_entry", None)
        bad_count = len(self.get("bad_items") or [])
        if created_se:
            frappe.msgprint(_("Stock Entry {0} created successfully.").format(created_se))
        if bad_count:
            # build short summary for UI
            summary = []
            for b in (self.get("bad_items") or [])[:10]:
                summary.append(f"{b.get('batch_no')}: {b.get('reason')}")
            frappe.msgprint(_("Some bales were skipped and recorded in Bad Items:\n{0}").format("\n".join(summary)))

def get_warehouse_qty(item_code, warehouse, batch_no=None) -> float:
    """
    Fast helper: try Bin.actual_qty then fallback to Stock Ledger queries.
    Returns non-negative float.
    """
    try:
        if not item_code or not warehouse:
            return 0.0
        qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty")
        if qty is not None:
            return float(qty or 0.0)
        # fallback to SLE sums (batch-aware)
        if batch_no:
            s = frappe.db.sql("""SELECT COALESCE(SUM(actual_qty),0) FROM `tabStock Ledger Entry`
                                 WHERE batch_no=%s AND warehouse=%s AND is_cancelled=0""",
                               (batch_no, warehouse))
            if s:
                return float(s[0][0] or 0.0)
        # final fallback: SLE by item+warehouse
        s = frappe.db.sql("""SELECT COALESCE(SUM(actual_qty),0) FROM `tabStock Ledger Entry`
                             WHERE item_code=%s AND warehouse=%s AND is_cancelled=0""",
                           (item_code, warehouse))
        if s:
            return float(s[0][0] or 0.0)
    except Exception:
        frappe.log_error(title="get_warehouse_qty error", message=frappe.get_traceback())
    return 0.0


def create_stock_entry(cons_doc):
    """
    Validate batches and create a Material Issue Stock Entry for valid rows.
    Returns {"stock_entry": <name_or_None>, "bad_items": [ ... ]}.
    Does NOT persist bad_items into cons_doc (caller will set them).
    """
    if not cons_doc.location:
        frappe.throw(_("Please provide Location to move stock."))

    bad_items = []
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Issue"
    stock_entry.custom_reference_doctype = "Leaf Consumption"
    stock_entry.custom_reference_name = cons_doc.name

    # tolerance for float comparison (kg precision)
    tol = 0.001

    for row in cons_doc.consumption_detail:
        try:
            bale = row.bale_barcode
            expected_qty = flt(row.purchase_weight, 3)
            # 1) Already issued?
            sename = already_issued(bale, cons_doc.item)
            if sename:
                bad_items.append({
                    "batch_no": bale,
                    "reason": "Already Issued",
                    "expected_qty": expected_qty,
                    "found_qty": 0,
                    "item_code": cons_doc.item,
                    "detailed_reason": f"Already issued in Stock Entry {sename}"
                })
                continue

            # 2) Batch info
            batch_info = get_batch_qty(batch_no=bale, item_code=cons_doc.item)
            info = batch_info[0] if batch_info else None
            if not info:

                # batch not found at all
                bad_items.append({
                    "batch_no": bale,
                    "reason": "Batch Not Found",
                    "expected_qty": expected_qty,
                    "found_qty": 0,
                    "item_code": cons_doc.item,
                    "detailed_reason": "No batch information found in the system."
                })
                continue

            warehouse = info.get("warehouse")
            found_qty = flt(info.get("qty") or info.get("available_qty") or 0.0, 3)

            # treat negative found as zero (avoid negative confusion)
            if found_qty < 0:
                found_qty = 0.0

            # 3) Qty mismatch tolerance
            if abs(found_qty - expected_qty) > tol:
                bad_items.append({
                    "batch_no": bale,
                    "reason": "Quantity Mismatch",
                    "expected_qty": expected_qty,
                    "found_qty": found_qty,
                    "item_code": cons_doc.item,
                    "detailed_reason": f"Expected {expected_qty}, but found {found_qty} in batch."
                })
                continue

            # 4) invoice details
            details = get_invoice_item_by_barcode(cons_doc.item, bale)
            if not details:
                bad_items.append({
                    "batch_no": bale,
                    "reason": "Invoice Not Found",
                    "expected_qty": expected_qty,
                    "found_qty": found_qty,
                    "item_code": cons_doc.item,
                    "detailed_reason": "No matching invoice details found for this barcode."
                })
                continue

            rate = details.get("rate") or 0.0
            lot_number = details.get("lot_number")
            grade = details.get("grade")
            sub_grade = details.get("sub_grade")
            invoice_qty = details.get("qty") or expected_qty

            # Append valid row to stock entry (Material Issue: s_warehouse should be batch location)
            stock_entry.append("items", {
                "item_code": cons_doc.item,
                "qty": expected_qty,
                "s_warehouse": warehouse,
                "uom": "Kg",
                "stock_uom": "Kg",
                "conversion_factor": 1,
                "batch_no": bale,
                "use_serial_batch_fields": 1,
                "reclassification_grade": row.internal_grade,
                "process_order": cons_doc.process_order,
                "lot_number": lot_number,
                "grade": grade,
                "sub_grade": sub_grade,
                "basic_rate": rate,
                "basic_amount": rate * invoice_qty
            })
        except Exception as ex:
            frappe.log_error(title="Error Creating Stock Entry For POS", message=frappe.get_traceback())
            bad_items.append({
                "batch_no": getattr(row, "bale_barcode", None),
                "item_code": cons_doc.item,
                "reason": "Unexpected error",
                "expected_qty": getattr(row, "purchase_weight", 0),
                "found_qty": 0,
                "detailed_reason": str(ex)
            })
            continue

    # Do NOT save cons_doc here. Caller will persist bad_items as part of submit (before_submit).
    # If you previously called cons_doc.save() here, remove that.

    # If no valid items
    if not stock_entry.items:
        return {"stock_entry": None, "bad_items": bad_items}

    # # Prepare SE, revalidate before submit (minimize race)
    # stock_entry.set_missing_values()
    # stock_entry.calculate_rate_and_amount()

    # # Re-check availability for each item before submit. Remove items that are now insufficient.
    # items_to_remove = []
    # for idx, it in enumerate(stock_entry.items):
    #     avail = get_warehouse_qty(item_code=it.item_code, warehouse=it.s_warehouse, batch_no=it.batch_no)
    #     if avail < flt(it.qty, 3) - tol:
    #         # record as bad and mark to remove
    #         bad_items.append({
    #             "batch_no": it.batch_no,
    #             "item_code": it.item_code,
    #             "expected_qty": it.qty,
    #             "found_qty": avail,
    #             "reason": "Insufficient stock at submit time",
    #             "detailed_reason": f"Available {avail}, required {it.qty}"
    #         })
    #         items_to_remove.append(idx)

    # # remove from the end to maintain indices
    # for i in reversed(items_to_remove):
    #     stock_entry.items.pop(i)

    result = {"stock_entry": None, "bad_items": bad_items}

    # # if after removal no items remain, return bad_items
    # if not stock_entry.items:
    #     return result



    # Save & submit, with handling for submit exceptions
    try:
        stock_entry.flags.ignore_mandatory = True
        stock_entry.save(ignore_permissions=True)
        stock_entry.reload()
        stock_entry.submit()
        result["stock_entry"] = stock_entry.name
        return result
    except Exception as exc:
        # log full trace
        frappe.log_error(title="Error Creating/Submitting Stock Entry",
                         message=f"Error submitting Stock Entry for {cons_doc.name}: {str(exc)}\n{frappe.get_traceback()}")

        return result


def already_issued(batch_no, item_code):
    result = frappe.db.sql("""
        SELECT sed.parent
        FROM `tabStock Entry Detail` sed
        JOIN `tabStock Entry` se ON se.name = sed.parent
        WHERE sed.batch_no = %s
          AND sed.item_code = %s
          AND se.stock_entry_type = 'Material Issue'
          AND se.docstatus = 1
        LIMIT 1
    """, (batch_no, item_code), as_dict=True)

    return result[0].get("parent") if result else None

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
           AND sbe.is_outward = 0
        ORDER BY sb.posting_date DESC, sb.posting_time DESC, sb.modified DESC
        LIMIT 1
    """, (batch_no,), as_dict=True)

    if result:
        return result[0].warehouse
    return None
