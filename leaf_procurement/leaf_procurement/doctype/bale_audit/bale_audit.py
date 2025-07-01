# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from datetime import datetime
from frappe import _, ValidationError 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore

class BaleAudit(Document):
    def autoname(self):
        if getattr(self, "skip_autoname", False):
            self.name = self.servername
            return

        from datetime import datetime

        year = datetime.today().strftime('%Y')

        # settings = frappe.get_doc("Leaf Procurement Settings")
        # self.custom_location = settings.get("location_warehouse")
        # self.location_shortcode = frappe.db.get_value(
        #     "Warehouse",
        #     settings.get("location_warehouse"),
        #     "custom_short_code"
        # )


        prefix = f"{self.location_shortcode}-AUD-{year}-"
        self.name = make_autoname(prefix + ".######")

    def on_submit(self):
        # if check validations is false, no need to check validations
        # as this is a sync operation
        day_open = frappe.get_all("Audit Day Setup",
            filters={
                "location_warehouse": self.location_warehouse,
                "date": self.date,
                "day_open_time": ["is", "set"],
                "day_close_time": ["is", "not set"]
            },
            fields=["name"]
        )

        if not day_open:
            frappe.throw(_("⚠️ Audit not permitted because the day is either not opened or already closed for location: " + self.location_warehouse))
        

    
    def validate(self):
        if not self.detail_table or len(self.detail_table) == 0:
            frappe.throw(_("Please add at least one row in the Bale Audit Detail table."))