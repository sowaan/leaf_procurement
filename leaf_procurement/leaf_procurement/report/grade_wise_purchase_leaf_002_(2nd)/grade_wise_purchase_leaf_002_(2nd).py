# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	inc_rej_bales = filters.get("include_rejected_bales", False)

	params = {
        "from_date": from_date,
        "to_date": to_date
    }
    
    # Use a dynamic grade column name securely
	grade_mapping = {"Item Grade": "grade", "Reclassification Grade": "reclassification_grade"}
	grade_current = grade_mapping.get(filters.get("grade_type"), "grade")
    
	# Build filter conditions and parameters
	conditions = []
	if filters.get("supplier"):
		conditions.append("pi.supplier IN %(supplier)s")
		params["supplier"] = filters.get("supplier")

	if filters.get("warehouse"):
		conditions.append("supp.custom_location_warehouse = %(warehouse)s")
		params["warehouse"] = filters.get("warehouse")
		
	if not inc_rej_bales:
		conditions.append(f"LOWER(pii.{grade_current}) != 'reject'")

	if filters.get("grade"):
		conditions.append(f"pii.{grade_current} IN %(grade)s")
		params["grade"] = filters.get("grade")

	# Combine all conditions into a single string
	filter_str = (" AND " + " AND ".join(conditions)) if conditions else ""

	# --- Optimized SQL Query ---
	data = frappe.db.sql(f"""
		-- Step 1: Get all filtered base data in a single pass.
		-- All filters (date, supplier, warehouse, grade) are applied here once.
		WITH base_data AS (
			SELECT
				pi.posting_date,
				pii.qty,
				pii.rate,
				pii.{grade_current} AS grade,
				supp.custom_location_warehouse AS warehouse
			FROM `tabPurchase Invoice` pi
			JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
			LEFT JOIN `tabSupplier` supp ON pi.supplier = supp.name
			WHERE pi.docstatus = 1
				AND pii.item_group = 'Products'
				-- This date filtering is SARGable and allows index usage
				AND pi.posting_date >= %(from_date)s
				AND pi.posting_date < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
				{filter_str}
		),
		-- Step 2: Aggregate the filtered data by group.
		grouped_data AS (
			SELECT
				warehouse,
				grade,
				-- Today's aggregates
				COUNT(CASE WHEN posting_date >= %(to_date)s THEN 1 END) AS bales_today,
				SUM(CASE WHEN posting_date >= %(to_date)s THEN qty ELSE 0 END) AS kgs_today,
				SUM(CASE WHEN posting_date >= %(to_date)s THEN qty * rate ELSE 0 END) AS amount_today,
				-- To-Date aggregates
				COUNT(*) AS bales_todate,
				SUM(qty) AS kgs_todate,
				SUM(qty * rate) AS amount_todate
			FROM base_data
			GROUP BY warehouse, grade
		)
		-- Step 3: Final selection and percentage calculation using window functions.
		-- This is much more efficient than using subqueries.
		SELECT
			warehouse,
			grade,
			bales_today,
			kgs_today,
			amount_today,
			amount_today / NULLIF(kgs_today, 0) AS avg_today,
			(amount_today * 100.0) / NULLIF(SUM(amount_today) OVER(), 0) AS percentage_today,
			
			bales_todate,
			kgs_todate,
			amount_todate,
			amount_todate / NULLIF(kgs_todate, 0) AS avg_todate,
			(amount_todate * 100.0) / NULLIF(SUM(amount_todate) OVER(), 0) AS percentage_todate

		FROM grouped_data
		-- The HAVING clause from the original query can be replaced by a WHERE
		WHERE bales_today > 0 OR bales_todate > 0
		ORDER BY warehouse, grade
	""", params, as_dict=True)

	# supplier_filter = "AND 1=1"
	# warehouse_filter = " AND 1=1"
	# grade_filter = " AND 1=1"

	# grade_mapping = {
	# 	"Item Grade": "grade",
	# 	"Reclassification Grade": "reclassification_grade"
	# }
	# grade_current = grade_mapping.get(filters.get("grade_type"), "grade")


	# if filters.get("supplier"):
	# 	supplier_list = ", ".join([f"'{s}'" for s in filters.get("supplier")])
	# 	supplier_filter = f" AND pi.supplier IN ({supplier_list})"

	

	# if filters.get("warehouse"):
	# 	warehouse_filter = f" AND supp.custom_location_warehouse = %(warehouse)s"
	
	
	# if not inc_rej_bales:
	# 	grade_filter += f" AND LOWER(pii.{grade_current}) != 'reject'"
	
	# if filters.get("grade"):
	# 	grade_list = ", ".join([f"'{g}'" for g in filters.get("grade")])
	# 	grade_filter = f" AND pii.{grade_current} IN ({grade_list})"
	
	
	

	
	
	# data = frappe.db.sql(f"""
	# 	WITH totals AS (
	# 		SELECT
	# 			SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0) ELSE 0 END) AS total_today,
	# 			SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0) ELSE 0 END) AS total_todate
	# 		FROM `tabPurchase Invoice` pi
	# 		JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
	# 		WHERE pi.docstatus = 1 AND pii.item_group = 'Products'
	# 	)

	# 	SELECT
	# 		pii.{grade_current} AS grade,
	# 		supp.custom_location_warehouse AS warehouse,
			
	# 		-- Today
	# 		COUNT(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN pii.name END) AS bales_today,
	# 		SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN IFNULL(pii.qty, 0) END) AS kgs_today,
	# 		SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0) END) AS amount_today,
	# 		CASE
	# 			WHEN SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN IFNULL(pii.qty, 0) END) = 0 THEN 0
	# 			ELSE
	# 				SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0) END) /
	# 				SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN IFNULL(pii.qty, 0) END)
	# 		END AS avg_today,
	# 		(
	# 			SUM(CASE WHEN DATE(pi.posting_date) = %(to_date)s THEN IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0) END)
	# 			/ NULLIF((SELECT total_today FROM totals), 0)
	# 		) * 100 AS percentage_today,

	# 		-- To Date
	# 		COUNT(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN pii.name END) AS bales_todate,
	# 		SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(pii.qty, 0) END) AS kgs_todate,
	# 		SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0) END) AS amount_todate,
	# 		CASE
	# 			WHEN SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(pii.qty, 0) END) = 0 THEN 0
	# 			ELSE
	# 				SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0) END) /
	# 				SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(pii.qty, 0) END)
	# 		END AS avg_todate,
	# 		(
	# 			SUM(CASE WHEN DATE(pi.posting_date) BETWEEN %(from_date)s AND %(to_date)s THEN IFNULL(pii.qty, 0) * IFNULL(pii.rate, 0) END)
	# 			/ NULLIF((SELECT total_todate FROM totals), 0)
	# 		) * 100 AS percentage_todate

	# 	FROM `tabPurchase Invoice` pi
	# 	JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
	# 	LEFT JOIN `tabSupplier` supp ON pi.supplier = supp.name
	# 	WHERE pi.docstatus = 1 AND pii.item_group = 'Products'
	# 	{supplier_filter}
	# 	{warehouse_filter}
	# 	{grade_filter}
	# 	GROUP BY supp.custom_location_warehouse, pii.{grade_current}
	# 	HAVING bales_today > 0 OR bales_todate > 0
	# 	ORDER BY supp.custom_location_warehouse, pii.{grade_current}
	# """, {
	# 	"from_date": from_date,
	# 	"to_date": to_date,
	# 	"warehouse": filters.get("warehouse")
	# }, as_dict=True)


	columns = [
		{"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
		{"label": filters.get("grade_type"), "fieldname": "grade", "fieldtype": "Link", "options": filters.get("grade_type"), "width": 120 if filters.get("grade_type") == "Item Grade" else 172, "align": "left"},
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

	totals = {
		"bales_today": 0,
		"kgs_today": 0,
		"amount_today": 0,
		"percentage_today": 0,
		"bales_todate": 0,
		"kgs_todate": 0,
		"amount_todate": 0,
		"percentage_todate": 0
	}

	for row in data:
		totals["bales_today"] += row.get("bales_today", 0) or 0
		totals["kgs_today"] += row.get("kgs_today", 0) or 0
		totals["amount_today"] += row.get("amount_today", 0) or 0
		totals["percentage_today"] += row.get("percentage_today", 0) or 0
		totals["bales_todate"] += row.get("bales_todate", 0) or 0
		totals["kgs_todate"] += row.get("kgs_todate", 0) or 0
		totals["amount_todate"] += row.get("amount_todate", 0) or 0
		totals["percentage_todate"] += row.get("percentage_todate", 0) or 0

	data.append({
		"warehouse": "Total",
		"grade": "",
		"sub_grade": "",
		"reclassification_grade": "",
		"bales_today": totals["bales_today"],
		"kgs_today": totals["kgs_today"],
		"amount_today": totals["amount_today"],
		"avg_today": (totals["amount_today"] / (totals["kgs_today"] or 1)),
		"percentage_today": round(totals["percentage_today"]),
		"bales_todate": totals["bales_todate"],
		"kgs_todate": totals["kgs_todate"],
		"amount_todate": totals["amount_todate"],
		"avg_todate": (totals["amount_todate"] / (totals["kgs_todate"] or 1)),
		"percentage_todate": round(totals["percentage_todate"]),
		"is_total_row": 1
	})
	return columns, data
	
