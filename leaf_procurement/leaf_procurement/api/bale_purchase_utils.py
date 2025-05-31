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