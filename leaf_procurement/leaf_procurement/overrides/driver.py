import uuid
import frappe
from erpnext.setup.doctype.driver.driver import Driver  # type: ignore
from frappe.model.naming import make_autoname


class CustomDriver(Driver):
    def before_insert(doc):
        if not doc.custom_sync_id:
            doc.custom_sync_id = str(uuid.uuid4())    
       
    def autoname(self):
        if getattr(self, "skip_autoname", False):
            print("Skipping autoname for CustomDriver", self.servername)
            self.name = self.servername
            return

        print("Running autoname for CustomDriver", self.name)
        from datetime import datetime

        year = datetime.today().strftime('%Y')

        settings = frappe.get_doc("Leaf Procurement Settings")
        self.custom_location = settings.get("location_warehouse")
        self.custom_code = frappe.db.get_value(
            "Warehouse",
            settings.get("location_warehouse"),
            "custom_short_code"
        )

        prefix = f"{self.custom_code}-DRV-{year}-"
        self.name = make_autoname(prefix + ".#####")