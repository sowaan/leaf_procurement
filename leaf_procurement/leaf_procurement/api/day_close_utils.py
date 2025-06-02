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
        purchase_grade = frappe.db.get_value("Bale Purchase Detail", {"bale_barcode": bale_id}, "item_grade")
        weight_grade = frappe.db.get_value("Bale Weight Detail", {"bale_barcode": bale_id}, "item_grade")

        # Skip if grade data is incomplete
        if not purchase_grade or not weight_grade:
            mismatches.append({
                "bale_id": bale_id,
                "purchase_grade": purchase_grade,
                "weight_grade": weight_grade,
                "gtn_status": "Missing",
                "note": "GTN missing and grade is not rejected or grades differ"
            })
            continue

        # Get rejection status from Item Grade
        is_rejected = frappe.db.get_value("Item Grade", {"item_grade_name": weight_grade}, "rejected_grade")

        if not is_rejected and  purchase_grade == weight_grade:
            mismatches.append({
                "bale_id": bale_id,
                "purchase_grade": purchase_grade or "Not Found",
                "weight_grade": weight_grade or "Not Found",
                "gtn_status": "Missing",
                "note": "GTN missing and grade is not rejected or grades differ"
            })

    return mismatches
