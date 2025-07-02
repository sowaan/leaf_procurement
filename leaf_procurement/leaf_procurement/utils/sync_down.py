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
def sync_down_worker(values: dict):
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
		register_local_instance(base_url, headers, settings.location_warehouse)

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
		url = f"{base_url}/api/resource/{doctype}?fields=['*']&limit_page_length=1000000"
		response = requests.get(url, headers=headers)

		if response.status_code != 200:
			msg = response.json().get("message", response.text)
			frappe.throw(_("❌ Failed to fetch {0}: {1}").format(doctype, msg))

		data = response.json().get("data", [])

		if len(data) > 20:
			process_sync(doctype, data)
			# frappe.enqueue(
			# 	"leaf_procurement.leaf_procurement.doctype.leaf_procurement_sync_tool.leaf_procurement_sync_tool.process_sync",
			# 	queue='default',
			# 	doctype=doctype,
			# 	data=data
			# )
			frappe.msgprint(_(f"Queued sync for {doctype} in background."))
		else:
			from leaf_procurement.leaf_procurement.doctype.leaf_procurement_sync_tool.leaf_procurement_sync_tool import process_sync
			process_sync(doctype, data)
			frappe.msgprint(_(f"✅ Synced {len(data)} records for {doctype}."))

	except Exception:
		frappe.log_error(traceback.format_exc(), f"❌ Sync Down Failed - {doctype}")
		

def process_sync(doctype, data):
	settings = frappe.get_doc("Leaf Procurement Settings")
	headers = {
		"Authorization": f"token {settings.get('api_key')}:{settings.get('api_secret')}",
		"Content-Type": "application/json"
	}

	doctype_handlers = {
		"Company": create_company,
		"Fiscal Year": create_fiscal_year,
		"Warehouse": create_warehouse,
		"Quota Setup": create_quota_setup,
		"Item": create_item,
		"Item Grade": create_item_grade,
		"Item Sub Grade": create_item_sub_grade,
		"Item Grade Price": create_item_grade_price,
		"Bale Status": create_bale_status,
		"Reclassification Grade": create_reclassification_grade,
		"Transport Type": create_transport_type,
	}

	handler = doctype_handlers.get(doctype)
	if handler:
		handler(settings, headers, data)
	else:
		frappe.log_error(f"No handler for Doctype: {doctype}", "❌ Unhandled Doctype")
