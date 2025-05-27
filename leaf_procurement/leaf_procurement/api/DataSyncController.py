import frappe 	#type: ignore

@frappe.whitelist()
def sync_down():
    from leaf_procurement.utils.sync import sync_master_data
    sync_master_data()
    return "Master data synced successfully."

@frappe.whitelist()
def sync_up():
    from leaf_procurement.utils.sync import sync_transactions
    sync_transactions()
    return "Transactions pushed to server successfully."
