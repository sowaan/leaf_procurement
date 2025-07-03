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
		conditions += " AND ba.date BETWEEN %(from_date)s AND %(to_date)s"
	elif filters.get("from_date"):
		conditions += " AND ba.date >= %(from_date)s"
	elif filters.get("to_date"):
		conditions += " AND ba.date <= %(to_date)s"
	if filters.get("depot"):
		conditions += " AND ba.location_warehouse = %(depot)s"
	return conditions

def get_columns():
	return [
		{"label": "BALE ID", "fieldname": "bale_barcode", "fieldtype": "Data", "width": 120},
		{"label": "Warehouse", "fieldname": "location_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 140},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": "TSA#", "fieldname": "tsa", "fieldtype": "Data", "width": 140},
		{"label": "GTN", "fieldname": "gtn", "fieldtype": "Link", "options": "Goods Transfer Note", "width": 180},
		{"label": "Truck Number", "fieldname": "truck_number", "fieldtype": "Data", "width": 130},
		{"label": "Advance Weight", "fieldname": "advance_weight", "fieldtype": "Float", "width": 130},
		{"label": "Re-Weight", "fieldname": "re_weight", "fieldtype": "Float", "width": 130},
		{"label": "Weight Difference", "fieldname": "weight_difference", "fieldtype": "Float", "width": 150},
		{"label": "Bales", "fieldname": "bales", "fieldtype": "Int", "width": 80},
	]


def get_data(filters):
	conditions = get_filters(filters) 
	data = frappe.db.sql(f"""
		SELECT
			bad.bale_barcode AS bale_barcode,
			ba.location_warehouse AS location_warehouse,
			ba.date AS date,
			gtn.tsa_number AS tsa,
			gtn.name AS gtn,
			bag.truck_number AS truck_number,
			gtni.weight AS advance_weight,
			bad.weight AS re_weight,
			(bad.weight - gtni.weight) AS weight_difference,
			1 AS bales
		FROM `tabBale Audit` ba
		LEFT JOIN `tabBale Audit Detail` bad ON ba.name = bad.parent
		LEFT JOIN `tabGoods Transfer Note Items` gtni ON bad.bale_barcode = gtni.bale_barcode
		LEFT JOIN `tabGoods Transfer Note` gtn ON gtni.parent = gtn.name
		LEFT JOIN `tabBale Audit GTN` bag ON bag.parent = ba.name
		WHERE ba.docstatus = 1
		{conditions}
		GROUP BY bad.bale_barcode
		ORDER BY bad.bale_barcode
	""", filters, as_dict=True)
	return data