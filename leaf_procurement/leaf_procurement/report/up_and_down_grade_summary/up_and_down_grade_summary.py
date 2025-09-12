# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	if not filters:
		filters = {}

	# --- Fetch Settings From Leaf Procurement Settings
	settings = frappe.get_single("Leaf Procurement Settings")
	rejected_item = settings.rejected_invoice_item or "RBC"

	# --- Fetch all dynamic Reclassification Grades ---
	reclass_grades = frappe.get_all("Reclassification Grade", pluck="name")

	# --- Build columns ---
	columns = [
		{"label": "Grade", "fieldname": "grade", "fieldtype": "Data", "width": 150}
	]
	for g in reclass_grades:
		columns.append({
			"label": g,
			"fieldname": frappe.scrub(g),
			"fieldtype": "Float",
			"width": 120
		})
	columns.append({
		"label": "Total",
		"fieldname": "total_qty",
		"fieldtype": "Float",
		"width": 120
	})

	# --- Fetch data from Purchase Invoice + Items ---
	conditions = ""
	values = {}

	conditions += " AND pii.item_code <> %(rejected_item)s"
	values["rejected_item"] = rejected_item

	if filters.get("from_date"):
		conditions += " AND pi.posting_date >= %(from_date)s"
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions += " AND pi.posting_date <= %(to_date)s"
		values["to_date"] = filters["to_date"]

	if filters.get("depot"):
		conditions += " AND pii.warehouse <= %(depot)s"
		values["depot"] = filters["depot"]		
	
	query = f"""
		SELECT 
			pii.grade as grade,
			pii.reclassification_grade as reclassification_grade,
			SUM(pii.qty) as weight
		FROM `tabPurchase Invoice Item` pii
		INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
		WHERE pi.docstatus = 1 {conditions}
		GROUP BY pii.grade, pii.reclassification_grade
	"""

	results = frappe.db.sql(query, values=values, as_dict=True)
	# --- Pivot data into rows ---
	data_map = {}
	for r in results:
		grade = r.grade or "Unknown"
		reclass = r.reclassification_grade or "Unknown"
		weight = r.weight or 0

		if grade not in data_map:
			data_map[grade] = { "grade": grade, "total_qty": 0 }
			for g in reclass_grades:
				data_map[grade][frappe.scrub(g)] = 0

		if reclass in reclass_grades:
			data_map[grade][frappe.scrub(reclass)] += weight
		else:
			# if reclass not in list, skip or put under Unknown
			pass

		data_map[grade]["total_qty"] += weight

	# --- Final data list ---
	data = list(data_map.values())

	return columns, data