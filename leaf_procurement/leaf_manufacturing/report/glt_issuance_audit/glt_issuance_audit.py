# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe  # type: ignore
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw("From Date and To Date are mandatory.")
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "S.No", "fieldname": "sno", "fieldtype": "Int", "width": 60},
		{"label": "Shift", "fieldname": "shift", "fieldtype": "Data", "width": 70},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
		{"label": "Bale ID", "fieldname": "bale_id", "fieldtype": "Data", "width": 160},
		{"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 120},
		{"label": "Purch Center", "fieldname": "purch_center", "fieldtype": "Data", "width": 120},
		{"label": "Buying Date", "fieldname": "buying_date", "fieldtype": "Date", "width": 120},
		{"label": "Weight (Kgs)", "fieldname": "weight", "fieldtype": "Float", "width": 110, "precision": 3},
		{"label": "Re-weight (Kgs)", "fieldname": "reweight", "fieldtype": "Float", "width": 120, "precision": 3},
		{"label": "Difference (Kgs)", "fieldname": "difference", "fieldtype": "Float", "width": 120, "precision": 3},
	]


def get_conditions(filters):
	conditions = ["lc.docstatus = 1"]
	params = {}

	if filters.get("from_date"):
		conditions.append("lc.date >= %(from_date)s")
		params["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("lc.date <= %(to_date)s")
		params["to_date"] = filters.to_date

	if filters.get("shift"):
		conditions.append("po.shift = %(shift)s")
		params["shift"] = filters.shift

	if filters.get("warehouse"):
		conditions.append("lc.location = %(warehouse)s")
		params["warehouse"] = filters.warehouse

	if filters.get("purchase_center"):
		conditions.append("pii.warehouse = %(purchase_center)s")
		params["purchase_center"] = filters.purchase_center

	if filters.get("audit_status") == "With Audit":
		conditions.append("ab.bale_barcode IS NOT NULL")
	elif filters.get("audit_status") == "Without Audit":
		conditions.append("ab.bale_barcode IS NULL")

	return " AND ".join(conditions), params


def get_data(filters):
	conditions, params = get_conditions(filters)

	rows = frappe.db.sql(
		f"""
		SELECT
			lc.location_short_code AS warehouse,
			po.shift AS shift,
			lc.date AS date,
			lcd.bale_barcode AS bale_id,
			IFNULL(pi.custom_short_code, '') AS purch_center,
			pi.posting_date AS buying_date,
			IFNULL(pii.qty, 0) AS weight,
			IFNULL(ab.reweight, 0) AS reweight
		FROM `tabLeaf Consumption` lc
		INNER JOIN `tabProcess Order` po
			ON po.name = lc.process_order
		INNER JOIN `tabLeaf Consumption Detail` lcd
			ON lcd.parent = lc.name
		LEFT JOIN `tabPurchase Invoice Item` pii
			ON pii.batch_no = lcd.bale_barcode
			AND pii.docstatus = 1
			AND IFNULL(pii.qty, 0) > 0
		LEFT JOIN `tabPurchase Invoice` pi
			ON pi.name = pii.parent
			AND pi.docstatus = 1
		LEFT JOIN (
			SELECT bad.bale_barcode, bad.weight AS reweight
			FROM `tabBale Audit Detail` bad
			INNER JOIN `tabBale Audit` ba
				ON ba.name = bad.parent
				AND ba.docstatus = 1
			WHERE ba.creation = (
				SELECT MAX(ba2.creation)
				FROM `tabBale Audit` ba2
				INNER JOIN `tabBale Audit Detail` bad2
					ON bad2.parent = ba2.name
				WHERE bad2.bale_barcode = bad.bale_barcode
					AND ba2.docstatus = 1
			)
		) ab ON ab.bale_barcode = lcd.bale_barcode
		WHERE {conditions}
		ORDER BY lc.date, po.shift, lcd.bale_barcode
		""",
		params,
		as_dict=True,
	)

	result = []
	for idx, row in enumerate(rows, start=1):
		weight = flt(row.get("weight"))
		reweight = flt(row.get("reweight"))
		result.append({
			"sno": idx,
			"shift": row.get("shift"),
			"date": row.get("date"),
			"bale_id": row.get("bale_id"),
			"warehouse": row.get("warehouse"),
			"purch_center": row.get("purch_center"),
			"buying_date": row.get("buying_date"),
			"weight": round(weight, 3),
			"reweight": round(reweight, 3),
			"difference": round(weight - reweight, 3),
		})

	return result
