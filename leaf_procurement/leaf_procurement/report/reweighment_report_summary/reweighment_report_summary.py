# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_filters(filters):
	conditions = ""
	if not filters:
		filters = frappe._dict()
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND gtn.date BETWEEN %(from_date)s AND %(to_date)s"
	elif filters.get("from_date"):
		conditions += " AND gtn.date >= %(from_date)s"
	elif filters.get("to_date"):
		conditions += " AND gtn.date <= %(to_date)s"
	if filters.get("depot"):
		conditions += " AND gtn.location_warehouse = %(depot)s"
	return conditions

def get_columns():
	return [
		{"label": "GTN Code", "fieldname": "gtn_code", "fieldtype": "Link", "options": "Goods Transfer Note", "width": 150},
		{"label": "Depot Name", "fieldname": "depot_name", "fieldtype": "Link", "options": "Warehouse", "width": 150},
		{"label": "Total No. of Bales", "fieldname": "t_no_of_bale", "fieldtype": "Int", "width": 130},
		{"label": "GTN Advance Weight", "fieldname": "gtn_adv_wt", "fieldtype": "Float", "width": 130},
		{"label": "Audit No. of Bales", "fieldname": "no_of_bale", "fieldtype": "Int", "width": 130},
		{"label": "Advance weight", "fieldname": "advance_wt", "fieldtype": "Float", "width": 130},
		{"label": "Re-weighment", "fieldname": "re_weighment", "fieldtype": "Float", "width": 130},
		{"label": "Difference", "fieldname": "diff", "fieldtype": "Float", "width": 130}
	]

def get_data(filters):
	conditions = get_filters(filters)
	data = frappe.db.sql(f"""
		SELECT
			gtn.name AS gtn_code,
			gtn.location_warehouse AS depot_name,
			COUNT(DISTINCT gtni.name) AS t_no_of_bale,
			SUM(gtni.weight) AS gtn_adv_wt,
			COUNT(DISTINCT bad.name) AS no_of_bale,
			SUM(CASE WHEN bad.name IS NOT NULL THEN gtni.weight ELSE 0 END) AS advance_wt,
			IFNULL(SUM(bad.weight), 0) AS re_weighment,
			IFNULL(SUM(bad.weight - gtni.weight), 0) AS diff
		FROM `tabGoods Transfer Note` gtn
		LEFT JOIN `tabGoods Transfer Note Items` gtni ON gtn.name = gtni.parent
		LEFT JOIN `tabBale Audit Detail` bad ON gtni.bale_barcode = bad.bale_barcode
		WHERE gtn.docstatus = 1
		{conditions}
		GROUP BY gtn.name
		ORDER BY gtn.name
	""", filters, as_dict=True)
	return data