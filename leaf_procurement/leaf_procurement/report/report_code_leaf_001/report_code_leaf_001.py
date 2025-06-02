# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	data = frappe.db.sql("""
		WITH 
			grand_today AS (
				SELECT 
					SUM(IFNULL(child.weight, 0) * IFNULL(child.rate, 0)) AS total_amount_today
				FROM `tabBale Weight Info` AS parent
				JOIN `tabBale Weight Detail` AS child ON parent.name = child.parent
				WHERE parent.docstatus = 1 AND DATE(parent.date) = %(to_date)s
			),
			grand_todate AS (
				SELECT 
					SUM(IFNULL(child.weight, 0) * IFNULL(child.rate, 0)) AS total_amount_todate
				FROM `tabBale Weight Info` AS parent
				JOIN `tabBale Weight Detail` AS child ON parent.name = child.parent
				WHERE parent.docstatus = 1 AND DATE(parent.date) BETWEEN %(from_date)s AND %(to_date)s
			)

		SELECT 
			parent.location_warehouse AS depot_name,

			-- Today
			COUNT(CASE WHEN DATE(parent.date) = %(to_date)s THEN child.name ELSE NULL END) AS bales_today,
			SUM(CASE WHEN DATE(parent.date) = %(to_date)s THEN IFNULL(child.weight, 0) ELSE 0 END) AS kgs_today,
			SUM(CASE WHEN DATE(parent.date) = %(to_date)s THEN (IFNULL(child.weight, 0) * IFNULL(child.rate, 0)) ELSE 0 END) AS amount_today,
			(
				SUM(CASE WHEN DATE(parent.date) = %(to_date)s THEN (IFNULL(child.weight, 0) * IFNULL(child.rate, 0)) ELSE 0 END)
				/ NULLIF(SUM(CASE WHEN DATE(parent.date) = %(to_date)s THEN IFNULL(child.weight, 0) ELSE 0 END), 0)
			) AS avg_today,
			(
				SUM(CASE WHEN DATE(parent.date) = %(to_date)s THEN (IFNULL(child.weight, 0) * IFNULL(child.rate, 0)) ELSE 0 END)
				/ NULLIF((SELECT total_amount_today FROM grand_today), 0)
			) * 100 AS percentage_today,

			-- ToDate
			COUNT(CASE WHEN DATE(parent.date) BETWEEN %(from_date)s AND %(to_date)s THEN child.name ELSE NULL END) AS bales_todate,
			SUM(CASE WHEN DATE(parent.date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(child.weight, 0) ELSE 0 END) AS kgs_todate,
			SUM(CASE WHEN DATE(parent.date) BETWEEN %(from_date)s AND %(to_date)s THEN (IFNULL(child.weight, 0) * IFNULL(child.rate, 0)) ELSE 0 END) AS amount_todate,
			(
				SUM(CASE WHEN DATE(parent.date) BETWEEN %(from_date)s AND %(to_date)s THEN (IFNULL(child.weight, 0) * IFNULL(child.rate, 0)) ELSE 0 END)
				/ NULLIF(SUM(CASE WHEN DATE(parent.date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(child.weight, 0) ELSE 0 END), 0)
			) AS avg_todate,
			(
				SUM(CASE WHEN DATE(parent.date) BETWEEN %(from_date)s AND %(to_date)s THEN (IFNULL(child.weight, 0) * IFNULL(child.rate, 0)) ELSE 0 END)
				/ NULLIF((SELECT total_amount_todate FROM grand_todate), 0)
			) * 100 AS percentage_todate

		FROM `tabBale Weight Info` AS parent
		JOIN `tabBale Weight Detail` AS child ON parent.name = child.parent
		WHERE parent.docstatus = 1
		GROUP BY parent.location_warehouse
	""", {
		"from_date": from_date,
		"to_date": to_date
	}, as_dict=True)

	columns = [
		{"label": "Depot Name", "fieldname": "depot_name", "fieldtype": "Data", "width": 120},

		# Today
		{"label": "Bales (Today)", "fieldname": "bales_today", "fieldtype": "Int", "width": 120},
		{"label": "Kgs (Today)", "fieldname": "kgs_today", "fieldtype": "Float", "width": 110},
		{"label": "Amount (Today)", "fieldname": "amount_today", "fieldtype": "Currency", "width": 120},
		{"label": "Avg (Today)", "fieldname": "avg_today", "fieldtype": "Currency", "width": 110},
		{"label": "% (Today)", "fieldname": "percentage_today", "fieldtype": "Percent", "width": 100},

		# ToDate
		{"label": "Bales (ToDate)", "fieldname": "bales_todate", "fieldtype": "Int", "width": 120},
		{"label": "Kgs (ToDate)", "fieldname": "kgs_todate", "fieldtype": "Float", "width": 110},
		{"label": "Amount (ToDate)", "fieldname": "amount_todate", "fieldtype": "Currency", "width": 120},
		{"label": "Avg (ToDate)", "fieldname": "avg_todate", "fieldtype": "Currency", "width": 110},
		{"label": "% (ToDate)", "fieldname": "percentage_todate", "fieldtype": "Percent", "width": 100},
	]

	return columns, data



