import frappe 	#type: ignore
from frappe import _ 	#type: ignore
from frappe.utils import nowdate 	#type: ignore


@frappe.whitelist()
def create_purchase_invoice(bale_weight_info_name: str) -> str:
    """
    Creates a Purchase Invoice based on the Bale Weight Info document.

    Args:
        bale_weight_info_name (str): The name of the Bale Weight Info document.

    Returns:
        str: The name of the created Purchase Invoice.
    """
    doc = frappe.get_doc("Bale Weight Info", bale_weight_info_name)

    if doc.purchase_receipt_created:
        frappe.throw(_("Purchase Receipt has already been created for this Bale Weight Info."))

    # Default values from master doc
    company = doc.company
    warehouse = doc.location_warehouse
    rejected_warehouse = doc.rejected_item_location
    registration_code = doc.bale_registration_code

    # Create Purchase Invoice
    invoice = frappe.new_doc("Purchase Invoice")
    invoice.supplier = doc.supplier_grower
    invoice.posting_date = nowdate()
    invoice.company = company
    invoice.set_posting_time = 1
    invoice.update_stock = 1
    invoice.set_warehouse = warehouse
    invoice.rejected_warehouse = rejected_warehouse

    for detail in doc.detail_table:
        ensure_batch_exists(detail.bale_barcode, doc.item, detail.weight)

        invoice.append("items", {
            "item_code": doc.item,
            "qty": detail.weight,
            "rate": detail.rate,
            "uom": "Kg",
            "warehouse": warehouse,
            "use_serial_batch_fields": 1,
            "batch_no": detail.bale_barcode,
            "description": f"Bale Barcode: {detail.bale_barcode}",
            "lot_number": registration_code,
            "grade": detail.item_grade,
            "sub_grade": detail.item_sub_grade,
        })

    invoice.save()
    invoice.submit()

    # Mark the source document as processed
    doc.db_set("purchase_receipt_created", 1)
    
    frappe.db.commit()

    return invoice.name


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
        batch = frappe.new_doc("Batch")
        batch.batch_id = batch_no
        batch.item = item_code
        batch.batch_qty = batch_qty
        batch.save()


@frappe.whitelist()
def get_available_bale_registrations(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT br.name
        FROM `tabBale Registration` br
        INNER JOIN `tabBale Purchase` bp
            ON bp.bale_registration_code = br.name
            AND bp.docstatus < 2
        WHERE NOT EXISTS (
            SELECT 1 FROM `tabBale Weight Info` bwi
            WHERE bwi.bale_registration_code = br.name
        )
        AND br.name LIKE %(txt)s
        ORDER BY br.name
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })


@frappe.whitelist()
def get_registered_bale_count(bale_registration_code):
    if not bale_registration_code:
        return 0

    total = frappe.db.count("Bale Registration Detail", {
        "parent": bale_registration_code
    })

    return total

@frappe.whitelist()
def get_supplier(bale_registration_code):
    if not bale_registration_code:
        return None

    # Get the supplier field from Bale Registration
    supplier = frappe.db.get_value("Bale Registration", bale_registration_code, "supplier_grower")
    return supplier