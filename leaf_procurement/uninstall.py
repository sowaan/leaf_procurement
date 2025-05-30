import frappe

def before_uninstall():
    """
    This function is called when the app is uninstalled.
    It deletes translations created during installation.
    """
    delete_translations()
    frappe.db.commit()  # Ensure changes are committed to the database
    frappe.msgprint("Leaf Procurement app uninstalled successfully and translations deleted.")

def delete_translations():
    source_texts = ["Supplier"]  # Add all the source texts you created

    frappe.db.delete("Translation", {
        "source_text": ["in", source_texts]
    })
