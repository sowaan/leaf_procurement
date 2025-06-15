import frappe 	#type: ignore
from frappe.model.document import Document 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore
from erpnext.accounts.utils import get_fiscal_year # type: ignore
from datetime import datetime
from frappe import _, ValidationError 	#type: ignore
from leaf_procurement.leaf_procurement.api.config import get_cached_prefix

class BaleWeightInfo(Document):
	def before_save(self):
		self.scan_barcode = ""
		self.item_grade = ""
		self.item_sub_grade = ""
		self.reclassification_grade = ""
		self.price = 0
		self.bale_weight = 0
		

	def autoname(self):
		date_str = str(self.date)  # or date_obj.strftime("%Y-%m-%d")
		today = datetime.strptime(date_str, "%Y-%m-%d")        
		#date_part = today.strftime("%d%m%Y")
		fy = get_fiscal_year(today)
		fy_start_year_short = fy[1].strftime("%y")
		fy_end_year_short = fy[2].strftime("%y")
		prefix = f"{self.location_short_code}-{fy_start_year_short}-{fy_end_year_short}-BW-"
		self.name = make_autoname(prefix + ".######")

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

		self.make_purchase_invoice()


	
	def make_purchase_invoice(self):
		from leaf_procurement.leaf_procurement.api.bale_weight_utils import create_purchase_invoice

		create_purchase_invoice(self.name)

	# def autoname(self):
	# 	cached_prefix = get_cached_prefix()

	# 	prefix = f"{cached_prefix}-BW"

	# 	# Find current max number with this prefix
	# 	last_name = frappe.db.sql(
	# 		"""
	# 		SELECT name FROM `tabBale Weight Info`
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
def match_grade_with_bale_purchase(barcode):
	bale_purchase_detail = frappe.db.get_value('Bale Purchase Detail', {'bale_barcode': barcode}, ['bale_barcode', 'item_grade', 'item_sub_grade'], as_dict=1)

	return bale_purchase_detail


@frappe.whitelist()
def quota_weight(location):
	"""
	Get the quota weight for a given location.
	"""
	location_quota = frappe.db.get_value('Quota Setup', {'location_warehouse': location}, ['bale_minimum_weight_kg', 'bal_maximum_weight_kg'], as_dict=1)

	return location_quota