import frappe
import requests
from frappe import _
import json
from leaf_procurement.leaf_procurement.api.bale_weight_utils import ensure_batch_exists


def create_company(settings, headers, data):
	"""Update company records with the received data."""
	created = []
	skipped = []
	errors = []

	for item in data:
		if item.get("default_letter_head"):
			create_letterHead(settings, headers, item.get("default_letter_head"))
		if not frappe.db.exists("Company", item['name']):
			try:
				doc = frappe.new_doc("Company")
				doc.name = item.get('name', item['name'])
				doc.company_name = item['name']
				doc.abbr = item.get('abbr', item['name'])
				doc.default_currency = item.get('default_currency', 'USD')
				doc.country = item.get('country', 'United States')
				doc.insert(ignore_permissions=True)
				# create_company_accounts(settings, headers, item['name'])
				# doc.update(item)
				doc.save(ignore_permissions=True)
				created.append(doc.name)
				frappe.db.commit()
				frappe.logger().info(f"Created Company: {doc.name}")
			except Exception as e:
				frappe.db.rollback()
				errors.append(f"Error creating Company {item['name']}: {e}")
		else:
			skipped.append(item['name'])

	message = f"Company records updated.<br>Created: {len(created)}<br>Skipped: {len(skipped)}"
	if errors:
		message += f"<br>Errors: {len(errors)}"
		frappe.log_error("\n".join(errors), "Company Sync Errors")

	frappe.msgprint(_(message))

def create_company_accounts(settings, headers, company_name):
	"""Create company accounts for the given company name."""
	if not frappe.db.exists("Account", {"company": company_name}):
		try:
			url = f'{settings.get("instance_url")}/api/resource/Account?fields=["*"]&filters=[["Account","company", "=", "{company_name}"]]'
			print(f"Fetching accounts for company: {url}")
			response = requests.get(url, headers=headers)
			if response.status_code == 200:
				data = response.json().get("data", [])
				if data:
					data = data[0]
					doc = frappe.new_doc("Account")
					doc.update(data)
					doc.insert(ignore_permissions=True)
					frappe.db.commit()
			else:
				frappe.throw(_("Failed to fetch data for Account: {0}").format(response.text))
		except Exception as e:
			frappe.db.rollback()
			frappe.throw(_("Error fetching data for Account: {0}").format(e))


def create_letterHead(settings, headers, name):
	"""Create a Letter Head with the given name."""
	if not frappe.db.exists("Letter Head", name):
		try:
			url = f'{settings.get("instance_url")}/api/resource/Letter Head?fields=["*"]&filters=[["name", "=", "{name}"]]'
			response = requests.get(url, headers=headers)
			if response.status_code == 200:
				data = response.json().get("data", [])
				if data:
					data = data[0]
					doc = frappe.new_doc("Letter Head")
					doc.update(data)
					doc.insert(ignore_permissions=True)
			else:
				frappe.throw(_("Failed to fetch data for Letter Head: {0}").format(response.text))
		except Exception as e:
			frappe.throw(_("Error fetching data for Letter Head: {0}").format(e))


def create_warehouse(settings, headers, data):
	"""Update warehouse records with the received data."""
	created = []
	skipped = []
	errors = []

	for item in data:
		if not frappe.db.exists("Warehouse", item['name']):
			try:
				url = f'{settings.get("instance_url")}/api/resource/Warehouse?fields=["*"]'
				response = requests.get(url, headers=headers)
				print(f"Response status code: {response}")
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Warehouse")
						doc.skip_autoname = True
						doc.servername = item.get("servername", item['name'])
						doc.name = item.get('name', item['name'])
						doc.warehouse_name = item.get('warehouse_name', item['name'])
						doc.custom_short_code = item.get('custom_short_code', '')
						doc.company = item.get('company', 'Default Company')
						doc.set("__islocal", False)
						doc.db_insert()
						created.append(doc.name)
						frappe.db.commit()
				else:
					frappe.throw(_("Failed to fetch data for Warehouse: {0}").format(response.text))
			except Exception as e:
				frappe.db.rollback()
				errors.append(f"Error creating Warehouse {item['name']}: {e}")
		else:
			skipped.append(item['name'])
	message = f"Warehouse records updated.<br>Created: {len(created)}<br>Skipped: {len(skipped)}"


	if errors:
		frappe.log_error("\n".join(errors), "Warehouse Sync Errors")

	frappe.msgprint(_(message))


