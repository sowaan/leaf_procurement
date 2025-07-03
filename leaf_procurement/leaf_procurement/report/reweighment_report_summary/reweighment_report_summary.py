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
		{"label": "GTN Code", "fieldname": "gtn_code", "fieldtype": "Link", "options": "Goods Transfer Note", "width": 130},
		{"label": "Depot Name", "fieldname": "depot_name", "fieldtype": "Link", "options": "Warehouse", "width": 130},
		{"label": "GTN No. of Bales", "fieldname": "no_of_bale", "fieldtype": "Int", "width": 130},
		{"label": "GTN Advance Weight", "fieldname": "gtn_adv_wt", "fieldtype": "Float", "width": 130},
		{"label": "Re-weighment Advance weight", "fieldname": "re_weighment_advance_wt", "fieldtype": "Float", "width": 130},
		{"label": "Re-weighment", "fieldname": "re_weighment", "fieldtype": "Float", "width": 130},
		{"label": "Difference", "fieldname": "diff", "fieldtype": "Float", "width": 130},
	]

def get_data(filters):
	conditions = get_filters(filters)
	data = frappe.db.sql("""
		SELECT
			gtn.name AS gtn_code,
			gtn.location_warehouse AS depot_name,
			COUNT(DISTINCT gtni.name) AS no_of_bale
			SUM(gtni.weight) AS gtn_adv_wt,
			supp.custom_nic_number AS cnic,
			supp.custom_location_warehouse AS depot,
			supp.custom_location_warehouse AS depot,
		FROM `tabGoods Transfer Note` gtn
		LEFT JOIN `tabGoods Transfer Note Items` gtni ON gtn.name = gtni.parent 
		LEFT JOIN `tabBale Audit GTN` ba_gtn ON gtn.name = ba_gtn.gtn_number
		LEFT JOIN `tabBale Audit Detail` bad ON bad.parent = ba_gtn.parent
		LEFT JOIN `tabBale Audit` ba ON gtn.name = ba.gtn
		WHERE gtn.docstatus = 1
		{conditions}
		GROUP BY gtn_code
		ORDER BY gtn_code
	""".format(conditions=conditions), filters, as_dict=True)
	
	