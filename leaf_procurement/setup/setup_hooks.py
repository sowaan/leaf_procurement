import frappe

def set_supplier_naming_series():
    try:
        buying_settings = frappe.get_single("Buying Settings")
        buying_settings.supp_master_name = "Naming Series"
        buying_settings.save()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Failed to set Buying Settings")
