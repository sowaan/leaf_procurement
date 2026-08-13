# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 220},
        {"label": "Total Bales", "fieldname": "total_bales", "fieldtype": "Int", "width": 120},
        {"label": "Total Advance Weight", "fieldname": "total_advance_weight", "fieldtype": "Float", "width": 160},
        {"label": "Total Re Weight", "fieldname": "total_re_weight", "fieldtype": "Float", "width": 140},
        {"label": "Total Weight Difference", "fieldname": "total_weight_difference", "fieldtype": "Float", "width": 170},
    ]


def get_data(filters):
    return frappe.db.sql(
        """
        SELECT ba.location_warehouse AS warehouse,
               COUNT(DISTINCT bad.bale_barcode) AS total_bales,
               ROUND(SUM(bad.advance_weight), 2) AS total_advance_weight,
               ROUND(SUM(bad.weight), 2) AS total_re_weight,
               ROUND(SUM(bad.weight - bad.advance_weight), 2) AS total_weight_difference
          FROM `tabBale Audit Detail` AS bad
          LEFT JOIN `tabBale Audit` AS ba
            ON bad.parent = ba.name
         WHERE ba.docstatus = 1
           AND (bad.weight - bad.advance_weight) >= 1
           AND ba.date BETWEEN %(from_date)s AND %(to_date)s
         GROUP BY ba.location_warehouse
         ORDER BY ba.location_warehouse
        """,
        filters,
        as_dict=True,
    )
