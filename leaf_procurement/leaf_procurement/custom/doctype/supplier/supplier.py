import frappe # type: ignore
from frappe import _ # type: ignore

import re
import frappe
from frappe import _

def normalize_nic(nic):
    """Return NIC with only digits (remove -, spaces, etc)."""
    return re.sub(r'\D', '', nic or '')

def validate_unique_nic(doc, method):
    normalized_nic = normalize_nic(doc.custom_nic_number)

    # Auto-format if it's 13 digits
    cnic = None
    if len(normalized_nic) == 13:
        cnic = f"{normalized_nic[:5]}-{normalized_nic[5:12]}-{normalized_nic[12]}"
        doc.custom_nic_number = cnic

    # Validate formatted CNIC
    cnic_regex = r'^\d{5}-\d{7}-\d{1}$'
    if cnic and not re.match(cnic_regex, cnic):
        frappe.throw(_("CNIC must be in the format xxxxx-xxxxxxx-x"))

    if len(normalized_nic) != 13:
        frappe.throw(
            _("NIC must be 13 digits. Current value: {0}").format(doc.custom_nic_number),
            title="Invalid NIC Number"
        )
    settings = frappe.get_doc("Leaf Procurement Settings")
    
    if not doc.custom_location_warehouse:
        doc.custom_location_warehouse = settings.get("location_warehouse") if settings else None
    if not doc.custom_company:
        doc.custom_company = settings.get("company_name") if settings else None
    if not doc.custom_location_short_code:
        doc.custom_location_short_code = frappe.db.get_value(
            "Warehouse",
            doc.custom_location_warehouse,
            "custom_short_code"
        )

    location = doc.custom_location_warehouse

    if not normalized_nic or not location:
        return  # Skip if required fields are empty

    # Check for duplicates with same normalized NIC in the same warehouse
    suppliers = frappe.get_all(
        "Supplier",
        filters={
            "custom_location_warehouse": location,
            "name": ["!=", doc.name]  # Exclude current doc
        },
        fields=["name", "custom_nic_number", "mobile_no"]
    )

    for supplier in suppliers:
        existing_normalized_nic = normalize_nic(supplier.custom_nic_number)
        if normalized_nic == existing_normalized_nic:
            frappe.throw(
                _("Supplier with NIC <b>{0}</b> already exists for location <b>{1}</b> (Supplier: {2})").format(
                    doc.custom_nic_number, location, supplier.name
                ),
                title="Duplicate NIC Number"
            )
        elif doc.mobile_no and doc.mobile_no == supplier.mobile_no:
            frappe.throw(
                _("Supplier with mobile number <b>{0}</b> already exists for location <b>{1}</b> (Supplier: {2})").format(
                    doc.mobile_no, location, supplier.name
                ),
                title="Duplicate Mobile Number"
            )

