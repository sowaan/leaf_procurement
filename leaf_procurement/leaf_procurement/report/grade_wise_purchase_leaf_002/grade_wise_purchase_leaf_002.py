# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	grade_filter = ""

	if filters.get("grade"):
		grade_filter = "AND c.reclassification_grade = %(grade)s"

	data = frappe.db.sql(f"""
		WITH totals AS (
			SELECT
				SUM(CASE WHEN DATE(p.date) = %(to_date)s THEN IFNULL(c.weight, 0) * IFNULL(c.rate, 0) ELSE 0 END) AS total_today,
				SUM(CASE WHEN DATE(p.date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(c.weight, 0) * IFNULL(c.rate, 0) ELSE 0 END) AS total_todate
			FROM `tabBale Weight Info` p
			JOIN `tabBale Weight Detail` c ON p.name = c.parent
			WHERE p.docstatus = 1
			{grade_filter}
		)
		SELECT
			c.reclassification_grade AS grade,

			-- Today
			COUNT(CASE WHEN DATE(p.date) = %(to_date)s THEN c.name ELSE NULL END) AS bales_today,
			SUM(CASE WHEN DATE(p.date) = %(to_date)s THEN IFNULL(c.weight, 0) ELSE 0 END) AS kgs_today,
			SUM(CASE WHEN DATE(p.date) = %(to_date)s THEN (IFNULL(c.weight, 0) * IFNULL(c.rate, 0)) ELSE 0 END) AS amount_today,
			AVG(CASE WHEN DATE(p.date) = %(to_date)s THEN (IFNULL(c.weight, 0) * IFNULL(c.rate, 0)) ELSE NULL END) AS avg_today,
			(
				SUM(CASE WHEN DATE(p.date) = %(to_date)s THEN (IFNULL(c.weight, 0) * IFNULL(c.rate, 0)) ELSE 0 END)
				/ NULLIF((SELECT total_today FROM totals), 0)
			) * 100 AS percentage_today,

			-- ToDate
			COUNT(CASE WHEN DATE(p.date) BETWEEN %(from_date)s AND %(to_date)s THEN c.name ELSE NULL END) AS bales_todate,
			SUM(CASE WHEN DATE(p.date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(c.weight, 0) ELSE 0 END) AS kgs_todate,
			SUM(CASE WHEN DATE(p.date) BETWEEN %(from_date)s AND %(to_date)s THEN (IFNULL(c.weight, 0) * IFNULL(c.rate, 0)) ELSE 0 END) AS amount_todate,
			AVG(CASE WHEN DATE(p.date) BETWEEN %(from_date)s AND %(to_date)s THEN (IFNULL(c.weight, 0) * IFNULL(c.rate, 0)) ELSE NULL END) AS avg_todate,
			(
				SUM(CASE WHEN DATE(p.date) BETWEEN %(from_date)s AND %(to_date)s THEN (IFNULL(c.weight, 0) * IFNULL(c.rate, 0)) ELSE 0 END)
				/ NULLIF((SELECT total_todate FROM totals), 0)
			) * 100 AS percentage_todate

		FROM `tabBale Weight Info` p
		JOIN `tabBale Weight Detail` c ON p.name = c.parent
		WHERE p.docstatus = 1
		{grade_filter}
		GROUP BY c.reclassification_grade
	""", {
		"from_date": from_date,
		"to_date": to_date,
		"grade": filters.get("grade")
	}, as_dict=True)

	columns = [
		{"label": "Grade", "fieldname": "grade", "fieldtype": "Data", "width": 100},
		{"label": "Bales Today", "fieldname": "bales_today", "fieldtype": "Int", "width": 120},
		{"label": "Kgs Today", "fieldname": "kgs_today", "fieldtype": "Float", "width": 120},
		{"label": "Amount Today", "fieldname": "amount_today", "fieldtype": "Currency", "width": 120},
		{"label": "Avg Today", "fieldname": "avg_today", "fieldtype": "Currency", "width": 120},
		{"label": "Percentage Today", "fieldname": "percentage_today", "fieldtype": "Percent", "width": 140},
		{"label": "Bales ToDate", "fieldname": "bales_todate", "fieldtype": "Int", "width": 120},
		{"label": "Kgs ToDate", "fieldname": "kgs_todate", "fieldtype": "Float", "width": 120},
		{"label": "Amount ToDate", "fieldname": "amount_todate", "fieldtype": "Currency", "width": 120},
		{"label": "Avg ToDate", "fieldname": "avg_todate", "fieldtype": "Currency", "width": 120},
		{"label": "Percentage ToDate", "fieldname": "percentage_todate", "fieldtype": "Percent", "width": 140},
	]

	return columns, data
