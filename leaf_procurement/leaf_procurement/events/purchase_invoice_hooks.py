
import frappe # type: ignore
import urllib.parse
from leaf_procurement.leaf_procurement.api.barcode import get_base64_barcode

def on_cancel_purchase_invoice(doc, method):
    weight_docs = frappe.get_all("Bale Weight Info", 
        filters={"purchase_invoice": doc.name, "docstatus": 1}, 
        fields=["name"]
    )

    for weight_name in weight_docs:
        weight_doc = frappe.get_doc("Bale Weight Info", weight_name["name"])
        weight_doc.cancel()

def before_cancel_purchase_invoice(doc, method):
    bale_barcodes = [item.batch_no for item in doc.items if item.batch_no]

    # Optional: log for debugging
    print("🔎 Checking bale barcodes:", bale_barcodes)

    # Check if any of the bale barcodes were already transferred
    check_bale_dependencies(bale_barcodes)

def check_bale_dependencies(bale_barcodes):
    if not bale_barcodes:
        return

    existing = frappe.db.get_all(
        "Goods Transfer Note Items",
        filters={
            "bale_barcode": ["in", bale_barcodes],
            "docstatus": 1  # Assuming your parent doc is submitted
        },
        fields=["parent", "bale_barcode"]
    )

    if existing:
        message_lines = ["Cannot cancel Voucher: GTNs already exist for the following bale barcodes:<br>"]
        for row in existing:
            encoded_parent = urllib.parse.quote(row.parent)
            gtn_link = f'<a href="/app/goods-transfer-note/{encoded_parent}" target="_blank">{row.parent}</a>'
            message_lines.append(f"{row.bale_barcode} → {gtn_link}")

        message = "<br>".join(message_lines)
        frappe.throw(message)

def before_submit_purchase_invoice(self, doctype):
    if not self.custom_barcode:
        self.custom_barcode = self.name  # just before submit
    self.custom_barcode_base64 = get_base64_barcode(self.custom_barcode)
 