# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")


	conditions = get_conditions(filters)

	# Constructing the WHERE clause dynamically
	# where_clauses = [
	# 	"pi.docstatus = 1",
	# 	"pii.item_group = 'Products'",
	# 	"pi.posting_date BETWEEN %(from_date)s AND %(to_date)s"
	# ]

	# if conditions:
	# 	where_clauses.append(conditions)

	# final_where_clause = " AND ".join(where_clauses)

	# data = frappe.db.sql(f"""
    #     SELECT
    #         pi.name AS voucher_code,
    #         supp.supplier_name AS grower_name,
    #         supp.custom_father_name AS father_name,
    #         supp.custom_nic_number AS cnic,
    #         supp.custom_location_warehouse AS depot,
    #         pi.posting_date AS purchase_date,
    #         pi.due_date AS payment_date,
    #         SUM(pii.qty) AS quantity,
    #         pi.grand_total AS amount,
    #         pi.status AS status,
    #         COUNT(pii.name) AS no_of_bale -- Assuming pii.name is unique for each line item within an invoice
    #     FROM `tabPurchase Invoice` pi
    #     JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
    #     LEFT JOIN `tabSupplier` supp ON pi.supplier = supp.name
    #     WHERE {final_where_clause}
    #     GROUP BY
    #         pi.name,
    #         supp.supplier_name,
    #         supp.custom_father_name,
    #         supp.custom_nic_number,
    #         supp.custom_location_warehouse,
    #         pi.posting_date,
    #         pi.due_date,
    #         pi.grand_total,
    #         pi.status
    #     ORDER BY
    #         pi.posting_date DESC, pi.name DESC
    # """, {
    #     "from_date": from_date,
    #     "to_date": to_date,
    #     "depot": filters.get("depot"), # These parameters are correctly handled by get_conditions
    #     "grower": filters.get("grower") # if they are part of the 'conditions' string
    # }, as_dict=True)

	data = frappe.db.sql(f"""
		SELECT 
			pi.name AS voucher_code, 
			supp.supplier_name AS grower_name,
			supp.custom_father_name AS father_name,
			supp.custom_nic_number AS cnic,
			supp.custom_location_warehouse AS depot,
			pi.posting_date AS purchase_date,
			pi.due_date AS payment_date,
			sum(pii.qty) AS quantity,
			pi.grand_total AS amount,
			pi.status AS status,
			COUNT(DISTINCT pii.name) AS no_of_bale
		FROM `tabPurchase Invoice` pi
		JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
		LEFT JOIN `tabSupplier` supp ON pi.supplier = supp.name
		WHERE pi.docstatus = 1 AND pii.item_group = 'Products'
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
	inc_rej_bales = filters.get("include_rejected_bales", False)
	if filters.get("depot"):
		conditions.append("supp.custom_location_warehouse = %(depot)s")
	if filters.get("grower"):
		conditions.append("pi.supplier = %(grower)s")
	if not inc_rej_bales:
		conditions.append("LOWER(pii.grade) != 'reject'")
	return " AND ".join(conditions) if conditions else "1=1"
