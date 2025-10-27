import frappe # type: ignore
from frappe import _ # type: ignore
@frappe.whitelist()
def force_submit_gtn(gtn_name, skip_stock_entry=True):
    # if frappe.session.user != "Administrator":
    #     frappe.throw(_("Only Administrator is allowed to perform this operation."))

    try:
        
        gtn_doc = frappe.get_doc("Goods Transfer Note", gtn_name)

        if gtn_doc.docstatus == 1:
            return f"GTN {gtn_name} is already submitted."

        # Temporarily disable link validation
        frappe.flags.ignore_links = True
        frappe.flags.ignore_validate_update_after_submit = True

        # Bypass standard validation
        gtn_doc.flags.ignore_validate = True
        gtn_doc.flags.ignore_validate_update_after_submit = True
        gtn_doc.flags.ignore_links = True
        gtn_doc.flags.ignore_permissions = True
        gtn_doc.skip_stock_entry = skip_stock_entry
        # Submit document
        gtn_doc.submit()
        frappe.db.commit()

        frappe.flags.ignore_links = False
        frappe.msgprint(f"✅ Successfully submitted GTN: {gtn_name}")
        return f"Successfully submitted GTN: {gtn_name}"

    except Exception as e:
        frappe.log_error(title="Force Submit GTN Failed", message=frappe.get_traceback())
        frappe.throw(f"❌ Failed to submit GTN {gtn_name}: {str(e)}")