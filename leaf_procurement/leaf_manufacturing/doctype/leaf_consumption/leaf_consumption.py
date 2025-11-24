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

    def on_submit(self):
        try:
            result = create_stock_entry(self)
        except Exception as e:
            frappe.throw(_("Error creating Stock Entry: {0}").format(str(e)))

        bad_items = result.get("bad_items", [])
        stock_entry = result.get("stock_entry")
        # -----------------------------
        # FINAL MESSAGE
        # -----------------------------
        if bad_items:
            message = "<br>".join([
                f"Batch <b>{b['batch_no']}</b>: {b['reason']} "
                for b in bad_items
            ])

        # If no stock entry created → cancel submit
        if not stock_entry:
            frappe.throw(
                _("No Stock Entry created due to the following issues:<br><br>{0}<br><br>Kindly refresh the page to see details.").format(message),
                frappe.ValidationError
            )

        if bad_items:
            frappe.msgprint("Stock Entry created with some skipped items:<br><br>" + message)
        else:
            frappe.msgprint(_("Stock Entry {0} created successfully").format(stock_entry.name))


	
def create_stock_entry(cons_doc):

    if not cons_doc.location:
        frappe.throw("Please provide Location to move stock.")

    cons_doc.set("bad_items", [])
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Issue"
    stock_entry.custom_reference_doctype = "Leaf Consumption"
    stock_entry.custom_reference_name = cons_doc.name

    bad_items = []

    for row in cons_doc.consumption_detail:
        try:
            # -----------------------------
            # CASE 1: Batch already issued
            # -----------------------------            
            sename = already_issued(row.bale_barcode, cons_doc.item)
            if sename:
                bad_items.append({
                    "batch_no": row.bale_barcode,
                    "reason": "Already Issued",
                    "expected_qty": row.purchase_weight,
                    "found_qty": 0,
                    "item_code": cons_doc.item,
                    "detailed_reason": f"Already issued in Stock Entry {sename}"
                })
                continue

            
            batch_info = get_batch_qty(batch_no=row.bale_barcode, item_code=cons_doc.item)
            info = batch_info[0] if batch_info else None

            # -----------------------------
            # CASE 2: Batch info NOT found
            # -----------------------------
            if not info:
                #-----------------------------------
                # CASE 3: Check if batch in transit
                #-----------------------------------
                transit_entry = get_transit_stock_entry(row.bale_barcode)
                if transit_entry:
                    bad_items.append({
                        "batch_no": row.bale_barcode,
                        "reason": "Batch In Transit",
                        "expected_qty": row.purchase_weight,
                        "found_qty": 0,
                        "item_code": cons_doc.item,
                        "detailed_reason": f"Batch is currently in transit via Stock Entry {transit_entry}."
                    })
                    continue

                bad_items.append({
                    "batch_no": row.bale_barcode,
                    "reason": "Batch Not Found",
                    "expected_qty": row.purchase_weight,
                    "found_qty": 0,
                    "item_code": cons_doc.item,
                    "detailed_reason": "No batch information found in the system."
                })
                continue

            warehouse = info.get("warehouse")
            found_qty = flt(info.get("qty") or 0, 3)

            # -----------------------------
            # CASE 4: Qty mismatch
            # -----------------------------
            if found_qty != flt(row.purchase_weight, 3):
                bad_items.append({
                    "batch_no": row.bale_barcode,
                    "reason": "Quantity Mismatch",
                    "expected_qty": row.purchase_weight,
                    "found_qty": found_qty,
                    "item_code": cons_doc.item,
                    "detailed_reason": f"Expected {row.purchase_weight}, but found {found_qty} in batch."
                })
                continue

            # -----------------------------
            # CASE 5: Validate invoice details
            # -----------------------------
            details = get_invoice_item_by_barcode(cons_doc.item, row.bale_barcode)

            if not details:
                bad_items.append({
                    "batch_no": row.bale_barcode,
                    "reason": "Invoice Not Found",
                    "expected_qty": row.purchase_weight,
                    "found_qty": found_qty,
                    "item_code": cons_doc.item,
                    "detailed_reason": "No matching invoice details found for this barcode."
                })
                continue

            rate = details.get("rate")
            lot_number = details.get("lot_number")
            grade = details.get("grade")
            sub_grade = details.get("sub_grade")
            invoice_qty = details.get("qty")

            # -----------------------------
            # ADD VALID ITEM TO STOCK ENTRY
            # -----------------------------
            stock_entry.append("items", {
                "item_code": cons_doc.item,
                "qty": row.purchase_weight,
                "s_warehouse": warehouse,

                "uom": "Kg",
                "stock_uom": "Kg",
                "conversion_factor": 1,

                "batch_no": row.bale_barcode,
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
            frappe.log_error("Error Creating Stock Entry For POS", str(ex))
            bad_items.append({
                "batch_no": row.bale_barcode,
                "item_code": cons_doc.item,
                "reason": "Unexpected error",
                "expected_qty": row.purchase_weight,
                "found_qty": 0,
                "detailed_reason": str(ex)
            })
            continue

    # -----------------------------
    # SAVE BAD ITEMS IN DOC
    # -----------------------------
    if bad_items:
        for b in bad_items:
            cons_doc.append("bad_items", {
                "batch_no": b["batch_no"],
                "item_code": b["item_code"],
                "reason": b["reason"],
                "expected_qty": b["expected_qty"],
                "found_qty": b.get("found_qty", 0),
                "detailed_reason": b["detailed_reason"]

            })
        cons_doc.save(ignore_permissions=True)
        frappe.db.commit()
        

    # -----------------------------
    # NO VALID ITEMS → STOP HERE
    # -----------------------------
    if not stock_entry.items:
        # frappe.msgprint("No valid items found. Stock Entry will not be created.")
        return {
            "stock_entry": None,
            "bad_items": bad_items
        }

    # -----------------------------
    # PROCESS & SUBMIT STOCK ENTRY
    # -----------------------------
    stock_entry.set_missing_values()
    stock_entry.calculate_rate_and_amount()
    stock_entry.save(ignore_permissions=True)
    stock_entry.reload()
    stock_entry.submit()


    return {
        "stock_entry": stock_entry.name,
        "bad_items": bad_items
    }

def get_transit_stock_entry(batch_no):
    """
    Returns Stock Entry name if the given batch is in transit.
    Otherwise returns None.
    """

    query = """
        SELECT se.name
        FROM `tabStock Entry` se
        INNER JOIN `tabStock Entry Detail` sei 
            ON sei.parent = se.name
        WHERE 
            se.docstatus = 1
            AND sei.add_to_transit = 1
            AND sei.batch_no = %s
        LIMIT 1
    """

    result = frappe.db.sql(query, (batch_no,), as_dict=True)

    if result:
        return result[0].name  # Stock Entry number

    return None

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
