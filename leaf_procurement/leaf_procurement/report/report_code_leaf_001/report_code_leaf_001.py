# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	inc_rej_bales = filters.get("include_rejected_bales", False)

	grade_filter = ""

	if not inc_rej_bales:
		grade_filter = f" AND LOWER(pii.grade) != 'reject'"

	data = frappe.db.sql(f"""
		WITH 
			grand_today AS (
				SELECT 
					SUM(IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0)) AS total_amount_today
				FROM `tabPurchase Invoice` pi
					LEFT JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
					LEFT JOIN `tabSupplier` supp ON pi.supplier = supp.name
				WHERE pi.docstatus = 1 AND pii.item_group = 'Products'
					AND DATE(pi.posting_date) = %(to_date)s
			),
			grand_todate AS (
				SELECT 
					SUM(IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0)) AS total_amount_todate
				FROM `tabPurchase Invoice` pi
					LEFT JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
					LEFT JOIN `tabSupplier` supp ON pi.supplier = supp.name
				WHERE pi.docstatus = 1 AND pii.item_group = 'Products'
					AND DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s
			)
		SELECT 
			supp.custom_location_warehouse AS depot_name,
			-- Today
			COUNT(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN pii.name ELSE NULL END) AS bales_today,
			SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN IFNULL(pii.qty, 0) ELSE 0 END) AS kgs_today,
			SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN (IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0)) ELSE 0 END) AS amount_today,
			(
				SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN (IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0)) ELSE 0 END)
				/ NULLIF(SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN IFNULL(pii.qty, 0) ELSE 0 END), 0)
			) AS avg_today,
			(
				SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN (IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0)) ELSE 0 END)
				/ NULLIF((SELECT total_amount_today FROM grand_today), 0)
			) * 100 AS percentage_today,

			-- ToDate
			COUNT(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN pii.name ELSE NULL END) AS bales_todate,
			SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(pii.qty, 0) ELSE 0 END) AS kgs_todate,
			SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN (IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0)) ELSE 0 END) AS amount_todate,
			(
				SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN (IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0)) ELSE 0 END)
				/ NULLIF(SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(pii.qty, 0) ELSE 0 END), 0)
			) AS avg_todate,
			(
				SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN (IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0)) ELSE 0 END)
				/ NULLIF((SELECT total_amount_todate FROM grand_todate), 0)
			) * 100 AS percentage_todate

			FROM `tabPurchase Invoice` pi
			JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
			LEFT JOIN `tabSupplier` supp ON pi.supplier = supp.name
			WHERE pi.docstatus = 1 AND pii.item_group = 'Products'
			{grade_filter}
		GROUP BY supp.custom_location_warehouse
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


	total_bales_today = total_kgs_today = total_amount_today = total_avg_today = total_percentage_today = total_bales_todate = total_kgs_todate = total_amount_todate = total_avg_todate = total_percentage_todate = 0



	for row in data:
		total_bales_today += row.bales_today or 0
		total_kgs_today += row.kgs_today or 0
		total_amount_today += row.amount_today or 0
		total_bales_todate += row.bales_todate or 0
		total_kgs_todate += row.kgs_todate or 0
		total_amount_todate += row.amount_todate or 0
		total_percentage_today += row.percentage_today or 0
		total_percentage_todate += row.percentage_todate or 0

	total_avg_today = (total_amount_today / total_kgs_today) if total_kgs_today else 0
	total_avg_todate = (total_amount_todate / total_kgs_todate) if total_kgs_todate else 0

	
	

	# data.append({
	# 	"depot_name": None,
	# 	"bales_today": None,
	# 	"kgs_today": None,
	# 	"amount_today": None,
	# 	"avg_today": None,
	# 	"percentage_today": None,
	# 	"bales_todate": None,
	# 	"kgs_todate": None,
	# 	"amount_todate": None,
	# 	"avg_todate": None,
	# 	"percentage_todate": None
	# })

	data.append({
		"depot_name": "Total",
		"bales_today": total_bales_today,
		"kgs_today": total_kgs_today,
		"amount_today": total_amount_today,
		"avg_today": total_avg_today,
		"percentage_today": round(total_percentage_today),
		"bales_todate": total_bales_todate,
		"kgs_todate": total_kgs_todate,
		"amount_todate": total_amount_todate,
		"avg_todate": total_avg_todate,
		"percentage_todate": round(total_percentage_todate),
		"is_total_row": 1
	})


	return columns, data



