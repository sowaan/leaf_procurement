# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	conditions = get_conditions(filters)

	data = frappe.db.sql(f"""
SELECT 
			pi.name AS voucher_code, 
			supp.supplier_name AS grower_name,
			supp.custom_father_name AS father_name,
			supp.custom_nic_number AS cnic,
			supp.custom_location_warehouse AS depot,
			pi.posting_date AS purchase_date,
			pi.due_date AS payment_date,
			pi.total_qty AS quantity,
			pi.grand_total AS amount,
			pi.status AS status,
			COUNT(DISTINCT pii.name) AS no_of_bale
		FROM `tabPurchase Invoice` pi
		JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
		LEFT JOIN `tabSupplier` supp ON pi.supplier = supp.name
		WHERE pi.docstatus = 1
		AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
		AND {conditions}
		GROUP BY pi.name
	""", {
		"from_date": from_date,
		"to_date": to_date,
		"depot": filters.get("depot"),
		"grower": filters.get("grower")
	}, as_dict=True)

	columns = [
		{"label": "Voucher Code", "fieldname": "voucher_code", "fieldtype": "Link", "options": "Purchase Invoice", "width": 130},
		{"label": "Grower Name", "fieldname": "grower_name", "fieldtype": "Data", "width": 140},
		{"label": "Father Name", "fieldname": "father_name", "fieldtype": "Data", "width": 140},
		{"label": "CNIC", "fieldname": "cnic", "fieldtype": "Data", "width": 130},
		{"label": "Depot", "fieldname": "depot", "fieldtype": "Link", "options": "Warehouse", "width": 120},
		{"label": "Purchase Date", "fieldname": "purchase_date", "fieldtype": "Date", "width": 120},
		{"label": "Payment Date", "fieldname": "payment_date", "fieldtype": "Date", "width": 120},
		{"label": "Quantity", "fieldname": "quantity", "fieldtype": "Float", "width": 100},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "No Of Bale", "fieldname": "no_of_bale", "fieldtype": "Int", "width": 110},
	]

	return columns, data

def get_conditions(filters):
	conditions = []
	if filters.get("depot"):
		conditions.append("supp.custom_location_warehouse = %(depot)s")
	if filters.get("grower"):
		conditions.append("pi.supplier = %(grower)s")
	return " AND ".join(conditions) if conditions else "1=1"
