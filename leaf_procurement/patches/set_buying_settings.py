import frappe # type: ignore

def execute():
    """Force update of Buying Settings on every migrate"""
    try:
        settings = frappe.get_single("Buying Settings")
        settings.disable_last_purchase_rate = 1   # ✅ true
        settings.maintain_same_rate = 0          # ✅ false
        settings.set_landed_cost_based_on_purchase_invoice_rate = 0  # ✅ false
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.logger().info("Buying Settings updated: disable_last_purchase_rate=1, maintain_same_rate=0")
    except Exception as e:
        frappe.logger().error(f"Failed to update Buying Settings: {e}")
