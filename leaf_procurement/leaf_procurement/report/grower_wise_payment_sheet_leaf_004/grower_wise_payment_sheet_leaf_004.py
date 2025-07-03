# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	due_date = filters.get("due_date")

	conditions = get_conditions(filters)

	data = frappe.db.sql(f"""
		SELECT 
			pi.name AS voucher_code,
			pi.custom_stationary,
			supp.supplier_name AS grower_name,
			supp.custom_father_name AS father_name,
			supp.custom_nic_number AS cnic,
			supp.custom_location_warehouse AS depot,
			pi.posting_date AS purchase_date,
			pi.due_date AS payment_date,
			SUM(CASE WHEN pii.item_group = 'Products' THEN pii.amount ELSE 0 END) AS tob_amount,
			SUM(CASE WHEN pii.item_group != 'Products' THEN pii.amount ELSE 0 END) AS tc_amount
		FROM `tabPurchase Invoice` pi
			LEFT JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
			LEFT JOIN `tabSupplier` supp ON pi.supplier = supp.name
		WHERE pi.docstatus = 1
			AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND {conditions}
		GROUP BY pi.name
	""", {
		"from_date": from_date,
		"to_date": to_date,
		"depot": filters.get("depot"),
		"grower": filters.get("grower"),
		"due_date": filters.get("due_date")
	}, as_dict=True)

	columns = [
		{"label": "Voucher Code", "fieldname": "voucher_code", "fieldtype": "Link", "options": "Purchase Invoice", "width": 130},
		{"label": "Stationary No", "fieldname": "custom_stationary", "fieldtype": "Data", "width": 130},
		{"label": "Grower Name", "fieldname": "grower_name", "fieldtype": "Data", "width": 140},
		{"label": "Father Name", "fieldname": "father_name", "fieldtype": "Data", "width": 140},
		{"label": "CNIC", "fieldname": "cnic", "fieldtype": "Data", "width": 130},
		{"label": "Depot", "fieldname": "depot", "fieldtype": "Link", "options": "Warehouse", "width": 120},
		{"label": "Purchase Date", "fieldname": "purchase_date", "fieldtype": "Date", "width": 120},
		{"label": "Due Date", "fieldname": "payment_date", "fieldtype": "Date", "width": 120},
		{"label": "Transport Charges", "fieldname": "tc_amount", "fieldtype": "Float", "width": 100},
		{"label": "Amount", "fieldname": "tob_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Paid On/By", "fieldname": None, "fieldtype": "Data", "width": 120},
		{"label": "Grower Signature/LTI", "fieldname": None, "fieldtype": "Data", "width": 120},
		
	]

	return columns, data

def get_conditions(filters):
	conditions = []
	if filters.get("depot"):
		conditions.append("supp.custom_location_warehouse = %(depot)s")
	if filters.get("grower"):
		conditions.append("pi.supplier = %(grower)s")
	if filters.get("due_date"):
		conditions.append("pi.due_date = %(due_date)s")
	return " AND ".join(conditions) if conditions else "1=1"
