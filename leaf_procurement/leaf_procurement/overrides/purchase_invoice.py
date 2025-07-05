import uuid
import frappe
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from frappe.model.naming import make_autoname


class CustomPurchaseInvoice(PurchaseInvoice):
    def before_insert(doc):
        if not doc.custom_sync_id:
            doc.custom_sync_id = str(uuid.uuid4())    
           
    def autoname(self):
        """Override the default method to set a custom name."""
        if getattr(self, "skip_autoname", False):
            # print("Skipping autoname for CustomSupplier", self.servername)
            self.name = self.servername
            return  
        
        from datetime import datetime

        year = datetime.today().strftime('%Y') 
        
        settings = frappe.get_doc("Leaf Procurement Settings")
        self.custom_short_code = frappe.db.get_value(
            "Warehouse",
            settings.get("location_warehouse"),
            "custom_short_code"
        )
        prefix = ""
        if self.is_return:
            prefix = f"{self.custom_short_code}-{year}-ACC-PINV-RET-"
        else:
            prefix = f"{self.custom_short_code}-{year}-ACC-PINV-"
        self.name = make_autoname(prefix + ".#####")