# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import uuid
import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from datetime import datetime
from frappe import _, ValidationError 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore

class BaleAudit(Document):
    def before_insert(doc):
        if not doc.custom_sync_id:
            doc.custom_sync_id = str(uuid.uuid4())    
            
    def autoname(self):
        if getattr(self, "skip_autoname", False):
            self.name = self.servername
            return

        # Ensure self.date exists
        if not self.date:
            frappe.throw("Date is required for generating name")

        # Parse and format the date
        doc_date = datetime.strptime(str(self.date), "%Y-%m-%d")
        date_part = doc_date.strftime("%Y%m%d")  # Format: YYYYMMDD

        # Generate prefix
        prefix = f"{self.location_shortcode}-AUD-{date_part}-"
        self.name = make_autoname(prefix + ".######")

    def on_submit(self):
        # if check validations is false, no need to check validations
        # as this is a sync operation

        if not self.check_validations:
            return
        
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
        

    
   #def validate(self):
        # if not self.detail_table or len(self.detail_table) == 0:
        #     frappe.throw(_("Please add at least one row in the Bale Audit Detail table."))