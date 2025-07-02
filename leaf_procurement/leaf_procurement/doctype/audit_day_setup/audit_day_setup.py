# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from frappe import _ # type: ignore
from datetime import datetime, timedelta

class AuditDaySetup(Document):
    def validate(self):
        # Convert string to date object if needed
        date_obj = self._parse_date(self.date)
        date_obj2 = self._parse_date(self.date)

        # Ensure self.date is a date object
        if isinstance(self.date, str):
            date_obj2 = datetime.strptime(self.date, "%Y-%m-%d").date()
        else:
            date_obj2 = self.date

        today = frappe.utils.nowdate()
        today = datetime.strptime(today, "%Y-%m-%d").date()
        yesterday = today - timedelta(days=1)

        if self.date:
            existing = frappe.db.exists("Audit Day Setup", {
                "location_warehouse": self.location_warehouse,
                "date": self.date,
                "day_close_time": ["is", "set"],
                "name": ["!=", self.name]  # exclude current doc
            })
            if existing:
                frappe.throw(_("The selected date {} has been closed and cannot be modified.").format(self.date))

            existing = frappe.db.exists("Audit Day Setup", {
                "location_warehouse": self.location_warehouse,
                "date": self.date,
                "name": ["!=", self.name]  # exclude current doc
            })
            if existing:
                frappe.throw(_("The selected date {} already has a day setup for this location.").format(self.date))

        #only check if day in not open yet only than validate following
        if self.day_open_time:
            return 
        
        open_days = frappe.db.get_all(
            "Audit Day Setup",
            filters={
                "location_warehouse": self.location_warehouse,
                "day_open_time": ["is", "set"],
                "day_close_time": ["is", "not set"],
                "date": ["!=", self.date]
            },
            fields=["date"]
        )

        if open_days:
            # Format open dates with line breaks
            open_dates = '<br>'.join(f"- {day.date}" for day in open_days)
            frappe.throw(
                _("There are already open day(s):<br>{0}").format(open_dates),
                title=_("Open Days Found")
            )

        if date_obj2 < yesterday:
            frappe.throw("You cannot create a record for a date older than yesterday.")

        # Check if date is Sunday
        settings = frappe.get_doc("Leaf Procurement Settings", "Leaf Procurement Settings")
        if date_obj and date_obj.weekday() == 6 and not settings.allow_sunday_open:  # Sunday = 6
            frappe.throw(_("You cannot open day on Sunday as entry is not permitted on Sunday."))



          		
    def _parse_date(self, value):
        """Convert string to date if necessary."""
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d").date()
        return value  # Already a date object



