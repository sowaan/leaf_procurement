import frappe 	#type: ignore

@frappe.whitelist()
def get_batch_by_barcode(itemcode, barcode):
    batch = frappe.db.get_value(
        "Batch",
        {"item": itemcode, "batch_id": barcode},
        ["name", "batch_qty"],
        as_dict=True
    )
    if batch:
        batch_qty = float(batch.batch_qty or 0)
        return {
            "exists": True,
            "batch_no": batch.name,
            "batch_quantity": batch_qty
        }
    return {"exists": False}

import frappe  # type: ignore

@frappe.whitelist()
def get_invoice_item_by_barcode(itemcode, barcode):
    # Fetch the first Purchase Invoice Item with matching item and batch
    invoice_item = frappe.db.sql("""
        SELECT
            pii.name,
            pii.qty,
            pii.rate,
            pii.amount,
            pii.batch_no,
            pii.parent AS invoice_no,
            pi.supplier,
            pi.posting_date,
            pii.lot_number,
            pii.grade,
            pii.sub_grade
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE pii.item_code = %s AND pii.batch_no = %s AND pi.docstatus = 1
        ORDER BY pii.creation ASC
        LIMIT 1
    """, (itemcode, barcode), as_dict=True)

    if not invoice_item:
        return {"exists": False}

    i = invoice_item[0]

    return {
        "exists": True,
        "batch_no": i.batch_no,
        "rate": i.rate,
        "qty": i.qty,
        "lot_number": i.lot_number,
        "grade": i.grade,
        "sub_grade": i.sub_grade


    }

