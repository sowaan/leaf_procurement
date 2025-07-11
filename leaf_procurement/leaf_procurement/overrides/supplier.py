import frappe # type: ignore
from frappe import _ # type: ignore
from erpnext.buying.doctype.supplier.supplier import Supplier # type: ignore
from frappe.model.naming import make_autoname


class CustomSupplier(Supplier):
    def autoname(self):
        if getattr(self, "skip_autoname", False):
            print("Skipping autoname for CustomSupplier", self.servername)
            self.name = self.servername
            return  
        
        from datetime import datetime

        year = datetime.today().strftime('%Y') 
        
        settings = frappe.get_doc("Leaf Procurement Settings")
        self.custom_company = settings.get("company_name") if settings else None
        self.custom_location_short_code = frappe.db.get_value(
            "Warehouse",
            settings.get("location_warehouse"),
            "custom_short_code"
        )

        prefix = f"{self.custom_location_short_code}-{year}-SUP-"
        self.name = make_autoname(prefix + ".#####")
                  
    def create_primary_contact(self):
        if self.custom_quota_allowed is None or self.custom_quota_allowed <= 0:
            frappe.throw(_("Quota allowed must be greater than 0."), title=_("Invalid Quota Allowed"))

        if not self.mobile_no:
            frappe.throw(_("Mobile number is required."), title=_("Missing Mobile Number"))
        from erpnext.selling.doctype.customer.customer import make_contact # type: ignore

        if not self.supplier_primary_contact:
            if self.mobile_no:
                contact = make_contact(self)
                self.db_set("supplier_primary_contact", contact.name)
                self.db_set("mobile_no", self.mobile_no)
                if self.email_id:
                    self.db_set("email_id", self.email_id)
