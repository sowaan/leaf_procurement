# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
from frappe.model.document import Document
from frappe import _, ValidationError

class BalePurchase(Document):
	def autoname(self):
		if not self.company or not self.location_warehouse:
			frappe.throw("Company and Location Warehouse must be set before saving.")

		# Fetch Company Abbreviation
		company_abbr = frappe.db.get_value("Company", self.company, "abbr")
		# Fetch Warehouse Short Code
		warehouse_code = frappe.db.get_value("Warehouse", self.location_warehouse, "custom_short_code")

		if not company_abbr or not warehouse_code:
			frappe.throw("Could not fetch Company Abbreviation or Warehouse Short Code.")

		# Get current year
		current_year = datetime.now().year

		# Compose prefix
		prefix = f"{warehouse_code}-PO-{current_year}"


		# Find current max number with this prefix
		last_name = frappe.db.sql(
			"""
			SELECT name FROM `tabBale Purchase`
			WHERE name LIKE %s ORDER BY name DESC LIMIT 1
			""",
			(prefix + "-%%%%%",),
		)

		if last_name:
			last_number = int(last_name[0][0].split("-")[-1])
			next_number = last_number + 1
		else:
			next_number = 1

		self.name = f"{prefix}-{next_number:05d}"

	def validate(self):
		if not self.bale_registration_code:
			return

		# Get all registered bale barcodes for this registration
		registered_bales = frappe.get_all(
			"Bale Registration Detail",
			filters={"parent": self.bale_registration_code},
			fields=["bale_barcode"]
		)
		registered_barcodes = {d.bale_barcode for d in registered_bales}
		
		expected_count = len(registered_barcodes)
		
		# Check which ones are missing
		unregistered = []
		for row in self.detail_table:
			if row.bale_barcode not in registered_barcodes:
				unregistered.append(row.bale_barcode)

		if unregistered:
			message = _("The following bale barcodes are not registered under Bale Registration '{0}':").format(self.bale_registration_code)
			message += "<br><ul>"
			for code in unregistered:
				message += f"<li>{code}</li>"
			message += "</ul>"
        	# Show message without traceback
			frappe.msgprint(msg=message, title=_("Unregistered Bale Barcodes"), indicator='orange')
			
			# Raise clean validation error to stop save
			raise ValidationError
        
		# Check for incorrect number of bales
		entered_count = len(self.detail_table or [])
		if entered_count != expected_count:
			frappe.msgprint(
				msg=_("⚠️ The number of bales entered is <b>{0}</b>, but the expected number of bales is <b>{1}</b> from Bale Registration '{2}'.".format(
					entered_count, expected_count, self.bale_registration_code
				)),
				title=_("Mismatch in Bale Count"),
				indicator='orange'
			)
			raise ValidationError