def create_quota_setup(settings, headers, data):
	"""Update quota setup records with the received data."""
	created = []
	skipped = []
	errors = []

	for item in data:
		if not frappe.db.exists("Quota Setup", item['name']):
			try:
				url = f'{settings.get("instance_url")}/api/resource/Quota Setup?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Quota Setup")
						doc.skip_autoname = True
						doc.servername = item.get("servername", item['name'])
						doc.update(item)
						doc.insert(ignore_permissions=True)
						created.append(doc.name)
						frappe.db.commit()
				else:
					frappe.throw(_("Failed to fetch data for Quota Setup: {0}").format(response.text))
			except Exception as e:
				frappe.db.rollback()
				errors.append(f"Error creating Quota Setup {item['name']}: {e}")
		else:
			skipped.append(item['name'])
	message = f"Quota Setup records updated.<br>Created: {len(created)}<br>Skipped: {len(skipped)}"

	if errors:
		frappe.log_error("\n".join(errors), "Quota Setup Sync Errors")

	frappe.msgprint(_(message))


def create_item(settings, headers, data):
	"""Update item records with the received data."""
	created = []
	skipped = []
	errors = []

	for item in data:
		if not frappe.db.exists("Item", item['name']):
			try:
				url = f'{settings.get("instance_url")}/api/resource/Item?fields=["*"]'
				print(f"Fetching accounts for company: {url}")
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Item")
						doc.update(item)
						doc.insert(ignore_permissions=True)
						created.append(doc.name)
						frappe.db.commit()
				else:
					frappe.throw(_("Failed to fetch data for Item: {0}").format(response.text))
			except Exception as e:
				frappe.db.rollback()
				errors.append(f"Error creating Item {item['name']}: {e}")
		else:
			skipped.append(item['name'])
	message = f"Item records updated.<br>Created: {len(created)}<br>Skipped: {len(skipped)}"

	if errors:
		frappe.log_error("\n".join(errors), "Item Sync Errors")

	frappe.msgprint(_(message))


def create_item_grade(settings, headers, data):
	"""Update item grade records with the received data."""
	errors = []

	for item in data:
		if not frappe.db.exists("Item Grade", item['name']):
			try:
				url = f'{settings.get("instance_url")}/api/resource/Item Grade?fields=["*"]'
				print(f"Fetching accounts for company: {url}")
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Item Grade")
						doc.name = item.get('name', item['name'])
						doc.item_grade_name = item.get('item_grade_name', item['name'])
						doc.rejected_grade = item.get('rejected_grade', False)
						doc.insert(ignore_permissions=True)
						frappe.db.commit()
				else:
					frappe.throw(_("Failed to fetch data for Item Grade: {0}").format(response.text))
			except Exception as e:
				frappe.db.rollback()
				errors.append(f"Error creating Item Grade {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Item Grade Sync Errors")


def create_item_sub_grade(settings, headers, data):
	"""Update item sub-grade records with the received data."""
	errors = []

	for item in data:
		if not frappe.db.exists("Item Sub Grade", item['name']):
			try:
				url = f'{settings.get("instance_url")}/api/resource/Item Sub Grade?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Item Sub Grade")
						doc.name = item.get('name', item['name'])
						doc.item_grade = item.get('item_grade', item['name'])
						doc.item_sub_grade = item.get('item_sub_grade', item['name'])
						doc.insert(ignore_permissions=True)
						frappe.db.commit()
				else:
					frappe.throw(_("Failed to fetch data for Item Sub Grade: {0}").format(response.text))
			except Exception as e:
				frappe.db.rollback()
				errors.append(f"Error creating Item Sub Grade {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Item Sub Grade Sync Errors")


def create_item_grade_price(settings, headers, data):
	"""Update item grade price records with the received data."""
	errors = []

	for item in data:
		if not frappe.db.exists("Item Grade Price", item['name']):
			try:
				url = f'{settings.get("instance_url")}/api/resource/Item Grade Price?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Item Grade Price")
						doc.skip_autoname = True
						doc.servername = item.get("servername", item['name'])
						doc.name = item.get('name', item['name'])
						doc.company = item.get('company', item['name'])
						doc.location_warehouse = item.get('location_warehouse', 'Default Warehouse')
						doc.item = item.get('item', item['name'])
						doc.item_grade = item.get('item_grade', item['name'])
						doc.item_sub_grade = item.get('item_sub_grade', item['name'])
						doc.price_list = item.get('price_list', 'Standard Selling')
						doc.uom = item.get('uom', 'Nos')
						doc.rate = item.get('rate', 0.0)
						doc.insert(ignore_permissions=True)
						frappe.db.commit()
				else:
					frappe.throw(_("Failed to fetch data for Item Grade Price: {0}").format(response.text))
			except Exception as e:
				frappe.db.rollback()
				errors.append(f"Error creating Item Grade Price {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Item Grade Price Sync Errors")


