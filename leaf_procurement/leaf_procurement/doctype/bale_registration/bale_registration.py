# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe 	#type: ignore
from frappe.model.document import Document 	#type: ignore


from leaf_procurement.leaf_procurement.api.config import get_cached_prefix

class BaleRegistration(Document):
    def autoname(self):
        cached_prefix = get_cached_prefix()

        prefix = f"{cached_prefix}-PR"
        

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

