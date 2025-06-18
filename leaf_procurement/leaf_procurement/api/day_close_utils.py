import frappe # type: ignore

@frappe.whitelist()
def check_gtn_and_grade_difference(date):
    mismatches = []

    # Step 1: Get all bale IDs from Bale Registration Detail for the given date
    registration_names = frappe.get_all("Bale Registration", filters={"date": date}, pluck="name")
    bale_ids_registered = frappe.get_all(
        "Bale Registration Detail",
        filters={"parent": ["in", registration_names]},
        pluck="bale_barcode"
    )

    if not bale_ids_registered:
        return  mismatches# or return None / {} / [] depending on your function
    
    # Step 2: Get bale IDs from submitted GTNs
    bale_ids_with_gtn = frappe.db.sql("""
        SELECT gd.bale_barcode
        FROM `tabGoods Transfer Note Items` gd
        JOIN `tabGoods Transfer Note` gtn ON gd.parent = gtn.name
        WHERE gtn.docstatus = 1 AND gd.bale_barcode IN %s
    """, (tuple(bale_ids_registered),), as_dict=True)
    bale_ids_with_gtn = {d.bale_barcode for d in bale_ids_with_gtn}

    # Step 3: Now check only bales that are missing in GTN
    bales_missing_gtn = set(bale_ids_registered) - bale_ids_with_gtn

    for bale_id in bales_missing_gtn:
        result = frappe.db.sql("""
            SELECT d.item_grade, d.rate, d.weight
            FROM `tabBale Weight Detail` d
            JOIN `tabBale Weight Info` p ON d.parent = p.name
            WHERE d.bale_barcode = %s AND p.docstatus = 1
            LIMIT 1
        """, (bale_id,), as_dict=True)

        if not result:
            continue

        item_grade, rate, weight = result       
            
        # Get rejection status from Item Grade
        is_rejected = frappe.db.get_value("Item Grade", {"item_grade_name": item_grade}, "rejected_grade")

        if not is_rejected :
            mismatches.append({
                "bale_id": bale_id,
                "item_grade": item_grade or "-",
                "weight": weight or "-",
                "rate": rate or "-",
                "gtn_status": "Missing",
                "note": "GTN missing and grade is not rejected or grades differ"
            })

    return mismatches
