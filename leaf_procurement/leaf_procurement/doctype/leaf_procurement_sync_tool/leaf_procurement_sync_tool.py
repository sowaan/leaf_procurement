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
	create_quota_setup,
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
			("quota_setup", "Quota Setup"),
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
				url = f'{settings.instance_url}/api/resource/{doctype}?fields=["*"]&limit_page_length=1000000'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if len(data) > 20:
						frappe.enqueue(
							"leaf_procurement.leaf_procurement.doctype.leaf_procurement_sync_tool.leaf_procurement_sync_tool.process_sync",
							queue='default',
							doctype=doctype,
							data=data
						)
						frappe.msgprint(_(f"Sync for {doctype} is queued in the background."))
					else:
						process_sync(doctype, data)

						frappe.msgprint(_(f"Synced {len(data)} records for {doctype}."))
				else:
					frappe.throw(_("Failed to sync {0}: {1}").format(doctype, response.text))
	except Exception as e:
		frappe.log_error(str(e), "Sync Down Error")

def process_sync(doctype, data):
	settings = frappe.get_doc("Leaf Procurement Settings")
	headers = {
		"Authorization": f"token {settings.get('api_key')}:{settings.get('api_secret')}",
		"Content-Type": "application/json"
	}
	if doctype == "Company":
		create_company(settings, headers, data)
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
			("bale_audit", "Bale Audit"),
			("bale_registration", "Bale Registration"),
			("purchase_invoice", "Purchase Invoice"),
			("goods_receiving_note", "Goods Receiving Note"),
			("goods_transfer_note", "Goods Transfer Note"),
		]

		print(f"Syncing up data to the server... {doctypes}")

		for field, doctype in doctypes:
			if not doc.get(field): continue

			print(f"Syncing from {doctype} to server...")
			url = f'{settings.instance_url}/api/resource/{doctype}'
			data = frappe.get_all(doctype, filters={"custom_is_sync": 0, 'docstatus': ['<', 2]}, pluck='name')
			print(f"\n\n--------Data Variable: {data} to server...\n\n")
			for name in data:
				doc_data = frappe.get_doc(doctype, name)
				if doctype == "Bale Registration":
					doc_data.check_validations = 0
					doc_data.day_setup = ""

				doc_data = json.loads(doc_data.as_json())
				doc_data["skip_autoname"] = True
				doc_data["__islocal"] = 0
				doc_data["servername"] = name
				print(f"Syncing {doctype} record")
				response = requests.post(url, headers=headers, json=doc_data)
				print(doctype, name, 'custom_is_sync', "Want to check save record values")
				if response.status_code == 200 or response.status_code == 201:
					frappe.db.set_value(doctype, name, 'custom_is_sync', 1)
					frappe.msgprint({
						'title': _('Sync Successful'),
						'message': _(f"Synced record {doc_data['name']} for {doctype}.")
					})
				else:
					print(f"Failed to sync {doctype} {doc_data['name']}: {response.text}")
					frappe.log_error(response.text, f"Failed to sync {doctype} {doc_data['name']}")
	except Exception as e:
		frappe.log_error(str(e), "Sync Up Error",)
