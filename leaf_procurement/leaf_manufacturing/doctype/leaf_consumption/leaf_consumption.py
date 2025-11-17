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
		create_stock_entry(self)
	
def create_stock_entry(cons_doc):
    try:
        if not cons_doc.location:
            frappe.throw("Please provide Location to move stock.")


        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Issue"
        # stock_entry.to_warehouse = cons_doc.location

        # stock_entry.posting_date = cons_doc.date 
        # stock_entry.posting_time = "23:00:00"
        # stock_entry.purpose = "Material Issue"
        # stock_entry.set_posting_time = 1
        # stock_entry.skip_future_date_validation = True
        # stock_entry.custom_receiving_warehouse = cons_doc.location

        stock_entry.custom_reference_doctype = "Leaf Consumption"
        stock_entry.custom_reference_name = cons_doc.name

        bad_items = []
        for row in cons_doc.consumption_detail:
            try:
            # warehouse = get_current_batch_location(row.bale_barcode)
                batch_info = get_batch_qty(batch_no=row.bale_barcode, item_code=cons_doc.item)

                    # ✅ CASE 1 — No batch info found
                if not batch_info:
                    bad_items.append({
                        "batch_no": row.bale_barcode,
                        "reason": "Batch not found in any warehouse",
                        "expected_qty": row.purchase_weight,
                        "found_qty": 0,
                        "item_code": cons_doc.item
                    })
                    continue  # ✅ Skip this item and move to next      
                
                info = batch_info[0]

                if flt(info.get("qty"), 3) != flt(row.purchase_weight, 3):
                        bad_items.append({
                            "batch_no": row.bale_barcode,
                            "reason": "Batch quantity mismatch",
                            "expected_qty": row.purchase_weight,
                            "found_qty": info.get("qty"),
                            "item_code": cons_doc.item
                        })
                        continue  # ✅ Skip this item and move forward

                # ✅ All good — safe to use warehouse
                warehouse = info["warehouse"]     

                if not warehouse:
                    frappe.throw(f"Batch {row.bale_barcode} not found in any warehouse")

                # frappe.log_error(f"Batch {row.bale_barcode} found in warehouse {warehouse}")    

                details = get_invoice_item_by_barcode(cons_doc.item, row.bale_barcode)
                if not details:
                    frappe.throw(f"Batch {row.bale_barcode} not found in any Purchase Invoice for item {cons_doc.item}")
                
                # rate = details.get("rate")
                lot_number = details.get("lot_number")
                grade = details.get("grade")
                sub_grade = details.get("sub_grade")
                # reclassification_grade = details.get("reclassification_grade")
                # invoice_qty = details.get("qty")

                stock_entry.append("items", {
                    "item_code": cons_doc.item,
                    "qty": row.purchase_weight,
                    "s_warehouse": warehouse,

                    "uom": "Kg",
                    "stock_uom": "Kg",
                    "conversion_factor": 1,

                    "use_serial_batch_fields": 1,
                    "batch_no": row.bale_barcode,
                    "reclassification_grade": row.internal_grade,
                    "process_order": cons_doc.process_order,
                    "lot_number": lot_number,
                    "grade": grade,
                    "sub_grade": sub_grade,
                    # "basic_rate": rate,
                    # "basic_amount": rate * invoice_qty
                })
            except Exception as ex:
                # ✅ Unexpected exception for this batch — record it
                bad_items.append({
                    "batch_no": row.bale_barcode,
                    "item_code": cons_doc.item,
                    "reason": f"Unexpected error see detailed reason field.",
                    "expected_qty": row.purchase_weight,
                    "found_qty": info.get("qty") if 'info' in locals() else None,
                    "detailed_reason": str(ex)
                })
                continue  # ✅ Skip this batch and move to next           

        # ✅ Must call these controller methods BEFORE insert/submit
        stock_entry.set_missing_values()
        stock_entry.calculate_rate_and_amount()

        # ✅ Save as draft first — so ERPNext processes the valuation properly
        stock_entry.save(ignore_permissions=True)

        # ✅ Now reload (to simulate UI reload)
        stock_entry.reload()

        # ✅ Submit (GL entries will now be created)
        stock_entry.submit()

        if bad_items:
            for b in bad_items:
                cons_doc.append("bad_items", {
                    "batch_no": b["batch_no"],
                    "item_code": b["item_code"],
                    "reason": b["reason"],
                    "expected_qty": b["expected_qty"],
                    "found_qty": b["found_qty"],
                    "source_warehouse": b.get("source_warehouse")
                })

            cons_doc.save(ignore_permissions=True)

            message = "<br>".join([
                f"Batch <b>{b['batch_no']}</b>: {b['reason']} "
                f"(Expected: {b['expected_qty']}, Found: {b['found_qty']})"
                for b in bad_items
            ])

            # frappe.msgprint(_("Stock Entry {0} created with some issues. ").format(stock_entry.name))
            frappe.msgprint("Stock Entry created with errors. Some items were skipped:<br><br>" + message)
        else:
            frappe.msgprint(_("Stock Entry {0} created successfully").format(stock_entry.name))
        
        frappe.db.commit()
        return {
            "stock_entry": stock_entry.name,
            "bad_items": bad_items
        }
    except ValidationError as ve:
        frappe.throw(ve)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in creating Stock Entry for Leaf Consumption")
        frappe.throw(_("An error occurred while creating Stock Entry: {0}").format(str(e)))


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
