import frappe

def after_install():
    """
    This function is called when the app is installed.
    It creates necessary translations for the app.
    """
    create_translations()
    frappe.db.commit()  # Ensure changes are committed to the database
    frappe.msgprint("Leaf Procurement app installed successfully with translations.")

def create_translations():
    translations = [
        {
            "language": "en",
            "source_text": "Supplier",
            "translated_text": "Grower"
        }
    ]

    for t in translations:
        if not frappe.db.exists("Translation", {
            "language": t["language"],
            "source_text": t["source_text"]
        }):
            doc = frappe.get_doc({
                "doctype": "Translation",
                "language": t["language"],
                "source_text": t["source_text"],
                "translated_text": t["translated_text"]
            })
            doc.insert(ignore_permissions=True)