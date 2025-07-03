import frappe 	#type: ignore

@frappe.whitelist()
def check_draft_audits_exist(date, location):
    # Check if any draft Bale Audit exists for the given date and warehouse
    exists = frappe.db.exists(
        "Bale Audit",
        {
            "docstatus": 0,
            "date": date,
            "location_warehouse": location
        }
    )
    return {"exists": bool(exists)}

@frappe.whitelist()
def check_audit_records_exist(date, location):
    count = frappe.db.count("Bale Audit", {
        "date": date,
        "location_warehouse": location,
        "docstatus": 1
    })

    return {"exists": count > 0}

@frappe.whitelist()
def check_bale_barcode_exists(bale_barcode):
    if not bale_barcode:
        return False

    exists = frappe.db.exists("Bale Audit Detail", {"bale_barcode": bale_barcode})
    return bool(exists)
