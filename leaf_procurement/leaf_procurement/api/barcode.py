import frappe 	#type: ignore

@frappe.whitelist()
def get_bale_record_status(bale_barcode):
    def get_status_and_name(child_table, parent_doctype, filter_field="bale_barcode", batch=False):
        # Handle special case for Purchase Invoice using batch_no
        field = "batch_no" if batch else filter_field
        records = frappe.db.get_all(
            child_table,
            filters={field: bale_barcode},
            fields=["parent"],
            distinct=True
        )
        if not records:
            return "No Record Found", ""

        for docstatus in [1, 0, 2]:  # Priority: Submitted > Draft > Cancelled
            for r in records:
                doc = frappe.db.get_value(parent_doctype, r.parent, ["name", "docstatus"])
                if doc and doc[1] == docstatus:
                    status_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
                    return status_map[docstatus], doc[0]

        return "Unknown", ""

    status = {}

    status["in_bale_registration"], status["bale_registration_name"] = get_status_and_name(
        "Bale Registration Detail", "Bale Registration"
    )

    status["in_bale_purchase"], status["bale_purchase_name"] = get_status_and_name(
        "Bale Purchase Detail", "Bale Purchase"
    )

    status["in_bale_weight"], status["bale_weight_info_name"] = get_status_and_name(
        "Bale Weight Detail", "Bale Weight Info"
    )

    status["in_purchase_invoice"], status["purchase_invoice_name"] = get_status_and_name(
        "Purchase Invoice Item", "Purchase Invoice", batch=True
    )

    status["in_gtn"], status["goods_transfer_note_name"] = get_status_and_name(
        "Goods Transfer Note Items", "Goods Transfer Note"
    )

    status["in_grn"], status["goods_receiving_note_name"] = get_status_and_name(
        "Goods Receiving Detail", "Goods Receiving Note"
    )

    return status


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
    pii.sub_grade,
    bwi.name AS bale_weight_info_name,
    bwi.stationery
FROM `tabPurchase Invoice Item` pii
INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
LEFT JOIN `tabBale Weight Info` bwi ON bwi.purchase_invoice = pi.name
        WHERE pii.item_code = %s and qty>0 AND pii.batch_no = %s AND pi.docstatus = 1
            AND bwi.stationery is not null
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

