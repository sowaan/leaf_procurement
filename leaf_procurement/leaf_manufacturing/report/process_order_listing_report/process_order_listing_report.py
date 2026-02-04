# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe  # type: ignore


def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    # -----------------------------
    # Columns
    # -----------------------------
    columns = [
        {
            "label": "PO Order No",
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Process Order",
            "width": 150,
        },
        {
            "label": "Location",
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 150,
        },
        {"label": "Input Nos", "fieldname": "input_nos", "fieldtype": "Int", "width": 100},
        {"label": "Input KGs", "fieldname": "input_kgs", "fieldtype": "Float", "width": 120},
        {"label": "Output Nos", "fieldname": "output_nos", "fieldtype": "Int", "width": 110},
        {"label": "Output KGs", "fieldname": "output_kgs", "fieldtype": "Float", "width": 120},
        {"label": "Wastage KGs", "fieldname": "wastage_kgs", "fieldtype": "Float", "width": 120},
        {"label": "Wastage %", "fieldname": "wastage_percent", "fieldtype": "Percent", "width": 100},
    ]

    # -----------------------------
    # Build conditions
    # -----------------------------
    conditions = []	
    params = {}

    if filters.get("location"):
        conditions.append("po.location = %(location)s")
        params["location"] = filters.get("location")

    if filters.get("from_date"):
        conditions.append("po.date >= %(from_date)s")
        params["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("po.date <= %(to_date)s")
        params["to_date"] = filters.get("to_date")

    condition_str = " AND " + " AND ".join(conditions) if conditions else ""

    # -----------------------------
    # SQL Query
    # -----------------------------
    data = frappe.db.sql(
        f"""
        SELECT
			po.name,
			po.location AS warehouse,

			IFNULL(inp.input_nos, 0)  AS input_nos,
			IFNULL(inp.input_kgs, 0)  AS input_kgs,

			IFNULL(outp.output_nos, 0) AS output_nos,
			IFNULL(outp.output_kgs, 0) AS output_kgs

		FROM `tabProcess Order` po

		/* -------- INPUT (Leaf Consumption) -------- */
		JOIN (
			SELECT
				lc.process_order,
				COUNT(lcd.name) AS input_nos,
				SUM(lcd.purchase_weight) AS input_kgs
			FROM `tabLeaf Consumption` lc
			JOIN `tabLeaf Consumption Detail` lcd
				ON lcd.parent = lc.name
				AND lcd.parenttype = 'Leaf Consumption'
			WHERE lc.docstatus = 1
			AND lcd.docstatus = 1
			GROUP BY lc.process_order
		) inp ON inp.process_order = po.name

		/* -------- OUTPUT (Prized Item Creation) -------- */
		JOIN (
			SELECT
				pic.process_order,
				COUNT(pce.name) AS output_nos,
				SUM(pce.kgs) AS output_kgs
			FROM `tabPrized Item Creation` pic
			JOIN `tabPrized Item Creation Entry` pce
				ON pce.parent = pic.name
				AND pce.parenttype = 'Prized Item Creation'
			WHERE pic.docstatus = 1
			AND pce.docstatus = 1
			GROUP BY pic.process_order
		) outp ON outp.process_order = po.name

		WHERE po.docstatus = 1
         {condition_str}
		ORDER BY po.name;

        """,
        params,
        as_dict=True,
    )

    # -----------------------------
    # Final calculations
    # -----------------------------
    for row in data:
        input_kgs = row.input_kgs or 0
        output_kgs = row.output_kgs or 0

        row["wastage_kgs"] = input_kgs - output_kgs
        row["wastage_percent"] = (
            (row["wastage_kgs"] / input_kgs) * 100 if input_kgs else 0
        )

    return columns, data
