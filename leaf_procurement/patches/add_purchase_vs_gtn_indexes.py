import frappe


def execute():
    frappe.db.sql("""ALTER TABLE `tabPurchase Invoice`
                     ADD INDEX IF NOT EXISTS `idx_pi_docstatus_posting_date` (`docstatus`, `posting_date`)""")

    frappe.db.sql("""ALTER TABLE `tabPurchase Invoice Item`
                     ADD INDEX IF NOT EXISTS `idx_pii_parent_batch_no` (`parent`, `batch_no`(50))""")

    frappe.db.sql("""ALTER TABLE `tabGoods Transfer Note Items`
                     ADD INDEX IF NOT EXISTS `idx_gtni_parenttype_barcode` (`parenttype`, `bale_barcode`(50))""")

    frappe.db.sql("""ALTER TABLE `tabSupplier`
                     ADD INDEX IF NOT EXISTS `idx_supplier_location_wh` (`custom_location_warehouse`(100))""")

    frappe.db.sql("""ALTER TABLE `tabGoods Transfer Note`
                     ADD INDEX IF NOT EXISTS `idx_gtn_docstatus` (`docstatus`)""")

    # audit_master_report: warehouse filter and grade join
    frappe.db.sql("""ALTER TABLE `tabGoods Transfer Note`
                     ADD INDEX IF NOT EXISTS `idx_gtn_receiving_location` (`receiving_location`(100))""")

    frappe.db.sql("""ALTER TABLE `tabPurchase Invoice Item`
                     ADD INDEX IF NOT EXISTS `idx_pii_grade` (`grade`(100))""")

    # depot_despatch_report
    frappe.db.sql("""ALTER TABLE `tabGoods Transfer Note`
                     ADD INDEX IF NOT EXISTS `idx_gtn_docstatus_date` (`docstatus`, `date`)""")

    frappe.db.sql("""ALTER TABLE `tabGoods Transfer Note`
                     ADD INDEX IF NOT EXISTS `idx_gtn_location_warehouse` (`location_warehouse`(100))""")

    frappe.db.sql("""ALTER TABLE `tabGoods Transfer Note Items`
                     ADD INDEX IF NOT EXISTS `idx_gtni_parent` (`parent`(140))""")
