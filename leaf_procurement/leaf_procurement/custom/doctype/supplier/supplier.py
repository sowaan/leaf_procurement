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
        fields=["name", "custom_nic_number"]
    )

    for supplier in suppliers:
        existing_normalized_nic = normalize_nic(supplier.custom_nic_number)
        if normalized_nic == existing_normalized_nic:
            frappe.throw(
                _("Supplier with NIC <b>{0}</b> already exists for warehouse <b>{1}</b> (Supplier: {2})").format(
                    doc.custom_nic_number, location, supplier.name
                ),
                title="Duplicate NIC Number"
            )
