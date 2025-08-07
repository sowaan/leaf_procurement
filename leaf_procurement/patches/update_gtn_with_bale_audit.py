import frappe # type: ignore

def execute():
    affected = frappe.db.sql("""
        UPDATE `tabGoods Transfer Note Items` AS gtni
        JOIN `tabBale Audit Detail` AS bad
            ON gtni.bale_barcode = bad.bale_barcode
        SET 
            gtni.audit_weight = bad.weight,
            gtni.audit_remarks = bad.bale_remarks
        WHERE 
            gtni.audit_weight IS NULL
            AND gtni.bale_barcode IS NOT NULL
    """)
    frappe.logger().info(f"{affected} rows updated in Bale Audit Detail via GTN patch")
