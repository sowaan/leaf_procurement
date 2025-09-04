import frappe # type: ignore
from frappe.utils import now

@frappe.whitelist()
def change_audit_weight(parent, barcode,new_barcode, new_weight):
    # if frappe.session.user != "Administrator":
    #     frappe.throw(_("Only Administrator is allowed to perform this operation."))

    rows = frappe.get_all(
        "Goods Transfer Note Items",
        filters={"bale_barcode": new_barcode},
        fields=["name", "audit_weight"]
    )

    if not rows:
        frappe.throw(f"GTN not found for Bale Barcode: {new_barcode}")

    # --- Update Bale Audit Detail ---
    for row in frappe.get_all(
        "Bale Audit Detail", 
        filters={"bale_barcode": barcode}, 
        fields=["parent","name", "bale_barcode", "weight"]
    ):
        old_weight = row.weight
        frappe.db.set_value("Bale Audit Detail", row.name, "weight", new_weight)
        frappe.db.set_value("Bale Audit Detail", row.name, "bale_barcode", new_barcode)
        
        #frappe.rename_doc("Bale Audit Detail", row.name, new_barcode, force=True)

        # --- Append Log to Child Table ---
        parent_doc = frappe.get_doc("Bale Audit Change", parent)
        parent_doc.new_bale_barcode = new_barcode

        parent_doc.append("detail_table", {   # "change_log" = child table fieldname
            "audit_id": row.parent,
            "bale_barcode": barcode,
            "new_bale_barcode": new_barcode,
            "old_weight": old_weight,
            "new_weight": new_weight,
            "datetime": now(),
        })
        parent_doc.save(ignore_permissions=True)

    # --- Update GTN Items ---
    for row in frappe.get_all(
        "Goods Transfer Note Items", 
        filters={"bale_barcode": new_barcode}, 
        fields=["name", "audit_weight"]
    ):
        frappe.db.set_value("Goods Transfer Note Items", row.name, "audit_weight", new_weight)

    for row in frappe.get_all(
        "Goods Transfer Note Items", 
        filters={"bale_barcode": barcode}, 
        fields=["name", "audit_weight"]
    ):
        frappe.db.set_value("Goods Transfer Note Items", row.name, "audit_weight", None)

    frappe.db.commit()
    return "✅ All references updated and logged successfully."