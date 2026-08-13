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
        {"label": "Location Warehouse", "fieldname": "location_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 220},
        {"label": "Audited Bales", "fieldname": "audited_bales", "fieldtype": "Int", "width": 140},
    ]


def get_data(filters):
    return frappe.db.sql(
        """
        SELECT `tabBale Audit`.location_warehouse AS location_warehouse,
               COUNT(DISTINCT `tabBale Audit Detail`.bale_barcode) AS audited_bales
          FROM `tabBale Audit` AS `tabBale Audit`
         INNER JOIN `tabBale Audit Detail` AS `tabBale Audit Detail`
            ON `tabBale Audit`.name = `tabBale Audit Detail`.parent
         WHERE `tabBale Audit`.docstatus = 1
           AND `tabBale Audit`.date BETWEEN %(from_date)s AND %(to_date)s
         GROUP BY `tabBale Audit`.location_warehouse
        """,
        filters,
        as_dict=True,
    )
