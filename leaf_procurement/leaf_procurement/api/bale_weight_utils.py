import frappe 	#type: ignore
from frappe import _ 	#type: ignore
from frappe.utils import nowdate 	#type: ignore

@frappe.whitelist()
def get_bale_registration_code_by_barcode(barcode):
    # Step 1: Get parent Bale Registration Code
    result = frappe.db.get_value('Bale Registration Detail', {'bale_barcode': barcode}, 'parent', as_dict=True)
    if not result:
        return None

    bale_registration_code = result.parent

    # Step 2: Check if already exists in Bale Purchase
    exists_in_purchase = frappe.db.exists('Bale Weight Info', {'bale_registration_code': bale_registration_code})
    if exists_in_purchase:
        return None  # Already used, don't allow again

    return bale_registration_code  # Valid and not used yet

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
    warehouse_info = frappe.db.get_value(
        "Warehouse", 
        doc.location_warehouse, 
        ["custom_transport_charges"], 
        as_dict=True
    )
    day_setup = frappe.db.get_value(
        "Day Setup",
        doc.date,
        ["due_date"],
        as_dict=True
    )


    if doc.purchase_receipt_created:
        frappe.throw(_("Purchase Receipt has already been created for this Bale Weight Info."))

    purchase_name = frappe.db.get_value("Bale Purchase",
        {"bale_registration_code": doc.bale_registration_code}
    )

    # Default values from master doc
    company = doc.company
    warehouse = doc.location_warehouse
    rejected_warehouse = doc.rejected_item_location
    registration_code = doc.bale_registration_code
    transport_charges_rate = warehouse_info.custom_transport_charges
    transport_charges_item = doc.transport_charges_item

    rejected_grade = doc.rejected_item_grade
    rejected_sub_grade = doc.rejected_item_sub_grade

    if not transport_charges_item:
        frappe.throw(f"Transport Charges Item Code in not defined at Settings Screen")
    invoice_weight = 0

    # Create Purchase Invoice
    invoice = frappe.new_doc("Purchase Invoice")
    invoice.supplier = doc.supplier_grower
    invoice.posting_date = nowdate()
    invoice.company = company
    invoice.set_posting_time = 1
    invoice.update_stock = 1
    invoice.set_warehouse = warehouse
    invoice.rejected_warehouse = rejected_warehouse
    invoice.due_date = day_setup.due_date

    item_weight = 0
    item_grade = rejected_grade
    item_sub_grade = rejected_sub_grade
    item_rate = 0

    for detail in doc.detail_table:
        purchase_detail = frappe.db.get_value(
            "Bale Purchase Detail",
            {
                "parent": purchase_name,
                # "item": doc.item,
                "bale_barcode": detail.bale_barcode
            },
            ["item_grade", "item_sub_grade"],
            as_dict=True
        )

        if not purchase_detail:
            frappe.throw(
                _("No matching purchase detail found in Bale Purchase for item {0} and batch {1}")
                .format(doc.item, detail.bale_barcode)
            )
            
        if detail.item_grade == rejected_grade or  detail.item_grade != purchase_detail.item_grade or detail.item_sub_grade != purchase_detail.item_sub_grade:
            ensure_batch_exists(detail.bale_barcode, doc.item, 0)
            invoice.append("custom_rejected_items", {
                "item_code": doc.item,
                "qty": 0,
                "stock_qty": 0,  # Required field
                "rate": 0,
                "amount": 0,     # Required field
                "base_rate": 0,  # Required field
                "base_amount": 0,  # Required field
                "uom": "Kg",
                # "warehouse": rejected_warehouse,  # Only needed if this affects stock
                "use_serial_batch_fields": 1,
                "batch_no": detail.bale_barcode,
                "description": f"Bale Barcode: {detail.bale_barcode}",
                "lot_number": registration_code,
                "grade": rejected_grade,
                "sub_grade": rejected_sub_grade,
            })  
        else:
            ensure_batch_exists(detail.bale_barcode, doc.item, detail.weight)
            invoice.append("items", {
                "item_code": doc.item,
                "qty": detail.weight,
                "received_qty": detail.weight,
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
            invoice_weight += detail.weight             


        

    invoice.append("items", {
        "item_code": transport_charges_item,
        "qty": invoice_weight,
        "rate": transport_charges_rate,
        "uom": "Kg",
        "description": f"Transport Charges for Invoice Weight {invoice_weight} Kg",

    })

    invoice.save()
    invoice.submit()

    # Mark the source document as processed and save invoice number to source document
    doc.db_set("purchase_receipt_created", 1)
    doc.db_set("purchase_invoice", invoice.name)    

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
        # Create new batch if it doesn't exist  
        batch = frappe.new_doc("Batch")
        batch.batch_id = batch_no
        batch.item = item_code
        batch.batch_qty = batch_qty
        batch.save()
    else:
        # Update existing batch quantity
        batch = frappe.get_doc("Batch", {"batch_id": batch_no, "item": item_code})
        batch.batch_qty = batch_qty  # Add to existing quantity
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
        and br.docstatus=1 and bp.docstatus=1
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