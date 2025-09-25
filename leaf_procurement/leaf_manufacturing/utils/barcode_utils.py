import frappe 	#type: ignore

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
            pii.sub_grade,
            pii.reclassification_grade,
            pi.custom_stationary
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
                WHERE pii.item_code = %s and qty>0 AND pii.batch_no = %s AND pi.docstatus = 1       
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
        "sub_grade": i.sub_grade,
        "reclassification_grade": i.reclassification_grade
    }

@frappe.whitelist()
def check_bale_barcode_exists(bale_barcode):
    if not bale_barcode:
        return False

    exists = frappe.db.exists("Leaf Consumption Detail", {"bale_barcode": bale_barcode, "doc_status":1})
    return bool(exists)
