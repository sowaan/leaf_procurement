import frappe
from erpnext.stock.doctype.warehouse.warehouse import Warehouse  # type: ignore

class CustomWarehouse(Warehouse):
    def autoname(self):
        if getattr(self, "skip_autoname", False):
            self.name = self.servername
            return
        
        if self.company:
            suffix = " - " + frappe.get_cached_value("Company", self.company, "abbr")
            if not self.warehouse_name.endswith(suffix):
                self.name = self.warehouse_name + suffix
                return

        self.name = self.warehouse_name
