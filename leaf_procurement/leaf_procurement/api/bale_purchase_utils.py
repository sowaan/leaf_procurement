import frappe 	#type: ignore

@frappe.whitelist()
def get_available_bale_registrations(doctype, txt, searchfield, start, page_len, filters):
    open_day = frappe.db.get_value(
        "Day Setup",
        {"status": "Opened"},
        "date",
        order_by="date desc"
    )

    if not open_day:
        return []
    

    # Get bale registrations that are not already linked in a Bale Purchase
    return frappe.db.sql("""
        SELECT br.name
        FROM `tabBale Registration` br
        WHERE br.name NOT IN (
            SELECT bp.bale_registration_code
            FROM `tabBale Purchase` bp
            WHERE bp.docstatus < 2
            AND bp.bale_registration_code IS NOT NULL
        )
        AND br.docstatus = 1
        AND br.name LIKE %(txt)s
        AND br.date = %(open_day)s
        AND (
            SELECT COUNT(*)
            FROM `tabBale Registration Detail` brd
            WHERE brd.parent = br.name
        ) >
        (
            SELECT COUNT(*)
            FROM `tabBale Purchase Detail` bpd
            WHERE bpd.parent IN (
                SELECT name FROM `tabBale Purchase`
                WHERE bale_registration_code = br.name AND docstatus < 2
            )
        )
        ORDER BY br.name
        LIMIT %(start)s, %(page_len)s
    """, {
        "open_day": open_day,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })

    # return frappe.db.sql("""
    #     SELECT name
    #     FROM `tabBale Registration`
    #     WHERE name NOT IN (
    #         SELECT bale_registration_code
    #         FROM `tabBale Purchase`
    #         WHERE docstatus < 2
    #         AND bale_registration_code IS NOT NULL
    #     )
    #     AND name LIKE %(txt)s
    #                      AND docstatus=1
    #     ORDER BY name
    #     LIMIT %(start)s, %(page_len)s
    # """, {
    #     "txt": f"%{txt}%",
    #     "start": start,
    #     "page_len": page_len
    # })	

@frappe.whitelist()
def get_bale_registration_code_by_barcode(barcode):
    open_day = frappe.db.get_value(
        "Day Setup",
        {"status": "Opened"},
        "date",
        order_by="date desc"
    )

    if not open_day:
        return None

    # Step 1: Find the Bale Registration this barcode belongs to
    reg_detail = frappe.db.get_value('Bale Registration Detail', {'bale_barcode': barcode}, 'parent', as_dict=True)
    if not reg_detail:
        return None

    bale_registration_code = reg_detail.parent

    # Step 2: Check if this bale barcode has already been used in any purchase
    reg_date = frappe.db.get_value("Bale Registration", bale_registration_code, "date")

    if reg_date != open_day:
        return None  # Already used, don't allow reuse
    
    # Step 3: Check if this bale barcode has already been used in any purchase
    if frappe.db.exists('Bale Purchase Detail', {'bale_barcode': barcode}):
        return None  # Already used, don't allow reuse


    return bale_registration_code  # Valid and still has unused barcodes


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

@frappe.whitelist()
def get_free_gtn(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT gtn.name
        FROM `tabGoods Transfer Note` gtn
        WHERE NOT EXISTS (
            SELECT grn.gtn_number FROM `tabGoods Receiving Note` grn
            WHERE grn.gtn_number = gtn.name
        )
        AND gtn.name LIKE %(txt)s
        AND gtn.docstatus = 1
        ORDER BY gtn.creation ASC
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": int(start),
        "page_len": int(page_len)
    })
