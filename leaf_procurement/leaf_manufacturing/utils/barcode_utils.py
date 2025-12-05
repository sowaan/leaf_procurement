import frappe 	#type: ignore

@frappe.whitelist()
def get_invoice_item_by_barcode(itemcode, barcode):
    # 1) Try to fetch from Purchase Invoice Item first
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
        WHERE pii.item_code = %s
          AND pii.qty > 0
          AND pii.batch_no = %s
          AND pi.docstatus = 1
        ORDER BY pii.creation ASC
        LIMIT 1
    """, (itemcode, barcode), as_dict=True)

    # If we found invoice data, return that
    if invoice_item:
        i = invoice_item[0]
        return {
            "exists": True,
            "source": "Purchase Invoice",
            "batch_no": i.batch_no,
            "rate": i.rate,
            "qty": i.qty,
            "lot_number": i.lot_number,
            "grade": i.grade,
            "sub_grade": i.sub_grade,
            "reclassification_grade": i.reclassification_grade,
        }

    # 2) If no invoice item, try Bale Creation Detail
    bale = frappe.db.get_value(
        "Bale Creation Detail",
        {"bale_barcode": barcode},
        ["bale_barcode", "reclassification_grade", "rate", "weight"],
        as_dict=True,
    )

    if bale:
        return {
            "exists": True,
            "source": "Bale Creation Detail",
            # Treat bale_barcode as batch_no for consistency
            "batch_no": bale.bale_barcode,
            "rate": bale.rate,
            # Assuming 'weight' is the quantity equivalent
            "qty": bale.weight,
            # These don't exist on Bale Creation Detail, so we return None
            "lot_number": None,
            "grade": None,
            "sub_grade": None,
            "reclassification_grade": bale.reclassification_grade,
        }

    # 3) Nothing found in either place
    return {"exists": False}


@frappe.whitelist()
def check_bale_barcode_exists(bale_barcode):
    if not bale_barcode:
        return False

    exists = frappe.db.exists("Leaf Consumption Detail", {"bale_barcode": bale_barcode, "doc_status":1})
    return bool(exists)
