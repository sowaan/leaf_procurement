# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe  # type: ignore
from frappe.utils import flt, today  # type: ignore


def execute(filters=None):
	filters = frappe._dict(filters or {})

	if filters.get("for_today"):
		filters["from_date"] = today()
		filters["to_date"] = today()

	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw("From Date and To Date are mandatory.")

	data = get_raw_data(filters)
	columns, rows = build_report(data)
	return columns, rows


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


def get_raw_data(filters):
	conditions, params = get_conditions(filters)

	return frappe.db.sql(
		f"""
		SELECT
			lc.location AS location,
			po.shift AS shift,
			DATE_FORMAT(lc.date, '%%b - %%Y') AS month_label,
			lc.date AS date,
			COUNT(DISTINCT lcd.bale_barcode) AS bales_issued,
			SUM(IFNULL(lcd.purchase_weight, 0)) AS advance_weight,
			SUM(IFNULL(lcd.reweight, 0)) AS reweight
		FROM `tabLeaf Consumption` lc
		INNER JOIN `tabProcess Order` po
			ON po.name = lc.process_order
		INNER JOIN `tabLeaf Consumption Detail` lcd
			ON lcd.parent = lc.name
		WHERE {conditions}
		GROUP BY lc.location, po.shift, DATE_FORMAT(lc.date, '%%Y-%%m')
		ORDER BY lc.location, DATE_FORMAT(lc.date, '%%Y-%%m'), po.shift
		""",
		params,
		as_dict=True,
	)


METRIC_LABELS = [
	("bales_issued", "Bales Issued", "No.", "Int"),
	("advance_weight", "Advance Weight at the Time of Buying", "KGs", "Float"),
	("reweight", "Re-Weighment at the Time of Issuance", "KGs", "Float"),
	("weight_loss", "Total Weight Loss", "KGs", "Float"),
	("per_bale_loss", "Per Bale Weight Loss", "KGs", "Float"),
	("weight_loss_pct", "Weight Loss in %", "%", "Percent"),
]


def build_report(raw_data):
	if not raw_data:
		columns = [
			{"label": "Description", "fieldname": "description", "fieldtype": "Data", "width": 280},
			{"label": "UOM", "fieldname": "uom", "fieldtype": "Data", "width": 60},
		]
		return columns, []

	# Collect ordered unique (location, month_label, shift) column keys
	seen = []
	seen_set = set()
	for row in raw_data:
		key = (row.location, row.month_label, row.shift)
		if key not in seen_set:
			seen.append(key)
			seen_set.add(key)

	# Build data index: key -> aggregated values
	data_index = {}
	for row in raw_data:
		key = (row.location, row.month_label, row.shift)
		data_index[key] = row

	# Build columns
	columns = [
		{"label": "Description", "fieldname": "description", "fieldtype": "Data", "width": 280},
		{"label": "UOM", "fieldname": "uom", "fieldtype": "Data", "width": 60},
	]

	for loc, month, shift in seen:
		safe_key = f"{loc}_{month}_{shift}".replace(" ", "_").replace("-", "_").replace(".", "")
		columns.append({
			"label": f"{loc} | {month} | Shift {shift}",
			"fieldname": safe_key,
			"fieldtype": "Float",
			"width": 180,
			"precision": 3,
		})

	# Build per-column computed values
	col_values = {}
	for key in seen:
		row = data_index.get(key, {})
		bales = flt(row.get("bales_issued"))
		adv = flt(row.get("advance_weight"))
		rew = flt(row.get("reweight"))
		loss = rew - adv
		per_bale = (loss / bales) if bales else 0
		loss_pct = (loss / adv * 100) if adv else 0
		col_values[key] = {
			"bales_issued": bales,
			"advance_weight": adv,
			"reweight": rew,
			"weight_loss": loss,
			"per_bale_loss": per_bale,
			"weight_loss_pct": loss_pct,
		}

	# Build metric rows
	rows = []
	for metric_key, label, uom, _ in METRIC_LABELS:
		data_row = {"description": label, "uom": uom}
		for loc, month, shift in seen:
			safe_key = f"{loc}_{month}_{shift}".replace(" ", "_").replace("-", "_").replace(".", "")
			data_row[safe_key] = col_values.get((loc, month, shift), {}).get(metric_key, 0)
		rows.append(data_row)

	return columns, rows