def create_bale_status(settings, headers, data):
	"""Update bale status records with the received data."""
	errors = []

	for item in data:	
		if not frappe.db.exists("Bale Status", item['name']):
			try:
				url = f'{settings.get("instance_url")}/api/resource/Bale Status?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Bale Status")
						doc.name = item.get('name', item['name'])
						doc.bale_status_name = item.get('bale_status_name', item['name'])
						doc.default_status = item.get('default_status', False)
						doc.insert(ignore_permissions=True)
						frappe.db.commit()
				else:
					frappe.throw(_("Failed to fetch data for Bale Status: {0}").format(response.text))
			except Exception as e:
				frappe.db.rollback()
				errors.append(f"Error creating Bale Status {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Bale Status Sync Errors")


def create_reclassification_grade(settings, headers, data):
	"""Update reclassification grade records with the received data."""
	errors = []

	for item in data:
		if not frappe.db.exists("Reclassification Grade", item['name']):
			try:
				url = f'{settings.instance_url}/api/resource/Reclassification Grade?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Reclassification Grade")
						doc.name = item.get('name', item['name'])
						doc.reclassification_grade_name = item.get('reclassification_grade_name', item['name'])
						doc.insert(ignore_permissions=True)
						frappe.db.commit()
				else:
					frappe.throw(_("Failed to fetch data for Reclassification Grade: {0}").format(response.text))
			except Exception as e:
				frappe.db.rollback()
				errors.append(f"Error creating Reclassification Grade {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Reclassification Grade Sync Errors")

def create_transport_type(settings, headers, data):
	"""Update transport type records with the received data."""
	errors = []

	for item in data:
		if not frappe.db.exists("Transport Type", item['name']):
			try:
				url = f'{settings.get("instance_url")}/api/resource/Transport Type?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Transport Type")
						doc.name = item.get('name', item['name'])
						doc.transport_type = item.get('transport_type', item['name'])
						doc.insert(ignore_permissions=True)
						frappe.db.commit()
				else:
					frappe.throw(_("Failed to fetch data for Transport Type: {0}").format(response.text))
			except Exception as e:
				frappe.db.rollback()
				errors.append(f"Error creating Transport Type {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Transport Type Sync Errors")


@frappe.whitelist()
def update_bale_status(purchase_invoice):
    # Step 1: Fetch Bale Weight Info
    result = frappe.get_all(
        'Bale Weight Info',
        filters={'purchase_invoice': purchase_invoice},
        fields=['name', 'bale_registration_code'],
        limit_page_length=1
    )

    if result:
        bale_registration_code = result[0].get('bale_registration_code')

        # Step 2: Update Bale Registration status
        if bale_registration_code:
            frappe.db.set_value('Bale Registration', bale_registration_code, 'bale_status', 'Completed')
            return {'status': 'success', 'updated': bale_registration_code}

    return {'status': 'no_bale_found'}


@frappe.whitelist()
def supplier(supplier):
	if isinstance(supplier, str):
		supplier = json.loads(supplier)

	supplier_name = supplier.get("name")
	if not supplier_name:
		frappe.throw(_("Supplier name is required."))

	# ✅ Check if the supplier already exists
	if frappe.db.exists("Supplier", supplier_name):
		return supplier_name

	doc = frappe.new_doc("Supplier")
	doc.update(supplier)
	doc.insert()
	frappe.db.commit()
	return doc.name


@frappe.whitelist()
def driver(driver):
	if isinstance(driver, str):
		driver = json.loads(driver)

	driver_name = driver.get("name")
	if not driver_name:
		frappe.throw(_("Driver name is required."))

	if frappe.db.exists("Driver", driver_name):
		return driver_name

	doc = frappe.new_doc("Driver")
	doc.update(driver)
	doc.insert()
	frappe.db.commit()
	return doc.name


@frappe.whitelist()
def bale_audit(bale_audit):
	if isinstance(bale_audit, str):
		bale_audit = json.loads(bale_audit)

	doc = frappe.new_doc("Bale Audit")
	doc.update(bale_audit)
	doc.insert()
	frappe.db.commit()
	return doc.name


@frappe.whitelist()
def bale_registration(bale_registration):
	if isinstance(bale_registration, str):
		bale_registration = json.loads(bale_registration)

	bale_name = bale_registration.get("name")
	if not bale_name:
		frappe.throw(_("Bale Registration name is required."))
	
	if frappe.db.exists("Bale Registration", bale_name):
		return bale_name

	doc = frappe.new_doc("Bale Registration")
	doc.update(bale_registration)
	doc.insert()
	frappe.db.commit()
	return doc.name


