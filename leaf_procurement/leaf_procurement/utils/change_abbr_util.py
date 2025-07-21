import frappe # type: ignore

# Function to update fields with old_abbr suffix to new_abbr
def update_abbr_in_field(doctype, fieldname, old_abbr, new_abbr):
    for doc in frappe.get_all(doctype, fields=["name", fieldname]):
        val = doc[fieldname]
        if val and val.endswith(f" - {old_abbr}"):
            new_val = val.replace(f" - {old_abbr}", f" - {new_abbr}")

            # Skip if new_val already exists
            if frappe.db.exists(doctype, new_val):
                frappe.log_error(f"Skipping rename: {val} → {new_val} already exists.", "Duplicate Entry")
                continue

            if fieldname == "name":
                # Rename the doc itself
                frappe.rename_doc(doctype, val, new_val, force=True)
            else:
                # Update field value
                frappe.db.set_value(doctype, doc.name, fieldname, new_val)

def update_company_defaults(old_abbr, new_abbr):
    companies = frappe.get_all("Company", fields=["name"])

    for c in companies:
        doc = frappe.get_doc("Company", c.name)
        dirty = False

        for field in doc.meta.fields:
            if field.fieldtype == "Link" and field.options in ["Account", "Warehouse", "Cost Center"]:
                value = doc.get(field.fieldname)
                if value and value.endswith(f" - {old_abbr}"):
                    new_val = value.replace(f" - {old_abbr}", f" - {new_abbr}")
                    doc.set(field.fieldname, new_val)
                    dirty = True

        if dirty:
            doc.save(ignore_permissions=True)

        # Also check and update nested Company Defaults
        if hasattr(doc, "defaults"):
            for d in doc.defaults:
                if d.fieldname and d.value and d.value.endswith(f" - {old_abbr}"):
                    d.value = d.value.replace(f" - {old_abbr}", f" - {new_abbr}")
            doc.save(ignore_permissions=True)

@frappe.whitelist()
def change_abbr(old_abbr, new_abbr):
    if frappe.session.user != "Administrator":
        frappe.throw(_("Only Administrator is allowed to perform this operation."))

    # Update Company.abbr itself
    company = frappe.db.get_value("Company", {"abbr": old_abbr}, "name")
    if company:
        frappe.db.set_value("Company", company, "abbr", new_abbr)

    # Update dependent fields
    update_abbr_in_field("Account", "name", old_abbr, new_abbr)
    update_abbr_in_field("Cost Center", "name", old_abbr, new_abbr)
    update_abbr_in_field("Warehouse", "name", old_abbr, new_abbr)
    update_abbr_in_field("Budget Account", "account", old_abbr, new_abbr)
    update_abbr_in_field("GL Entry", "account", old_abbr, new_abbr)
    update_abbr_in_field("Purchase Invoice", "cost_center", old_abbr, new_abbr)

    frappe.db.commit()

    update_company_defaults(old_abbr=old_abbr, new_abbr=new_abbr)
    return f"Successfully changed abbreviation from {old_abbr} to {new_abbr}"
