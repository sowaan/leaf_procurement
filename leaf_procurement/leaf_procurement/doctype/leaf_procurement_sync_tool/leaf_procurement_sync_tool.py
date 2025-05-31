# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import requests
import json
from leaf_procurement.api_functions import (
	create_company,
	create_warehouse,
	create_item,
	create_item_grade,
	create_item_sub_grade,
	create_item_grade_price,
	create_bale_status,
	create_reclassification_grade,
	create_transport_type
)


class LeafProcurementSyncTool(Document):
	pass

@frappe.whitelist()
def sync_down():
	try:
		"""Sync down data from the server to the local database."""
		settings = frappe.get_doc("Leaf Procurement Settings")
		if not settings.instance_url:
			frappe.throw(_("Instance URL is not set in Leaf Procurement Settings."))
		if not settings.api_key:
			frappe.throw(_("API Key is not set in Leaf Procurement Settings."))
		if not settings.api_secret:
			frappe.throw(_("API Secret is not set in Leaf Procurement Settings."))

		doc = frappe.get_doc("Leaf Procurement Sync Tool")

		headers = {
			"Authorization": f"token {settings.api_key}:{settings.api_secret}",
			"Content-Type": "application/json"
		}

		doctypes = [
			("company_check", "Company"),
			("warehouse", "Warehouse"),
			("item", "Item"),
			("item_grade", "Item Grade"),
			("item_sub_grade", "Item Sub Grade"),
			("item_grade_price", "Item Grade Price"),
			("bale_status", "Bale Status"),
			("reclassification_grade", "Reclassification Grade"),
			("transport_type", "Transport Type")
		]

		for field, doctype in doctypes:
			if doc.get(field):
				print(f"Syncing from {doc.get(field)} to {doctype}...")
				url = f'{settings.instance_url}/api/resource/{doctype}?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if doctype == "Company":
						create_company(settings, headers, data)
					if doctype == "Warehouse":
						create_warehouse(settings, headers, data)
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

					frappe.msgprint(_(f"Synced {len(data)} records for {doctype}."))
				else:
					frappe.throw(_("Failed to sync {0}: {1}").format(doctype, response.text))
	except Exception as e:
		frappe.log_error(str(e), "Sync Down Error")


@frappe.whitelist()
def sync_up():
	try:
		"""Sync up data from the local database to the server."""
		settings = frappe.get_doc("Leaf Procurement Settings")
		if not settings.instance_url:
			frappe.throw(_("Instance URL is not set in Leaf Procurement Settings."))
		if not settings.api_key:
			frappe.throw(_("API Key is not set in Leaf Procurement Settings."))
		if not settings.api_secret:
			frappe.throw(_("API Secret is not set in Leaf Procurement Settings."))

		doc = frappe.get_doc("Leaf Procurement Sync Tool")

		headers = {
			"Authorization": f"token {settings.api_key}:{settings.api_secret}",
			"Content-Type": "application/json"
		}

		doctypes = [
			("supplier", "Supplier"),
			("driver", "Driver"),
			("bale_registration", "Bale Registration"),
			("purchase_invoice", "Purchase Invoice"),
			("stock_entry", "Stock Entry")
		]

		for field, doctype in doctypes:
			if doc.get(field):
				print(f"Syncing from {doctype} to server...")
				url = f'{settings.instance_url}/api/resource/{doctype}'
				data = frappe.get_all(doctype, filters={"custom_is_sync": 0}, pluck='name')
				for name in data:
					doc_data = frappe.get_doc(doctype, name)
					if doctype == "Bale Registration":
						doc_data.check_validations == 0
					doc_data = json.loads(doc_data.as_json())
					print(f"Syncing {doctype} record: {doc_data}")
					response = requests.post(url, headers=headers, json=doc_data)
					if response.status_code == 200 or response.status_code == 201:
						print(doctype, name, 'custom_is_sync', "Want to check save record values")
						frappe.db.set_value(doctype, name, 'custom_is_sync', 1)
						frappe.msgprint(_(f"Synced record {doc_data['name']} for {doctype}."))
					else:
						frappe.throw(_("Failed to sync {0} {1}: {2}").format(doctype, doc_data['name'], response.text))
	except Exception as e:
		frappe.log_error(str(e), "Sync Up Error")
