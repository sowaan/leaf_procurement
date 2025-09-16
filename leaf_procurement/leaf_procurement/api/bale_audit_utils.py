import frappe 	#type: ignore

@frappe.whitelist()
def get_gtn_datails_for_bale (bale_barcode: str):
    try:
        # Find GTN Item with matching bale_barcode
        gtn_item = frappe.db.get_value("Goods Transfer Note Items", {"bale_barcode": bale_barcode}, ["parent", "weight"], as_dict=True)
        if not gtn_item:
            return     {
                "gtn_name": None,
                "tsa_number": None,
                "vehicle_number": None, 
                "weight": None
            } 
        # Get GTN main record fields
        gtn = frappe.db.get_value("Goods Transfer Note", gtn_item.parent, ["name", "tsa_number", "vehicle_number"], as_dict=True)
        if not gtn:
            return     {
                "gtn_name": None,
                "tsa_number": None,
                "vehicle_number": None, 
                "weight": None
            } 
        
        return {
            "gtn_name": gtn.name,
            "tsa_number": gtn.tsa_number,
            "vehicle_number": gtn.vehicle_number,
            "weight": gtn_item.weight
        }  
    except Exception as e:
        frappe.log_error(
            title="update_bale_audit_from_gtn Failed",
            message=f"Bale Barcode: {bale_barcode}\nError: {frappe.get_traceback()}"
        )

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
