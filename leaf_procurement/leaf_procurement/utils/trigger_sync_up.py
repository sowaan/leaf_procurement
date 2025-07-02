import json
import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from ..utils.sync_up import sync_up_worker
from ..utils.sync_down import sync_down_worker

@frappe.whitelist()
def trigger_sync_up(values=None):
    if not values:
        return

    if isinstance(values, str):
        values = json.loads(values)

    frappe.enqueue(
        method=sync_down_worker,
        queue="long",
        values=values,
        user=frappe.session.user
    )

@frappe.whitelist()
def trigger_sync_down(values=None):
    if not values:
        return

    if isinstance(values, str):
        values = json.loads(values)

    frappe.enqueue(
        method=sync_up_worker,
        queue="long",
        values=values,
        user=frappe.session.user
    )

    #frappe.msgprint("✅ Sync started in background.")