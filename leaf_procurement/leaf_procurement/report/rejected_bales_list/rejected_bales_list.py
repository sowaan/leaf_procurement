# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_filters(filters):
    conditions = ""
    params = {}

    if not filters:
        filters = frappe._dict()

    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s"
        params["from_date"] = filters["from_date"]
        params["to_date"] = filters["to_date"]

    if filters.get("purchase_center"):
        conditions += " AND supp.custom_location_warehouse = %(purchase_center)s"
        params["purchase_center"] = filters["purchase_center"]

    return conditions, params


def get_columns():
    return [
        {"label": "Bale ID", "fieldname": "bale_id", "fieldtype": "Data", "width": 140},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 110},
        {"label": "Voucher No", "fieldname": "voucher_no", "fieldtype": "Link", "options": "Purchase Invoice", "width": 180},
        {"label": "Purchase Center", "fieldname": "purchase_center", "fieldtype": "Link", "options": "Warehouse", "width": 180},
        {"label": "Bales Count", "fieldname": "bales_count", "fieldtype": "Int", "width": 110},
    ]


def get_data(filters):
    conditions, params = get_filters(filters)

    data = frappe.db.sql(f"""
        SELECT
            pii.batch_no                        AS bale_id,
            pi.posting_date                     AS date,
            pi.name                             AS voucher_no,
            supp.custom_location_warehouse      AS purchase_center,
            1                                   AS bales_count
        FROM `tabPurchase Invoice` pi
        INNER JOIN `tabPurchase Invoice Item` pii
            ON pii.parent = pi.name
        LEFT JOIN `tabSupplier` supp
            ON supp.name = pi.supplier
        LEFT JOIN `tabItem Grade` ig
            ON ig.name = pii.grade
        WHERE pi.docstatus = 1
          AND pii.batch_no IS NOT NULL
          AND pii.batch_no != ''
          AND IFNULL(ig.rejected_grade, 0) = 1
          {conditions}
        ORDER BY pi.posting_date DESC, pi.name, pii.batch_no
    """, params, as_dict=True)

    return data
