import frappe

@frappe.whitelist()
def change_barcode(old_barcode, new_barcode):


    # 1. Bale Registration Detail
    for row in frappe.get_all("Bale Registration Detail", filters={"bale_barcode": old_barcode}, fields=["name"]):
        frappe.db.set_value("Bale Registration Detail", row.name, "bale_barcode", new_barcode)

    # 2. Bale Purchase Detail
    for row in frappe.get_all("Bale Purchase Detail", filters={"bale_barcode": old_barcode}, fields=["name"]):
        frappe.db.set_value("Bale Purchase Detail", row.name, "bale_barcode", new_barcode)

    # 3. Bale Weight Detail
    for row in frappe.get_all("Bale Weight Detail", filters={"bale_barcode": old_barcode}, fields=["name"]):
        frappe.db.set_value("Bale Weight Detail", row.name, "bale_barcode", new_barcode)

    # 4. Goods Transfer Note
    for row in frappe.get_all("Goods Transfer Note Items", filters={"bale_barcode": old_barcode}, fields=["name"]):
        frappe.db.set_value("Goods Transfer Note Items", row.name, "bale_barcode", new_barcode)

    # 5. Purchase Invoice Items
    for row in frappe.get_all("Purchase Invoice Item", filters={"batch_no": old_barcode}, fields=["name", "parent"]):
        frappe.db.set_value("Purchase Invoice Item", row.name, "batch_no", new_barcode)
        print(f"✅ Updated Purchase Invoice Item {row.name} in {row.parent}")

    settings = frappe.get_cached_doc("Leaf Procurement Settings")


    # 6. Ensure Batch exists
    if not frappe.db.exists("Batch", new_barcode):
        batch = frappe.new_doc("Batch")
        batch.batch_id = new_barcode
        batch.item = settings.default_item # Replace appropriately
        batch.save()
        print(f"✅ Created new Batch: {new_barcode}")

    frappe.db.commit()
    print("✅ All references updated successfully.")
