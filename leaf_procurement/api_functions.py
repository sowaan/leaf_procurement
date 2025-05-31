import frappe
import requests
from frappe import _

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
				doc.company_name = item['name']
				doc.abbr = item.get('abbr', item['name'])
				doc.default_currency = item.get('default_currency', 'USD')
				doc.country = item.get('country', 'United States')
				doc.insert(ignore_permissions=True)
				# create_company_accounts(settings, headers, item['name'])
				# doc.update(item)
				doc.save(ignore_permissions=True)
				created.append(doc.name)
				frappe.logger().info(f"Created Company: {doc.name}")
			except Exception as e:
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
			url = f'{settings.instance_url}/api/resource/Account?fields=["*"]&filters=[["Account","company", "=", "{company_name}"]]'
			print(f"Fetching accounts for company: {url}")
			response = requests.get(url, headers=headers)
			if response.status_code == 200:
				data = response.json().get("data", [])
				if data:
					data = data[0]
					doc = frappe.new_doc("Account")
					doc.update(data)
					doc.insert(ignore_permissions=True)
			else:
				frappe.throw(_("Failed to fetch data for Account: {0}").format(response.text))
		except Exception as e:
			frappe.throw(_("Error fetching data for Account: {0}").format(e))


def create_letterHead(settings, headers, name):
	"""Create a Letter Head with the given name."""
	if not frappe.db.exists("Letter Head", name):
		try:
			url = f'{settings.instance_url}/api/resource/Letter Head?fields=["*"]&filters=[["name", "=", "{name}"]]'
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
	errors = []

	for item in data:
		if not frappe.db.exists("Warehouse", item['name']):
			try:
				url = f'{settings.instance_url}/api/resource/Warehouse?fields=["*"]'
				response = requests.get(url, headers=headers)
				print(f"Response status code: {response}")
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Warehouse")
						doc.warehouse_name = item.get('warehouse_name', item['name'])
						doc.custom_short_code = item.get('custom_short_code', '')
						doc.company = item.get('company', 'Default Company')
						doc.insert(ignore_permissions=True)
				else:
					frappe.throw(_("Failed to fetch data for Warehouse: {0}").format(response.text))
			except Exception as e:
				errors.append(f"Error creating Warehouse {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Warehouse Sync Errors")


def create_item(settings, headers, data):
	"""Update item records with the received data."""
	errors = []

	for item in data:
		if not frappe.db.exists("Item", item['name']):
			try:
				url = f'{settings.instance_url}/api/resource/Item?fields=["*"]'
				print(f"Fetching accounts for company: {url}")
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Item")
						doc.update(item)
						doc.insert(ignore_permissions=True)
				else:
					frappe.throw(_("Failed to fetch data for Item: {0}").format(response.text))
			except Exception as e:
				errors.append(f"Error creating Item {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Item Sync Errors")


def create_item_grade(settings, headers, data):
	"""Update item grade records with the received data."""
	errors = []

	for item in data:
		if not frappe.db.exists("Item Grade", item['name']):
			try:
				url = f'{settings.instance_url}/api/resource/Item Grade?fields=["*"]'
				print(f"Fetching accounts for company: {url}")
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Item Grade")
						doc.item_grade_name = item.get('item_grade_name', item['name'])
						doc.rejected_grade = item.get('rejected_grade', False)
						doc.insert(ignore_permissions=True)
				else:
					frappe.throw(_("Failed to fetch data for Item Grade: {0}").format(response.text))
			except Exception as e:
				errors.append(f"Error creating Item Grade {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Item Grade Sync Errors")


def create_item_sub_grade(settings, headers, data):
	"""Update item sub-grade records with the received data."""
	errors = []

	for item in data:
		if not frappe.db.exists("Item Sub Grade", item['name']):
			try:
				url = f'{settings.instance_url}/api/resource/Item Sub Grade?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Item Sub Grade")
						doc.item_grade = item.get('item_grade', item['name'])
						doc.item_sub_grade = item.get('item_sub_grade', item['name'])
						doc.insert(ignore_permissions=True)
				else:
					frappe.throw(_("Failed to fetch data for Item Sub Grade: {0}").format(response.text))
			except Exception as e:
				errors.append(f"Error creating Item Sub Grade {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Item Sub Grade Sync Errors")


def create_item_grade_price(settings, headers, data):
	"""Update item grade price records with the received data."""
	errors = []

	for item in data:
		if not frappe.db.exists("Item Grade Price", item['name']):
			try:
				url = f'{settings.instance_url}/api/resource/Item Grade Price?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Item Grade Price")
						doc.company = item.get('company', item['name'])
						doc.location_warehouse = item.get('location_warehouse', 'Default Warehouse')
						doc.item = item.get('item', item['name'])
						doc.item_grade = item.get('item_grade', item['name'])
						doc.item_sub_grade = item.get('item_sub_grade', item['name'])
						doc.price_list = item.get('price_list', 'Standard Selling')
						doc.uom = item.get('uom', 'Nos')
						doc.rate = item.get('rate', 0.0)
						doc.insert(ignore_permissions=True)
				else:
					frappe.throw(_("Failed to fetch data for Item Grade Price: {0}").format(response.text))
			except Exception as e:
				errors.append(f"Error creating Item Grade Price {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Item Grade Price Sync Errors")


def create_bale_status(settings, headers, data):
	"""Update bale status records with the received data."""
	errors = []

	for item in data:	
		if not frappe.db.exists("Bale Status", item['name']):
			try:
				url = f'{settings.instance_url}/api/resource/Bale Status?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Bale Status")
						doc.bale_status_name = item.get('bale_status_name', item['name'])
						doc.default_status = item.get('default_status', False)
						doc.insert(ignore_permissions=True)
				else:
					frappe.throw(_("Failed to fetch data for Bale Status: {0}").format(response.text))
			except Exception as e:
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
						doc.reclassification_grade_name = item.get('reclassification_grade_name', item['name'])
						doc.insert(ignore_permissions=True)
				else:
					frappe.throw(_("Failed to fetch data for Reclassification Grade: {0}").format(response.text))
			except Exception as e:
				errors.append(f"Error creating Reclassification Grade {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Reclassification Grade Sync Errors")

def create_transport_type(settings, headers, data):
	"""Update transport type records with the received data."""
	errors = []

	for item in data:
		if not frappe.db.exists("Transport Type", item['name']):
			try:
				url = f'{settings.instance_url}/api/resource/Transport Type?fields=["*"]'
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					data = response.json().get("data", [])
					if data:
						doc = frappe.new_doc("Transport Type")
						doc.transport_type = item.get('transport_type', item['name'])
						doc.insert(ignore_permissions=True)
				else:
					frappe.throw(_("Failed to fetch data for Transport Type: {0}").format(response.text))
			except Exception as e:
				errors.append(f"Error creating Transport Type {item['name']}: {e}")

	if errors:
		frappe.log_error("\n".join(errors), "Transport Type Sync Errors")