@frappe.whitelist()
def purchase_invoice(purchase_invoice):
	if isinstance(purchase_invoice, str):
		purchase_invoice = json.loads(purchase_invoice)

	purchase_name = purchase_invoice.get("name")
	if not purchase_name:
		frappe.throw(_("Purchase Invoice name is required."))

	if frappe.db.exists("Purchase Invoice", purchase_name):
		return purchase_name

	invoice = frappe.new_doc("Purchase Invoice")
	invoice.name = purchase_name
	invoice.skip_autoname = True
	invoice.servername = purchase_invoice.get("servername", purchase_name)
	invoice.return_against = purchase_invoice.get("return_against")
	invoice.update_outstanding_for_self = purchase_invoice.get("update_outstanding_for_self", 0)
	invoice.supplier = purchase_invoice.get("supplier")
	invoice.posting_date = purchase_invoice.get("posting_date")
	invoice.company = purchase_invoice.get("company")
	invoice.set_posting_time = purchase_invoice.get("set_posting_time")
	invoice.update_stock = purchase_invoice.get("update_stock")
	invoice.set_warehouse = purchase_invoice.get("warehouse")
	invoice.rejected_warehouse = purchase_invoice.get("rejected_warehouse")
	invoice.due_date = purchase_invoice.get("due_date")
	invoice.custom_barcode = purchase_invoice.get("custom_barcode")
	invoice.currency = purchase_invoice.get("currency")
	invoice.conversion_rate = purchase_invoice.get("conversion_rate")
	invoice.is_return = purchase_invoice.get("is_return")
	invoice.buying_price_list = purchase_invoice.get("buying_price_list")
	invoice.price_list_currency = purchase_invoice.get("price_list_currency")
	invoice.plc_conversion_rate = purchase_invoice.get("plc_conversion_rate")
	invoice.custom_short_code = purchase_invoice.get("custom_short_code")
	invoice.docstatus = purchase_invoice.get("docstatus", 0)
	invoice.is_paid = purchase_invoice.get("is_paid", 0)
	invoice.apply_tds = purchase_invoice.get("apply_tds", 0)
	# invoice.custom_rejected_items = purchase_invoice.get("custom_rejected_items", [])

	for rejected in purchase_invoice.get("custom_rejected_items", []):
		if rejected["batch_no"]:
			ensure_batch_exists(rejected.get("batch_no"), rejected.get("item_code"), rejected.get("weight"))
		invoice.append("custom_rejected_items", rejected)
 

	for detail in purchase_invoice.get("items"):
		if detail["batch_no"]:
			ensure_batch_exists(detail.get("batch_no"), detail.get("item_code"), detail.get("weight"))
		item_data = {
			"item_code": detail.get("item_code"),
			"qty": detail.get("qty"),
			"rate": detail.get("rate"),
			"uom": detail.get("uom"),
			"description": detail.get("description"),
		}

		# Only include optional fields if they have a meaningful value
		optional_fields = [
			"received_qty", "warehouse", "use_serial_batch_fields",
			"batch_no", "lot_number", "grade", "sub_grade"
		]

		for key in optional_fields:
			value = detail.get(key)
			if value:
				item_data[key] = value
		invoice.append("items", item_data)   

	invoice.insert()
	frappe.db.commit()
	return invoice.name


@frappe.whitelist()
def goods_transfer_note(goods_transfer_note):
	if isinstance(goods_transfer_note, str):
		goods_transfer_note = json.loads(goods_transfer_note)

	goods_transfer_note_name = goods_transfer_note.get("name")
	if not goods_transfer_note_name:
		frappe.throw(_("Goods Transfer Note name is required."))

	if frappe.db.exists("Goods Transfer Note", goods_transfer_note_name):
		return goods_transfer_note_name

	doc = frappe.new_doc("Goods Transfer Note")
	doc.update(goods_transfer_note)
	doc.insert()
	frappe.db.commit()
	return doc.name


@frappe.whitelist()
def goods_receiving_note(goods_receiving_note):
	if isinstance(goods_receiving_note, str):
		goods_receiving_note = json.loads(goods_receiving_note)

	goods_receiving_note_name = goods_receiving_note.get("name")
	if not goods_receiving_note_name:
		frappe.throw(_("Goods Receiving Note name is required."))
	
	if frappe.db.exists("Goods Receiving Note", goods_receiving_note_name):
		return goods_receiving_note_name

	doc = frappe.new_doc("Goods Receiving Note")
	doc.update(goods_receiving_note)
	doc.insert()
	frappe.db.commit()
	return doc.name



