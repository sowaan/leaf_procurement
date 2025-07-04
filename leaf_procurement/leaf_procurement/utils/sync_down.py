import json
import traceback
import requests
from datetime import datetime
from frappe import _  # for translations

import frappe  # type: ignore
from frappe import safe_decode # type: ignore
from frappe.utils import now # type: ignore
from leaf_procurement.api_functions import (
	create_company,
	create_fiscal_year,
	create_warehouse,
	create_quota_setup,
	create_item,
	create_item_grade,
	create_item_sub_grade,
	create_item_grade_price,
	create_bale_status,
	create_reclassification_grade,
	create_transport_type
)
def sync_down_worker(values: dict, user=None):
	try:
		settings = frappe.get_cached_doc("Leaf Procurement Settings")
		base_url = settings.instance_url.rstrip('/')

		if not (settings.api_key and settings.api_secret and base_url):
			frappe.throw(_("Missing API credentials or Instance URL in Leaf Procurement Settings."))

		headers = {
			"Authorization": f"token {settings.api_key}:{settings.api_secret}",
			"Content-Type": "application/json"
		}

		# ✅ Register the local server instance
		#register_local_instance(base_url, headers, settings.location_warehouse)

		# ✅ Define the doctypes to sync down
		doctypes = {
			"company_check": "Company",
			"fiscal_year": "Fiscal Year",
			"warehouse": "Warehouse",
			"quota_setup": "Quota Setup",
			"item": "Item",
			"item_grade": "Item Grade",
			"item_sub_grade": "Item Sub Grade",
			"item_grade_price": "Item Grade Price",
			"bale_status": "Bale Status",
			"reclassification_grade": "Reclassification Grade",
			"transport_type": "Transport Type",
		}

		for field, doctype in doctypes.items():
			if not values.get(field):
				continue
			sync_down_records(doctype, base_url, headers)

		frappe.publish_realtime("sync_complete", {"doctype": "All"}, user=frappe.session.user)
		frappe.msgprint(_("✔️ Sync down complete."))

	except Exception:
		frappe.log_error(traceback.format_exc(), "❌ Sync Down Worker Error")


def register_local_instance(base_url: str, headers: dict, location: str):
	try:
		users = frappe.get_all("User", fields=["name", "email", "enabled", "creation"])

		# Convert datetime to ISO string
		for user in users:
			if isinstance(user.get("creation"), datetime):
				user["creation"] = user["creation"].isoformat()

		payload = {
			"api_key": headers["Authorization"].split(" ")[-1].split(":")[0],
			"location": location,
			"users": users,
			"sync_down_date": now(),
			"sync_up_date": None,
		}

		url = f"{base_url}/api/method/leaf_procurement.api_functions.local_server_instance"
		response = requests.post(url, headers=headers, json=payload)

		if response.status_code not in [200, 201]:
			msg = response.json().get("message", response.text)
			frappe.log_error(msg, "❌ Error registering local instance")

	except Exception:
		frappe.log_error(traceback.format_exc(), "❌ Error registering local instance")


def sync_down_records(doctype: str, base_url: str, headers: dict):
	try:
		params = {
			"fields": json.dumps(["*"]),  # This becomes '["*"]'
			"limit_page_length": 1000000
		}

		url = f"{base_url}/api/resource/{doctype}"
		response = requests.get(url, headers=headers, params=params)		
		
		msg = response.text
		status = response.status_code

		if status == 200 or status=="200":
			data = response.json().get("data", [])
			process_sync(doctype, data)
		else:
			frappe.log_error(f"❌ Sync Down Error - {doctype}", f"response: {response}\nstatus:{response.status_code}\nmessage: {msg}")
	except Exception:
		frappe.log_error(traceback.format_exc(), f"❌ Sync Down Failed - {doctype}")
		
def process_sync(doctype, data):
	settings = frappe.get_doc("Leaf Procurement Settings")
	headers = {
		"Authorization": f"token {settings.get('api_key')}:{settings.get('api_secret')}",
		"Content-Type": "application/json"
	}

	if doctype == "Company":
		create_company(settings, headers, data)
	if doctype == "Fiscal Year":
		create_fiscal_year(settings, headers, data)
	if doctype == "Warehouse":
		create_warehouse(settings, headers, data)
	if doctype == "Quota Setup":
		create_quota_setup(settings, headers, data)
	if doctype == "Item":
		create_item(settings, headers, data)
	if doctype == "Item Grade":
		create_item_grade(settings, headers, data)
	if doctype == "Item Sub Grade":
		create_item_sub_grade(settings, headers, data)
	if doctype == "Item Grade Price":
		create_item_grade_price(settings, headers, data)
	if doctype == "Bale Status":
		create_bale_status(settings, headers, data)
	if doctype == "Reclassification Grade":
		create_reclassification_grade(settings, headers, data)
	if doctype == "Transport Type":
		create_transport_type(settings, headers, data)
