# your_app/setup/setup_wizard.py
import frappe
from frappe import _
import requests
from leaf_procurement.leaf_procurement.utils.sync_down import sync_down_worker


def get_setup_stages(args=None):
    stages = [
			{
				"status": _("Connecting with live server"),
				"fail_msg": _("Failed to connect with live server"),
				"tasks": [{"fn": setup_server, "args": args, "fail_msg": _("Failed to connect with live server")}],
			}
		]

    return stages

def setup_server(args):
    
    if is_frappe_api_key_valid(args.get("server_url"), args.get("api_key"), args.get("api_secret"))    :
        frappe.db.set_single_value("Leaf Procurement Settings", "instance_url", args.get("server_url"))
        frappe.db.set_single_value("Leaf Procurement Settings", "api_key", args.get("api_key"))
        frappe.db.set_single_value("Leaf Procurement Settings", "api_secret", args.get("api_secret"))
        frappe.db.set_single_value("Leaf Procurement Settings", "lot_size", args.get("lot_size"))
        frappe.db.set_single_value("Leaf Procurement Settings", "barcode_length", args.get("barcode_length"))

        values = {
            "company_check": True,
            "fiscal_year": True,
            "warehouse": True,
            "quota_setup": True,
            "item": True,
            "item_grade": True,
            "item_sub_grade": True,
            "item_grade_price": True,
            "bale_status": True,
            "reclassification_grade": True,
            "transport_type": True
        }
        # Trigger sync down to fetch initial data
        print("✅ Triggering sync down to fetch initial data...")
        frappe.enqueue(
            method=sync_down_worker,
            queue="long",
            values=values,
            user=frappe.session.user
        )
    else:
        print("❌ Failed to connect to the server. Please check your API credentials and server URL.")
        raise Exception("Authentication failed while connecting to the server.")
    
    
    

def is_frappe_api_key_valid(base_url, api_key, api_secret):
    try:
        headers = {
            "Authorization": f"token {api_key}:{api_secret}"
        }
        response = requests.get(f"{base_url}/api/method/frappe.auth.get_logged_user", headers=headers)

        if response.status_code == 200:
            print("✅ API credentials are valid.")
            print("Logged in as:", response.json().get("message"))
            return True
        else:
            print("❌ API credentials are invalid.")
            print("Status:", response.status_code)
            print("Response:", response.text)
            return False
    except Exception as e:
        print("Error:", e)
        return False

def after_setup():
    # You can use frappe.get_doc("Domain Settings").set(...)
    frappe.logger().info("Sowaan Custom setup completed.")
