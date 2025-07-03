import frappe

def execute():
 frappe.db.set_value('Report', 'Grower Wise Purchase Leaf 003', 'add_total_row', 1)
 frappe.db.commit()

 # your patch code here
