import requests
import frappe # type: ignore

MASTER_DOCTYPES = [
    "Company", "Warehouse", "Item", "Item Grade", "Item Sub Grade", 
    "Item Grade Price",
    "Bale Status", "Reclassification Grade", "Transport Type"
]

# SOURCE_SITE = "https://central.example.com"
# API_KEY = "xxx"
# API_SECRET = "yyy"
# HEADERS = {"Authorization": f"token {API_KEY}:{API_SECRET}"}

def get_sync_settings():
    settings = frappe.get_single("Leaf Procurement Settings")
    if not (settings.central_server and settings.api_key and settings.api_secret):
        frappe.throw("Sync settings are not properly configured in Leaf Procurement Settings.")

    return {
        "SOURCE_SITE": settings.central_server,
        "HEADERS": {
            "Authorization": f"token {settings.api_key}:{settings.api_secret}"
        }
    }

def sync_master_data():
    config = get_sync_settings()
    for doctype in MASTER_DOCTYPES:
        res = requests.get(f"{config['SOURCE_SITE']}/api/resource/{doctype}?limit_page_length=1000", headers=config['HEADERS'])
        res.raise_for_status()
        for record in res.json()["data"]:
            detail = requests.get(f"{config['SOURCE_SITE']}/api/resource/{doctype}/{record['name']}", headers=config['HEADERS'])
            detail.raise_for_status()
            doc_data = detail.json()["data"]

            # Avoid overwriting unless needed
            if frappe.db.exists(doctype, doc_data["name"]):
                continue

            new_doc = frappe.get_doc(doc_data)
            new_doc.insert(ignore_permissions=True)

TRANSACTION_DOCTYPES = ["Supplier",
"Driver",
"Bale Registration",
"Bale Registration Detail",
"Bale Purchase",
"Bale Purchase Detail",
"Bale Weight Info",
"Bale Weight Detail",
"Purchase Invoice",
"Purchase Invoice Item",
"Stock Entry",
"Stock Entry Detail"]

def sync_transactions():
    config = get_sync_settings()
    for doctype in TRANSACTION_DOCTYPES:
        unsynced_docs = frappe.get_all(doctype, filters={"synced": 0}, fields=["name"])
        for d in unsynced_docs:
            doc = frappe.get_doc(doctype, d.name)
            data = doc.as_dict()
            # You might want to remove metadata like 'modified_by'
            data.pop('name')  # optional if you want server to generate name

            res = requests.post(
                f"{config['SOURCE_SITE']}/api/resource/{doctype}",
                headers=config['HEADERS'],
                json={"data": data}
            )
            res.raise_for_status()
            # Mark as synced
            doc.db_set("synced", 1)
