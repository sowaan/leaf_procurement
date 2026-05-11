# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 180},
		{"label": "Purchase (Grower)", "fieldname": "purchase_grower", "fieldtype": "Int", "width": 130},
		{"label": "Purchase (Trader)", "fieldname": "purchase_trader", "fieldtype": "Int", "width": 130},
		{"label": "Total Bales Purchased", "fieldname": "total_bales_purchased", "fieldtype": "Int", "width": 150},
		{"label": "Total Purchase Weight (Kgs)", "fieldname": "total_purchase_weight", "fieldtype": "Float", "width": 170, "precision": 2},
		{"label": "Advance Weight (Kgs)", "fieldname": "advance_weight", "fieldtype": "Float", "width": 140, "precision": 2},
		{"label": "Re-Weight (Kgs)", "fieldname": "re_weight", "fieldtype": "Float", "width": 140, "precision": 2},
		{"label": "Difference (Kgs)", "fieldname": "difference_kgs", "fieldtype": "Float", "width": 130, "precision": 2},
		{"label": "Variance in %", "fieldname": "variance_percent", "fieldtype": "Percent", "width": 110, "precision": 2},
		{"label": "Variance in (Kgs)", "fieldname": "variance_in_kgs", "fieldtype": "Float", "width": 130, "precision": 2},
		{"label": "Total Variance (Kg)", "fieldname": "forecasted_wastage", "fieldtype": "Float", "width": 160, "precision": 2},
	]


def get_conditions(filters):
	conditions = [
		"pi.docstatus = 1",
		"IFNULL(pii.item_group, '') = 'Products'",
		"IFNULL(pii.batch_no, '') != ''",
		"IFNULL(pii.qty, 0) > 0",
	]
	params = {}

	if filters.get("from_date"):
		conditions.append("pi.posting_date >= %(from_date)s")
		params["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("pi.posting_date <= %(to_date)s")
		params["to_date"] = filters.to_date

	if filters.get("warehouse"):
		conditions.append(
			"COALESCE(NULLIF(pii.warehouse, ''), NULLIF(pi.set_warehouse, '')) = %(warehouse)s"
		)
		params["warehouse"] = filters.warehouse

	if filters.get("season"):
		conditions.append(
			"(IFNULL(pii.lot_number, '') LIKE %(season)s OR IFNULL(pii.from_lot_number, '') LIKE %(season)s)"
		)
		params["season"] = f"%{filters.season.strip()}%"

	return " AND ".join(conditions), params


def get_data(filters):
	conditions, params = get_conditions(filters)

	data = frappe.db.sql(
		f"""
		WITH audit_base AS (
			SELECT
				bad.bale_barcode,
				MAX(IFNULL(bad.advance_weight, 0)) AS advance_weight,
				MAX(IFNULL(bad.weight, 0)) AS re_weight
			FROM `tabBale Audit Detail` bad
			INNER JOIN `tabBale Audit` ba
				ON ba.name = bad.parent
				AND ba.docstatus = 1
			GROUP BY bad.bale_barcode
		),
		base_data AS (
			SELECT
				COALESCE(NULLIF(pii.warehouse, ''), NULLIF(pi.set_warehouse, ''), 'Not Set') AS warehouse,
				CASE
					WHEN IFNULL(pii.lot_number, '') != '' THEN 1
					ELSE 0
				END AS purchase_grower,
				CASE
					WHEN IFNULL(pii.lot_number, '') = '' THEN 1
					ELSE 0
				END AS purchase_trader,
				IFNULL(pii.qty, 0) AS purchase_weight,
				IFNULL(ab.advance_weight, 0) AS advance_weight,
				IFNULL(ab.re_weight, 0) AS re_weight
			FROM `tabPurchase Invoice Item` pii
			INNER JOIN `tabPurchase Invoice` pi
				ON pi.name = pii.parent
			LEFT JOIN audit_base ab
				ON ab.bale_barcode = pii.batch_no
			WHERE {conditions}
		)
		SELECT
			warehouse,
			SUM(purchase_grower) AS purchase_grower,
			SUM(purchase_trader) AS purchase_trader,
			SUM(purchase_grower + purchase_trader) AS total_bales_purchased,
			ROUND(SUM(purchase_weight), 2) AS total_purchase_weight,
			ROUND(SUM(advance_weight), 2) AS advance_weight,
			ROUND(SUM(re_weight), 2) AS re_weight
		FROM base_data
		GROUP BY warehouse
		ORDER BY warehouse
		""",
		params,
		as_dict=True,
	)

	rows = []

	for row in data:
		rows.append(build_computed_row(row))

	return rows


def build_computed_row(row):
	advance_weight = flt(row.get("advance_weight"))
	re_weight = flt(row.get("re_weight"))
	total_bales = flt(row.get("total_bales_purchased"))
	difference = re_weight - advance_weight
	variance_ratio = (difference / advance_weight) if advance_weight else 0

	total_purchase_weight = flt(row.get("total_purchase_weight"))

	return {
		"warehouse": row.get("warehouse"),
		"purchase_grower": row.get("purchase_grower", 0),
		"purchase_trader": row.get("purchase_trader", 0),
		"total_bales_purchased": row.get("total_bales_purchased", 0),
		"total_purchase_weight": round(total_purchase_weight, 2),
		"advance_weight": round(advance_weight, 2),
		"re_weight": round(re_weight, 2),
		"difference_kgs": round(difference, 2),
		"variance_percent": round(variance_ratio * 100, 2),
		"variance_in_kgs": round(variance_ratio * total_bales, 2),
		"forecasted_wastage": round(variance_ratio * total_purchase_weight, 2),
	}
