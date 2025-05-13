import frappe # type: ignore

_cached_prefix = None  # Global cache


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
