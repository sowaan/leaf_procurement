# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe  # type: ignore
from frappe.utils import flt, today  # type: ignore


def execute(filters=None):
	filters = frappe._dict(filters or {})

	if filters.get("for_today"):
		filters["from_date"] = today()
		filters["to_date"] = today()

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "GLT", "fieldname": "location", "fieldtype": "Link", "options": "Warehouse", "width": 200},
		{"label": "Month", "fieldname": "month_label", "fieldtype": "Data", "width": 110},
		{"label": "Shift", "fieldname": "shift", "fieldtype": "Data", "width": 60},
		{"label": "Bales Issued", "fieldname": "bales_issued", "fieldtype": "Int", "width": 110},
		{"label": "Advance Weight (KG)", "fieldname": "advance_weight", "fieldtype": "Float", "width": 155, "precision": 3},
		{"label": "Re-Weight (KG)", "fieldname": "reweight", "fieldtype": "Float", "width": 130, "precision": 3},
		{"label": "Weight Loss (KG)", "fieldname": "weight_loss", "fieldtype": "Float", "width": 130, "precision": 3},
		{"label": "Per Bale Loss (KG)", "fieldname": "per_bale_loss", "fieldtype": "Float", "width": 140, "precision": 3},
		{"label": "Loss %", "fieldname": "loss_pct", "fieldtype": "Percent", "width": 90, "precision": 2},
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

	if filters.get("location"):
		conditions.append("lc.location = %(location)s")
		params["location"] = filters.location

	if filters.get("shift"):
		conditions.append("po.shift = %(shift)s")
		params["shift"] = filters.shift

	if filters.get("season"):
		conditions.append("YEAR(lc.date) = %(season)s")
		params["season"] = filters.season

	return " AND ".join(conditions), params


def get_data(filters):
	conditions, params = get_conditions(filters)

	rows = frappe.db.sql(
		f"""
		SELECT
			lc.location AS location,
			DATE_FORMAT(lc.date, '%%b - %%Y') AS month_label,
			DATE_FORMAT(lc.date, '%%Y-%%m') AS month_sort,
			po.shift AS shift,
			COUNT(DISTINCT lcd.bale_barcode) AS bales_issued,
			SUM(IFNULL(lcd.purchase_weight, 0)) AS advance_weight,
			SUM(IFNULL(lcd.reweight, 0)) AS reweight
		FROM `tabLeaf Consumption` lc
		INNER JOIN `tabProcess Order` po
			ON po.name = lc.process_order
		INNER JOIN `tabLeaf Consumption Detail` lcd
			ON lcd.parent = lc.name
		WHERE {conditions}
		GROUP BY lc.location, DATE_FORMAT(lc.date, '%%Y-%%m'), po.shift
		ORDER BY lc.location, month_sort, po.shift
		""",
		params,
		as_dict=True,
	)

	data = []
	totals = {
		"location": "Total",
		"month_label": "",
		"shift": "",
		"bales_issued": 0,
		"advance_weight": 0.0,
		"reweight": 0.0,
		"weight_loss": 0.0,
		"per_bale_loss": 0.0,
		"loss_pct": 0.0,
		"bold": 1,
	}

	for row in rows:
		bales = flt(row.bales_issued)
		adv = flt(row.advance_weight)
		rew = flt(row.reweight)
		loss = rew - adv
		per_bale = (loss / bales) if bales else 0
		loss_pct = (loss / adv * 100) if adv else 0

		data.append({
			"location": row.location,
			"month_label": row.month_label,
			"shift": row.shift,
			"bales_issued": int(bales),
			"advance_weight": round(adv, 3),
			"reweight": round(rew, 3),
			"weight_loss": round(loss, 3),
			"per_bale_loss": round(per_bale, 3),
			"loss_pct": round(loss_pct, 2),
		})

		totals["bales_issued"] += int(bales)
		totals["advance_weight"] += adv
		totals["reweight"] += rew

	if data:
		total_loss = totals["reweight"] - totals["advance_weight"]
		total_bales = totals["bales_issued"]
		total_adv = totals["advance_weight"]
		totals["weight_loss"] = round(total_loss, 3)
		totals["per_bale_loss"] = round((total_loss / total_bales) if total_bales else 0, 3)
		totals["loss_pct"] = round((total_loss / total_adv * 100) if total_adv else 0, 2)
		totals["advance_weight"] = round(totals["advance_weight"], 3)
		totals["reweight"] = round(totals["reweight"], 3)
		data.append(totals)

	return data
