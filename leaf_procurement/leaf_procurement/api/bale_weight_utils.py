import frappe 	#type: ignore

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