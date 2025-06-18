import frappe # type: ignore

def on_cancel_purchase_invoice(doc, method):
    bale_barcodes = [item.batch_no for item in doc.items if item.batch_no]

    # Optional: log for debugging
    print("🔎 Checking bale barcodes:", bale_barcodes)

    # Check if any of the bale barcodes were already transferred
    check_bale_dependencies(bale_barcodes)

def check_bale_dependencies(bale_barcodes):
    if not bale_barcodes:
        return

    existing = frappe.db.get_all(
        "Stock Entry Detail",
        filters={
            "bale_barcode": ["in", bale_barcodes],
            "docstatus": 1
        },
        fields=["parent", "bale_barcode"]
    )

    if existing:
        barcode_list = ", ".join([row.bale_barcode for row in existing])
        frappe.throw(f"Cannot cancel Purchase Invoice: GTNs already exist for bale barcodes: {barcode_list}")

    frappe.throw(f"------------GREAT--------------: {barcode_list}")