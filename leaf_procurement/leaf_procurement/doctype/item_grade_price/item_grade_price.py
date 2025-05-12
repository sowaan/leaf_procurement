# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ItemGradePrice(Document):
    def validate(self):
        # Check if another entry with the same composite key exists
        existing = frappe.db.exists(
            "Item Grade Price",
            {
                "item": self.item,
                "item_grade": self.item_grade,
                "item_sub_grade": self.item_sub_grade,
                "price_list": self.price_type,
                "name": ["!=", self.name],  # exclude current doc in case of update
            }
        )

        if existing:
            frappe.throw(
                f"An entry already exists for Item: <b>{self.item}</b>, "
                f"Grade: <b>{self.item_grade}</b>, Sub Grade: <b>{self.item_sub_grade}</b>, "
                f"Price Type: <b>{self.price_type}</b>."
            )
@frappe.whitelist()
def get_item_grade_price(item_grade, item_sub_grade):
    price = frappe.db.get_value(
        "Item Grade Price",
        {
            "item_grade": item_grade,
            "item_sub_grade": item_sub_grade,
            "price_list": "Standard Buying"
        },
        "rate"
    )
    return price or 0