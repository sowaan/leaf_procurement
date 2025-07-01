# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import requests
import traceback
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
def sync_down(values=None):
	if not values: return

	if isinstance(values, str):
		values = json.loads(values)
	
	try:
		"""Sync down data from the server to the local database."""
		settings = frappe.get_doc("Leaf Procurement Settings")
		if not settings.instance_url:
			frappe.throw(_("Instance URL is not set in Leaf Procurement Settings."))
		if not settings.api_key:
			frappe.throw(_("API Key is not set in Leaf Procurement Settings."))
		if not settings.api_secret:
			frappe.throw(_("API Secret is not set in Leaf Procurement Settings."))

		#doc = frappe.get_doc("Leaf Procurement Sync Tool")
		parsedurl = settings.instance_url.rstrip('/')

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
			#if sync down check for current doctype is false continue to next record
			if not values.get(field): continue

			url = f'{parsedurl}/api/resource/{doctype}?fields=["*"]&limit_page_length=1000000'
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
def sync_up(values=None):
	if not values: return

	if isinstance(values, str):
		values = json.loads(values)
	
	try:
		# Load settings
		settings = frappe.get_doc("Leaf Procurement Settings")
		if not settings.instance_url:
			frappe.throw(_("Instance URL is not set in Leaf Procurement Settings."))
		if not settings.api_key:
			frappe.throw(_("API Key is not set in Leaf Procurement Settings."))
		if not settings.api_secret:
			frappe.throw(_("API Secret is not set in Leaf Procurement Settings."))

		#doc = frappe.get_doc("Leaf Procurement Sync Tool")
		parsedurl = settings.instance_url.rstrip('/')

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
			("goods_transfer_note", "Goods Transfer Note"),
			("goods_receiving_note", "Goods Receiving Note"),
		]

		for field, doctype in doctypes:
			if not values.get(field): continue

			url = f"{parsedurl}/api/method/leaf_procurement.api_functions.{field}"
			print(f"Syncing {doctype} to {url}")
			try:
				data = frappe.get_all(
					doctype,
					filters={"custom_is_sync": 0, "docstatus": ["<", 2]},
					pluck="name"
				)
			except Exception as e:
				frappe.log_error(traceback.format_exc(), f"Failed to fetch {doctype}")
				continue

			for name in data:
				print(f"Syncing {doctype}: {name}")
				try:
					doc_data = frappe.get_doc(doctype, name)
					# Special handling per doctype
					if doctype == "Bale Registration":
						doc_data.check_validations = 0
						doc_data.day_setup = ""

					# Prepare data for sync
					doc_data = json.loads(doc_data.as_json())
					doc_data["skip_autoname"] = True
					doc_data["__islocal"] = 0
					doc_data["servername"] = name

					# Send request
					response = requests.post(url, headers=headers, json={field: doc_data})

					if response.status_code in [200, 201]:
						frappe.db.set_value(doctype, name, "custom_is_sync", 1)
						if doctype == "Supplier":
							contactUrl = f"{settings.instance_url}/api/resource/Contact"
							create_supplier_contact(contactUrl, headers, doc_data)
						print(f"✅ Synced {doctype}: {name}")
					else:
						try:
							error_msg = response.json().get("message", response.text)
						except:
							error_msg = response.text
						frappe.log_error(f"❌ Failed to sync {doctype} ", error_msg)

				except Exception as e:
					frappe.log_error(f"❌ Exception syncing {doctype} {name}", traceback.format_exc())
	except Exception as e:
		frappe.log_error("❌ Sync Up Failed", traceback.format_exc())



def create_supplier_contact(url, headers, supplier_doc):
	if supplier_doc.get("supplier_primary_contact"):
		contact = frappe.get_doc("Contact", supplier_doc.get("supplier_primary_contact"))
		if contact.custom_is_sync:
			print(f"⚠️ Contact {contact.name} already synced. Skipping...")
			return

		contact_data = json.loads(contact.as_json())
		contact_data["skip_autoname"] = True
		contact_data["__islocal"] = 0
		contact_data["servername"] = contact.name
		response = requests.post(url, headers=headers, json=contact_data)

		if response.status_code in [200, 201]:
			print(f"✅ Synced Supplier Contact: {contact.name}")
			frappe.db.set_value("Contact", contact.name, "custom_is_sync", 1)
		else:
			try:
				error_msg = response.json().get("message", response.text)
			except:
				error_msg = response.text
			frappe.log_error(f"❌ Failed to sync Supplier Contact {contact.name}", error_msg)


def ensure_batch_exists(url, headers, batch_no, item_code, qty):
	if batch_no:
		try:
			batch_url = f"{url}/api/resource/Batch"
			batch = frappe.get_doc("Batch", batch_no)
			# ✅ Only sync if not already synced
			if batch.custom_is_sync:
				print(f"⚠️ Batch {batch.name} already synced. Skipping...")
				return

			# Convert batch doc to a dictionary for JSON serialization
			batch_data = json.loads(batch.as_json())
			batch_data["skip_autoname"] = True
			batch_data["__islocal"] = 0
			batch_data["servername"] = batch_no

			response = requests.post(batch_url, headers=headers, json=batch_data)

			if response.status_code in [200, 201]:
				print(f"✅ Synced Batch: {batch.name}")
				# sync Serial and Batch Bundle
				# ser_and_batch_bundle_list = frappe.get_all(
				# 	"Serial and Batch Bundle",
				# 	filters=[["Serial and Batch Entry","batch_no","=",batch.name]],
				# 	pluck="name"
				# )
				# for bundle in ser_and_batch_bundle_list:
				# 	bundle_doc = frappe.get_doc("Serial and Batch Bundle", bundle)
				# 	bundle_data = json.loads(bundle_doc.as_json())
				# 	bundle_data["skip_autoname"] = True
				# 	bundle_data["__islocal"] = 0
				# 	bundle_data["servername"] = bundle_doc.name
				# 	response_bundle = requests.post(
				# 		f"{url}/api/resource/Serial and Batch Bundle",
				# 		headers=headers,
				# 		json=bundle_data
				# 	)
				# 	if response_bundle.status_code not in [200, 201]:
				# 		try:
				# 			error_msg = response_bundle.json().get("message", response_bundle.text)
				# 		except:
				# 			error_msg = response_bundle.text
				# 		frappe.log_error(error_msg, f"❌ Failed to sync Serial and Batch Bundle {bundle_doc.name}")
						
				frappe.db.set_value("Batch", batch.name, "custom_is_sync", 1)
			else:
				try:
					error_msg = response.json().get("message", response.text)
				except:
					error_msg = response.text
				frappe.log_error(f"❌ Failed to sync Batch {batch.name}", error_msg)

		except Exception as e:
			frappe.log_error(f"❌ Exception ensuring Batch {batch_no} for Item {item_code} with Qty {qty}", traceback.format_exc())
