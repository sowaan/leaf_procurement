# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from datetime import datetime
from frappe import _, ValidationError 	#type: ignore

class BaleAudit(Document):
    def on_submit(self):
        # if check validations is false, no need to check validations
        # as this is a sync operation
        day_open = frappe.get_all("Audit Day Setup",
            filters={
                "date": self.date,
                "day_open_time": ["is", "set"],
                "day_close_time": ["is", "not set"]
            },
            fields=["name"]
        )

        if not day_open:
            frappe.throw(_("⚠️ Audit no permitted because the day is either not opened or already closed."))
