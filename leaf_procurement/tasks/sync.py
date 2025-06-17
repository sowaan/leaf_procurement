import frappe
import socket
from leaf_procurement.leaf_procurement.doctype.leaf_procurement_sync_tool.leaf_procurement_sync_tool import sync_up

@frappe.whitelist()
def hybrid_sync():
    settings = frappe.get_doc("Leaf Procurement Settings")
    if not settings.enable_hybrid_mode:
        return
    
    if is_internet_available():
        # print("✅ Internet is available.")
        # proceed with API call or online task
        sync_up()
    else:
        print("❌ No internet connection")
        # handle offline logic


def is_internet_available(host="8.8.8.8", port=53, timeout=3):
    """
    Check internet connectivity by trying to connect to Google's DNS server (8.8.8.8) on port 53.
    Returns True if successful, False otherwise.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False
