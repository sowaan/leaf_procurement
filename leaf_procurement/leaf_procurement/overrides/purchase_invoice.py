
import frappe
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice

class CustomPurchaseInvoice(PurchaseInvoice):
    def validate(self):
        if self.name and not self.custom_barcode:
            self.custom_barcode = self.name