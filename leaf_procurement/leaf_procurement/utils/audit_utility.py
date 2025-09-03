import frappe # type: ignore
from frappe.utils import now

@frappe.whitelist()
def change_audit_weight(parent, barcode, new_weight):
    # if frappe.session.user != "Administrator":
    #     frappe.throw(_("Only Administrator is allowed to perform this operation."))

    # --- Update Bale Audit Detail ---
    for row in frappe.get_all(
        "Bale Audit Detail", 
        filters={"bale_barcode": barcode}, 
        fields=["name", "weight"]
    ):
        old_weight = row.weight
        frappe.db.set_value("Bale Audit Detail", row.name, "weight", new_weight)

        # --- Append Log to Child Table ---
        parent_doc = frappe.get_doc("Bale Audit Change", parent)
        parent_doc.append("detail_table", {   # "change_log" = child table fieldname
            "bale_barcode": barcode,
            "old_weight": old_weight,
            "new_weight": new_weight,
            "datetime": now(),
        })
        parent_doc.save(ignore_permissions=True)

    # --- Update GTN Items ---
    for row in frappe.get_all(
        "Goods Transfer Note Items", 
        filters={"bale_barcode": barcode}, 
        fields=["name", "audit_weight"]
    ):
        frappe.db.set_value("Goods Transfer Note Items", row.name, "audit_weight", new_weight)

    frappe.db.commit()
    return "✅ All references updated and logged successfully."