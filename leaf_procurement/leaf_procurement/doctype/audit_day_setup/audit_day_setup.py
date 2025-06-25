# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from frappe import _ # type: ignore
from datetime import datetime

class AuditDaySetup(Document):
    def validate(self):
        # Convert string to date object if needed
        date_obj = self._parse_date(self.date)

        # Check if date is Sunday
        settings = frappe.get_doc("Leaf Procurement Settings", "Leaf Procurement Settings")
        if date_obj and date_obj.weekday() == 6 and not settings.allow_sunday_open:  # Sunday = 6
            frappe.throw(_("You cannot open day on Sunday as entry is not permitted on Sunday."))


        if self.date:
            existing = frappe.db.exists("Audit Day Setup", {
                "date": self.date,
                "name": ["!=", self.name]  # exclude current doc
            })
            if existing:
                frappe.throw(_("A record already exists for the date {}. Only one record per day is allowed.").format(self.date))
        # Find all open days (with open time but no close time), excluding current date
        
        if not self.day_open_time: #only check if day in not open yet
            open_days = frappe.db.get_all(
                "Audit Day Setup",
                filters={
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

          		
    def _parse_date(self, value):
        """Convert string to date if necessary."""
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d").date()
        return value  # Already a date object
