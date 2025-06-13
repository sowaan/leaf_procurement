# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe 	#type: ignore
from frappe.model.document import Document 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore
from erpnext.accounts.utils import get_fiscal_year # type: ignore
from datetime import datetime
from frappe import _, ValidationError 	#type: ignore
from leaf_procurement.leaf_procurement.api.config import get_cached_prefix

class BalePurchase(Document):
	def autoname(self):
		date_str = str(self.date)  # or date_obj.strftime("%Y-%m-%d")
		today = datetime.strptime(date_str, "%Y-%m-%d")

		#today = datetime.strptime(self.date, "%Y-%m-%d")
		
		fy = get_fiscal_year(today)
		fy_start_year_short = fy[1].strftime("%y")
		fy_end_year_short = fy[2].strftime("%y")
		prefix = f"{self.location_short_code}-{fy_start_year_short}-{fy_end_year_short}-BP-"
		self.name = make_autoname(prefix + ".######")

	def before_save(self):
		self.bale_barcode = ""
		self.item_grade = ""
		self.item_sub_grade = ""
		self.price = ""

	def on_submit(self):
		if not self.bale_registration_code:
			return

		day_open = frappe.get_all("Day Setup",
			filters={
				"date": self.date,
				"day_open_time": ["is", "set"],
				"day_close_time": ["is", "not set"]
			},
			fields=["name"]
		)

		if not day_open:
			frappe.throw(_("⚠️ You cannot register bales because the day is either not opened or already closed."))

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

			# Raise with user-friendly HTML message and title
			frappe.throw(
				msg=message,
				title=_("Unregistered Bale Barcodes")
			)

        
		# Check for incorrect number of bales
		entered_count = len(self.detail_table or [])
		if entered_count > expected_count:
			frappe.throw(
				msg=_("⚠️ The number of bales entered is <b>{0}</b>, but the expected number of bales is <b>{1}</b> from Bale Registration '{2}'.".format(
					entered_count, expected_count, self.bale_registration_code
				)),
				title=_("Mismatch in Bale Count")
			)

	

	# def autoname(self):
	# 	cached_prefix = get_cached_prefix()

	# 	prefix = f"{cached_prefix}-BP"

	# 	# Find current max number with this prefix
	# 	last_name = frappe.db.sql(
	# 		"""
	# 		SELECT name FROM `tabBale Purchase`
	# 		WHERE name LIKE %s ORDER BY name DESC LIMIT 1
	# 		""",
	# 		(prefix + "-%%%%%",),
	# 	)

	# 	if last_name:
	# 		last_number = int(last_name[0][0].split("-")[-1])
	# 		next_number = last_number + 1
	# 	else:
	# 		next_number = 1

	# 	self.name = f"{prefix}-{next_number:05d}"

@frappe.whitelist()
def get_purchase_bales(name):
	bale_registration_list = frappe.get_all(
		"Bale Registration Detail",
		filters={"parent": name},
		fields=["bale_barcode"],
		pluck="bale_barcode"
	)
	get_purchase = frappe.db.exists("Bale Purchase", {"bale_registration_code": name, "docstatus": ["<", 2]})
	if not get_purchase:
		return None

	bale_purchase_details = frappe.get_all(
			"Bale Purchase Detail",
			filters={"parent": ["in", frappe.get_all(
				"Bale Purchase",
				filters={"bale_registration_code": name, "docstatus": ["<", 2]},
				fields=["name"],
				pluck="name"
			)]},
			fields=["bale_barcode"],
			pluck="bale_barcode"
		)
	
	print("Bale Purchase Details:", bale_purchase_details)
	# bale_code = frappe.get_all(
	# 	"Bale Registration Detail",
	# 	filters={'parent': name, 'bale_barcode': ['not in', bale_purchase_details]},
	# 	fields=["bale_barcode"]
	# )

	# print("Bale Code:", bale_code, "\n\n\n\n\n\n")

	return bale_purchase_details

	# if len(bale_registration_list) > 0:
	# 	return frappe.get_all(
	# 		"Bale Purchase Detail",
	# 		filters={"bale_barcode": ["not in", bale_registration_list]},
	# 		fields=["bale_barcode"]
	# 	)
	# else:
	# 	return []
