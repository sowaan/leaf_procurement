import frappe 	#type: ignore

@frappe.whitelist()
def get_available_bale_registrations(doctype, txt, searchfield, start, page_len, filters):
    # Get bale registrations that are not already linked in a Bale Purchase
    return frappe.db.sql("""
        SELECT name
        FROM `tabBale Registration`
        WHERE name NOT IN (
            SELECT bale_registration_code
            FROM `tabBale Purchase`
            WHERE docstatus < 2
            AND bale_registration_code IS NOT NULL
        )
        AND name LIKE %(txt)s
                         AND docstatus=1
        ORDER BY name
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })	

@frappe.whitelist()
def get_bale_registration_code_by_barcode(barcode):
    # Step 1: Get parent Bale Registration Code
    result = frappe.db.get_value('Bale Registration Detail', {'bale_barcode': barcode}, 'parent', as_dict=True)
    if not result:
        return None

    bale_registration_code = result.parent

    # Step 2: Check if already exists in Bale Purchase
    exists_in_purchase = frappe.db.exists('Bale Purchase', {'bale_registration_code': bale_registration_code})
    if exists_in_purchase:
        return None  # Already used, don't allow again

    return bale_registration_code  # Valid and not used yet

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