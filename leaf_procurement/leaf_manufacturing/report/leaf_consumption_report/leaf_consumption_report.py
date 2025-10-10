# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore


def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    # Define columns
    columns = [
        {"label": "Process Order", "fieldname": "process_order", "fieldtype": "Link", "options": "Process Order", "width": 220},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 120},
        {"label": "Location", "fieldname": "location", "fieldtype": "Data", "width": 200},
        {"label": "Bale Barcode", "fieldname": "bale_barcode", "fieldtype": "Data", "width": 150},
        {"label": "Purchase Weight", "fieldname": "purchase_weight", "fieldtype": "Float", "width": 120},
        {"label": "Internal Grade", "fieldname": "internal_grade", "fieldtype": "Data", "width": 150},
        {"label": "Re-Weight", "fieldname": "reweight", "fieldtype": "Float", "width": 120},
        {"label": "Difference", "fieldname": "difference", "fieldtype": "Float", "width": 120},
    ]

    # Build dynamic filters for SQL
    conditions = []
    params = {}

    if filters.get("process_order"):
        conditions.append("lc.process_order = %(process_order)s")
        params["process_order"] = filters.get("process_order")

    if filters.get("location"):
        conditions.append("lc.location = %(location)s")
        params["location"] = filters.get("location")
         
    if filters.get("from_date"):
        conditions.append("lc.date >= %(from_date)s")
        params["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("lc.date <= %(to_date)s")
        params["to_date"] = filters.get("to_date")

    condition_str = " AND " + " AND ".join(conditions) if conditions else ""

    # SQL Query
    data = frappe.db.sql(f"""
        SELECT
            lc.process_order AS process_order,
            lc.date AS date,
            lc.location AS location,
            lcd.bale_barcode AS bale_barcode,
            lcd.purchase_weight AS purchase_weight,
            lcd.internal_grade AS internal_grade,
            lcd.reweight AS reweight,
            (lcd.reweight - lcd.purchase_weight) AS difference
        FROM
            `tabLeaf Consumption` lc
        LEFT JOIN
            `tabLeaf Consumption Detail` lcd
        ON
            lcd.parent = lc.name
        WHERE
            lc.docstatus = 1
            {condition_str}
        ORDER BY
            lc.date DESC
    """, params, as_dict=True)

    return columns, data
