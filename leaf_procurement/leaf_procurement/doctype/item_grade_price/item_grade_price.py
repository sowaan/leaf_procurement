# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from frappe import _ # type: ignore

class ItemGradePrice(Document):
    def autoname(self):
        """Override the default method to set a custom name."""
        if getattr(self, "skip_autoname", False):
            self.name = self.servername
            return  

        settings = frappe.get_doc("Leaf Procurement Settings")
        # self.short_code = frappe.db.get_value(
        #     "Warehouse",
        #     settings.get("location_warehouse"),
        #     "custom_short_code"
        # )

        prefix = f"{self.abbr}-{self.short_code}-{self.item_sub_grade}-"
        self.name = frappe.model.naming.make_autoname(prefix + ".###")


    def validate(self):
        # Check if another entry with the same composite key exists
        existing = frappe.db.exists(
            "Item Grade Price",
            {
                "company": self.company,
                "location_warehouse": self.location_warehouse,                
                "item": self.item,
                "item_grade": self.item_grade,
                "item_sub_grade": self.item_sub_grade,
                "price_list": self.price_list,
                "name": ["!=", self.name],  # exclude current doc in case of update
            }
        )

        if existing:
            frappe.throw(
                f"An entry already exists for Item: <b>{self.item}</b>, "
                f"Grade: <b>{self.item_grade}</b>, Sub Grade: <b>{self.item_sub_grade}</b>, "
                f"Price Type: <b>{self.price_list}</b> against the given location."
            )
@frappe.whitelist()
def get_item_grade_price(company, location_warehouse, item, item_grade, item_sub_grade):
    price = frappe.db.get_value(
        "Item Grade Price",
        {
            "company": company,
            "location_warehouse": location_warehouse,
            "item": item,            
            "item_grade": item_grade,
            "item_sub_grade": item_sub_grade,
            "price_list": "Standard Buying"
        },
        "rate"
    )
    return price or 0
