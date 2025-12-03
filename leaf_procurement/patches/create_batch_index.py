import frappe

def execute():
    frappe.db.sql("""ALTER TABLE `tabStock Entry Detail`
                     ADD INDEX IF NOT EXISTS `idx_se_detail_batch_no` (`batch_no`)""")