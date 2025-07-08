# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 150},
		{"label": "Number of Bales", "fieldname": "number_of_bales", "fieldtype": "Int", "width": 130},
		{"label": "Item Grade", "fieldname": "item_grade", "fieldtype": "Data", "width": 100},
		{"label": "Item Sub Grade", "fieldname": "item_sub_grade", "fieldtype": "Data", "width": 120},
		{"label": "Advance Weight (Kgs)", "fieldname": "advance_weight", "fieldtype": "Float", "width": 150},
		{"label": "Re-Weight (Kgs)", "fieldname": "re_weight", "fieldtype": "Float", "width": 140},
		{"label": "Difference (Kgs)", "fieldname": "difference", "fieldtype": "Float", "width": 130},
		{"label": "Variance (%)", "fieldname": "variance_percent", "fieldtype": "Percent", "width": 120},
	]


def get_data(filters):
	conditions = []

	if filters.get("from_date"):
		conditions.append("grn.date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("grn.date <= %(to_date)s")
	if filters.get("grade"):
		conditions.append("gtni.item_grade = %(grade)s")
	if filters.get("sub_grade"):
		conditions.append("gtni.item_sub_grade = %(sub_grade)s")
	if filters.get("warehouse"):
		conditions.append("grn.location_warehouse = %(warehouse)s")

	where_clause = " AND ".join(conditions)
	if where_clause:
		where_clause = "WHERE " + where_clause

	query = f"""
		SELECT
			grn.location_warehouse AS warehouse,
			COUNT(gtni.name) AS number_of_bales,
			gtni.item_grade AS item_grade,
			gtni.item_sub_grade AS item_sub_grade,
			SUM(gtni.weight) AS advance_weight,
			SUM(IFNULL(bad.weight, 0)) AS re_weight
		FROM `tabGoods Receiving Note` grn
		LEFT JOIN `tabGoods Transfer Note Items` gtni ON grn.name = gtni.parent
		LEFT JOIN `tabBale Audit Detail` bad ON gtni.bale_barcode = bad.bale_barcode
		{where_clause}
		GROUP BY grn.location_warehouse, gtni.item_grade, gtni.item_sub_grade
	"""

	raw_data = frappe.db.sql(query, filters, as_dict=True)

	for row in raw_data:
		advance_weight = flt(row.advance_weight)
		re_weight = flt(row.re_weight)
		difference = re_weight - advance_weight

		row["difference"] = difference
		row["variance_percent"] = (difference / advance_weight * 100) if advance_weight else 0

	return raw_data
