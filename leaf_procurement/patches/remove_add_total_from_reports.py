import frappe

def execute():
 frappe.db.set_value('Report', 'Report Code Leaf 001', 'add_total_row', 0)
 frappe.db.set_value('Report', 'Grade Wise Purchase Leaf 002', 'add_total_row', 0)
 frappe.db.set_value('Report', 'Grower Wise Purchase Leaf 003', 'add_total_row', 0)
 frappe.db.commit()

 # your patch code here
