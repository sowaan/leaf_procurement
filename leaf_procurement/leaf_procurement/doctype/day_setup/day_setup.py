# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from frappe import _ # type: ignore
from datetime import datetime

class DaySetup(Document):
    def validate(self):
        # Convert string to date object if needed
        date_obj = self._parse_date(self.date)
        due_date_obj = self._parse_date(self.due_date)
        print(f"\n\n{date_obj.weekday()}")
        # Ensure due date is after date
        if date_obj and due_date_obj:
            if due_date_obj <= date_obj:
                frappe.throw(_("Due Date ({}) must be after Date ({}).").format(self.due_date, self.date))

        # Check if date is Sunday
        if date_obj and date_obj.weekday() == 6:  # Sunday = 6
            frappe.throw(_("Date cannot be a Sunday."))

        if self.date:
            existing = frappe.db.exists("Day Setup", {
                "date": self.date,
                "name": ["!=", self.name]  # exclude current doc
            })
            if existing:
                frappe.throw(_("A record already exists for the date {}. Only one record per day is allowed.").format(self.date))
          		
    def _parse_date(self, value):
        """Convert string to date if necessary."""
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d").date()
        return value  # Already a date object