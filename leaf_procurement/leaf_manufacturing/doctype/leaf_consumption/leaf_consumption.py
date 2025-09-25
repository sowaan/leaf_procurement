# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from datetime import datetime
from erpnext.accounts.utils import get_fiscal_year # type: ignore
from frappe import _, ValidationError 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore

class LeafConsumption(Document):
	def autoname(self):
		date_str = str(self.date)  # or date_obj.strftime("%Y-%m-%d")
		today = datetime.strptime(date_str, "%Y-%m-%d")

		#today = datetime.strptime(self.date, "%Y-%m-%d")
		
		fy = get_fiscal_year(today)
		fy_start_year_short = fy[1].strftime("%y")
		fy_end_year_short = fy[2].strftime("%y")
		prefix = f"{self.location_short_code}-{fy_start_year_short}-{fy_end_year_short}-CON-"
		self.name = make_autoname(prefix + ".######")

