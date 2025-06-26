# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname # type: ignore

class QuotaSetup(Document):
	def autoname(self):
		if getattr(self, "skip_autoname", False):
			self.name = self.servername
			return

		prefix = "Quo-"
		self.name = make_autoname(prefix + ".#####")
