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