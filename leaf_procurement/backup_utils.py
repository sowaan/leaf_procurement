import frappe
import os
from frappe.utils.backups import BackupGenerator

@frappe.whitelist()
def take_backup_now():
    try:
        # Get DB credentials
        db_name = frappe.conf.db_name
        db_user = frappe.conf.db_name
        db_password = frappe.conf.db_password

        # Initialize backup
        backup = BackupGenerator(db_name, db_user, db_password)
        backup.set_backup_file_name()

        # Perform database dump
        backup.take_dump()

        # Perform file backup (no return value in Frappe 15)
        backup.backup_files()

        # DB file is stored in this attribute
        db_file = os.path.basename(backup.backup_path_db)

        return {
            "message": "Backup created successfully.<br>Download them from \"Download Backups\"."
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Manual Backup Failed")
        frappe.throw("Backup failed. Check error logs.")
