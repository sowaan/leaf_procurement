import frappe
from frappe import _


def successful_login(login_manager):
    user = login_manager.user
    api_key = frappe.db.get_value("User", user, "api_key")
    api_secret = frappe.db.get_value("User", user, "api_secret")

    # If user has both API Key and Secret, block login
    if api_key and api_secret:
        frappe.throw(_("This user is restricted to API access only."), frappe.AuthenticationError)
        