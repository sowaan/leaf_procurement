# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime

import frappe
from frappe.model.document import Document

class BaleRegistration(Document):
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
        prefix = f"{warehouse_code}-PR-{current_year}"
        

        # Find current max number with this prefix
        last_name = frappe.db.sql(
            """
            SELECT name FROM `tabBale Registration`
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

