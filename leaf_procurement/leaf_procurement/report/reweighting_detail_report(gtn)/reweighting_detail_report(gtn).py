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
	if filters.get("date"):
		conditions += " AND gtn.date = %(date)s"
	if filters.get("depot"):
		conditions += " AND gtn.location_warehouse = %(depot)s"
	return conditions

def get_columns():
	return [
		{"label": "BALE ID", "fieldname": "bale_barcode", "fieldtype": "Data", "width": 120},
		{"label": "Warehouse", "fieldname": "location_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 140},
		{"label": "Location Warehouse", "fieldname": "l_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 140},
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
# SELECT
#     bad.bale_barcode AS bale_barcode,
#     ba.location_warehouse AS location_warehouse,
#     ba.location_warehouse AS l_warehouse,  -- redundant, but kept as per your original query
#     ba.date AS date,
#     bad.tsa_number AS tsa,
#     bad.gtn_number AS gtn,
#     bad.truck_number AS truck_number,
#     bad.advance_weight AS advance_weight,
#     IFNULL(bad.weight, 0) AS re_weight,
#     IFNULL(bad.weight, 0) - bad.advance_weight AS weight_difference,
#     1 AS bales
# FROM `tabBale Audit Detail` AS bad
# LEFT JOIN `tabBale Audit` AS ba ON bad.parent = ba.name
# WHERE ba.docstatus = 1

	data = frappe.db.sql(f"""
		SELECT
			gtni.bale_barcode AS bale_barcode,
			gtn.location_warehouse AS location_warehouse,
			ba.location_warehouse AS l_warehouse,
			gtn.date AS date,
			gtn.tsa_number AS tsa,
			gtn.name AS gtn,
			bag.truck_number AS truck_number,
			gtni.weight AS advance_weight,
			IFNULL(bad.weight, 0) AS re_weight,
			IFNULL(bad.weight, 0) - gtni.weight AS weight_difference,
			1 AS bales
		FROM `tabGoods Transfer Note Items` gtni
		LEFT JOIN `tabGoods Transfer Note` gtn ON gtni.parent = gtn.name
		LEFT JOIN `tabBale Audit Detail` bad ON bad.bale_barcode = gtni.bale_barcode
		LEFT JOIN `tabBale Audit` ba ON bad.parent = ba.name
		LEFT JOIN `tabBale Audit GTN` bag ON bag.parent = ba.name
		WHERE gtn.docstatus = 1
		{conditions}
		ORDER BY gtni.bale_barcode
	""", filters, as_dict=True)

	return data
