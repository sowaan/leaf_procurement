import frappe # type: ignore
from frappe import _

# In audit_day_setup.py or any relevant file
@frappe.whitelist()
def get_user_audit_day_status():
    return frappe.get_all(
        "Audit Day Setup",
        filters={
            "date": frappe.utils.today()
        },
        fields=["name", "location_warehouse", "day_open_time", "day_close_time"]
    )


@frappe.whitelist()
def check_gtn_and_grade_difference(date):
   # ----------- 1. Check for Unprinted Vouchers (bale_status != 'Completed') ----------
    incomplete_vouchers = frappe.get_all(
        "Purchase Invoice",
        filters={
            "posting_date": date,
            "custom_stationary": ["in", [None, ""]],
            "docstatus": 1  # Optional: Only consider submitted invoices
        },
        fields=["name"]
    )

    if incomplete_vouchers:
        invoice_names = [d["name"] for d in incomplete_vouchers]
        frappe.throw(
            _("Please print vouchers for the following Purchase Invoices to continue:\n{0}")
            .format(", ".join(invoice_names))
        )   
        
    # ----------- 2. Check GTN and Grade Mismatches ----------
    mismatches = []

    # Get all Bale Registration names and details for the date
    registration_names = frappe.get_all("Bale Registration", filters={"date": date}, pluck="name")
    bale_ids_registered = frappe.get_all(
        "Bale Registration Detail",
        filters={"parent": ["in", registration_names]},
        pluck="bale_barcode"
    )

    if not bale_ids_registered:
        return mismatches

    # Get bale IDs present in submitted GTNs
    bale_ids_with_gtn = frappe.db.sql("""
        SELECT gd.bale_barcode
        FROM `tabGoods Transfer Note Items` gd
        JOIN `tabGoods Transfer Note` gtn ON gd.parent = gtn.name
        WHERE gtn.docstatus = 1 AND gd.bale_barcode IN %s
    """, (tuple(bale_ids_registered),), as_dict=True)

    bale_ids_with_gtn = {d.bale_barcode for d in bale_ids_with_gtn}

    # Identify bales missing in GTN
    bales_missing_gtn = set(bale_ids_registered) - bale_ids_with_gtn

    for bale_id in bales_missing_gtn:
        result = frappe.db.sql("""
            SELECT d.item_grade, d.rate, d.weight
            FROM `tabBale Weight Detail` d
            JOIN `tabBale Weight Info` p ON d.parent = p.name
            WHERE d.bale_barcode = %s AND p.docstatus = 1
            LIMIT 1
        """, (bale_id,), as_dict=True)

        if result:
            item_grade = result[0]["item_grade"]
            rate = result[0]["rate"]
            weight = result[0]["weight"]
        else:
            continue

        is_rejected = frappe.db.get_value("Item Grade", {"item_grade_name": item_grade}, "rejected_grade")

        if not is_rejected:
            mismatches.append({
                "bale_id": bale_id,
                "item_grade": item_grade or "-",
                "weight": weight or "-",
                "rate": rate or "-",
                "gtn_status": "Missing",
                "note": "GTN missing and grade is not rejected"
            })

    return mismatches
