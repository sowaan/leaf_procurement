# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_filters(filters):
	conditions = ""
	params = {}

	if not filters:
		filters = frappe._dict()

	# Date filter
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND gtn.date BETWEEN %(from_date)s AND %(to_date)s"
		params["from_date"] = filters["from_date"]
		params["to_date"] = filters["to_date"]

	# GTN filter
	if filters.get("gtn"):
		conditions += " AND gtn.name = %(gtn)s"
		params["gtn"] = filters["gtn"]

	# Depot MultiSelectList
	depot_list = filters.get("depot") or []
	if depot_list:
		placeholders = ', '.join([f"%({f'depot_{i}'})s" for i in range(len(depot_list))])
		conditions += f" AND gtn.location_warehouse IN ({placeholders})"
		for i, val in enumerate(depot_list):
			params[f"depot_{i}"] = val

	# Warehouse MultiSelectList
	warehouse_list = filters.get("warehouse") or []
	if warehouse_list:
		placeholders = ', '.join([f"%({f'warehouse_{i}'})s" for i in range(len(warehouse_list))])
		conditions += f" AND ba.location_warehouse IN ({placeholders})"
		for i, val in enumerate(warehouse_list):
			params[f"warehouse_{i}"] = val

	return conditions, params


def get_columns():
	return [
		{"label": "BALE ID", "fieldname": "bale_barcode", "fieldtype": "Data", "width": 120},
		{"label": "Depot", "fieldname": "location_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 140},
		{"label": "Warehouse", "fieldname": "l_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 140},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": "TSA#", "fieldname": "tsa", "fieldtype": "Data", "width": 140},
		{"label": "GTN", "fieldname": "gtn", "fieldtype": "Link", "options": "Goods Transfer Note", "width": 180},
		{"label": "Truck Number", "fieldname": "truck_number", "fieldtype": "Data", "width": 130},
		{"label": "Advance Weight", "fieldname": "advance_weight", "fieldtype": "Float", "width": 130},
		{"label": "Re-Weight", "fieldname": "re_weight", "fieldtype": "Float", "width": 130},
		{"label": "Weight Difference", "fieldname": "weight_difference", "fieldtype": "Float", "width": 150},
		{"label": "Remarks", "fieldname": "remarks", "fieldtype": "Data", "width": 200},
		{"label": "Bales", "fieldname": "bales", "fieldtype": "Int", "width": 80},
	]


def get_data(filters):
	conditions, sql_params = get_filters(filters)

	data = frappe.db.sql(f"""
SELECT 
    gtn_items.bale_barcode AS bale_barcode,
    gtn.location_warehouse AS location_warehouse,
    ba.location_warehouse AS l_warehouse,
    gtn.date AS date,
    gtn.tsa_number AS tsa,
    gtn.name AS gtn,
    gtn.vehicle_number AS truck_number,
    gtn_items.weight AS advance_weight,
    bad.weight AS re_weight,
    (bad.weight - gtn_items.weight) AS weight_difference,
    bad.bale_remarks AS remarks, 
					  1 AS bales
FROM `tabGoods Transfer Note` gtn
INNER JOIN `tabGoods Transfer Note Items` gtn_items
    ON gtn_items.parent = gtn.name
LEFT JOIN `tabBale Audit Detail` bad
    ON bad.bale_barcode = gtn_items.bale_barcode
LEFT JOIN `tabBale Audit` ba
    ON bad.parent = ba.name
   AND ba.docstatus = 1
WHERE gtn.docstatus = 1
  AND gtn.date BETWEEN '2025-07-01' AND '2025-07-31'
ORDER BY gtn.name, gtn_items.bale_barcode;

	""", sql_params, as_dict=True)
	# data = frappe.db.sql(f"""
	# 	SELECT
	# 		gtni.bale_barcode AS bale_barcode,
	# 		gtn.location_warehouse AS location_warehouse,
	# 		gtn.receiving_location AS l_warehouse,
	# 		gtn.date AS date,
	# 		gtn.tsa_number AS tsa,
	# 		gtn.name AS gtn,
	# 		gtn.vehicle_number AS truck_number,
	# 		ROUND(gtni.weight,2) AS advance_weight,
	# 		ROUND(gtni.audit_weight,2) AS re_weight,
	# 		(gtni.audit_weight - gtni.weight) AS weight_difference,
	# 		gtni.audit_remarks AS remarks,
	# 		1 AS bales
	# 	FROM `tabGoods Transfer Note Items` gtni
	# 	LEFT JOIN `tabGoods Transfer Note` gtn ON gtni.parent = gtn.name
	# 	WHERE gtn.docstatus = 1
	# 	{conditions}
	# 	ORDER BY gtni.bale_barcode
	# """, sql_params, as_dict=True)

	return data
