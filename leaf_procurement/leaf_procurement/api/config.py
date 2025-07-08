import frappe # type: ignore

_cached_prefix = None  # Global cache

@frappe.whitelist()
def get_service_items_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.get_all(
        "Item",
        filters={"item_group": "Services"},
        fields=["name", "item_name"],
        limit_page_length=page_len,
        start=start
    )
@frappe.whitelist()
def get_Product_items_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.get_all(
        "Item",
        filters={"item_group": "Products"},
        fields=["name", "item_name"],
        limit_page_length=page_len,
        start=start
    )
def get_cached_prefix():
    global _cached_prefix
    if _cached_prefix is None:
        try:
            settings = frappe.get_single("Leaf Procurement Settings")
            warehouse_code = frappe.db.get_value("Warehouse", settings.location_warehouse, "custom_short_code")
            
            # Default to "LP" if warehouse_code is None or empty
            if not warehouse_code:
                raise ValueError("Missing warehouse short code")

            _cached_prefix = f"{warehouse_code}-{frappe.utils.now_datetime().year}"
        except Exception:
            #Fallback to LP prefix if settings or short_code not found
            _cached_prefix = f"LP-{frappe.utils.now_datetime().year}"

    return _cached_prefix
