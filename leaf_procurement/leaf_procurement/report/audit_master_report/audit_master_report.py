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

    if filters.get("warehouse"):
        conditions += " AND gtn.receiving_location = %(warehouse)s"
        params["warehouse"] = filters["warehouse"]

    if filters.get("gtn"):
        conditions += " AND gtn.name = %(gtn)s"
        params["gtn"] = filters["gtn"]

    gtn_status = filters.get("gtn_status", "All")
    if gtn_status == "With GTN":
        conditions += " AND gtn_items.bale_barcode IS NOT NULL"
    elif gtn_status == "Without GTN":
        conditions += " AND gtn_items.bale_barcode IS NULL"

    return conditions, params


def get_columns():
    return [
        {"label": "Bale ID", "fieldname": "bale_barcode", "fieldtype": "Data", "width": 130},
        {"label": "Purchase Center", "fieldname": "purchase_center", "fieldtype": "Link", "options": "Warehouse", "width": 160},
        {"label": "Purchase Date", "fieldname": "purchase_date", "fieldtype": "Date", "width": 120},
        {"label": "Purchase Weight", "fieldname": "purchase_weight", "fieldtype": "Float", "width": 130},
        {"label": "Purchase Rate", "fieldname": "purchase_rate", "fieldtype": "Currency", "width": 130},
        {"label": "GTN Number", "fieldname": "gtn_number", "fieldtype": "Link", "options": "Goods Transfer Note", "width": 180},
        {"label": "GTN Date", "fieldname": "gtn_date", "fieldtype": "Date", "width": 110},
        {"label": "TSA Number", "fieldname": "tsa_number", "fieldtype": "Data", "width": 130},
        {"label": "Truck Number", "fieldname": "truck_number", "fieldtype": "Data", "width": 130},
        {"label": "Receiving Warehouse", "fieldname": "receiving_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 160},
        {"label": "GTN Reweight", "fieldname": "gtn_reweight", "fieldtype": "Float", "width": 120},
    ]


def get_data(filters):
    conditions, params = get_filters(filters)

    data = frappe.db.sql(f"""
        SELECT
            pii.batch_no                 AS bale_barcode,
            supp.custom_location_warehouse AS purchase_center,
            pi.posting_date              AS purchase_date,
            pii.qty                      AS purchase_weight,
            pii.rate                     AS purchase_rate,
            gtn.name                     AS gtn_number,
            gtn.date                     AS gtn_date,
            gtn.receiving_location       AS receiving_warehouse,
            gtn_items.weight             AS gtn_reweight,
            gtn.tsa_number               AS tsa_number,
            gtn.vehicle_number           AS truck_number
        FROM `tabPurchase Invoice` pi
        INNER JOIN `tabPurchase Invoice Item` pii
            ON pii.parent = pi.name
        LEFT JOIN `tabSupplier` supp
            ON supp.name = pi.supplier
        LEFT JOIN (
            SELECT gi.bale_barcode, gi.weight, gi.parent
            FROM `tabGoods Transfer Note Items` gi
            INNER JOIN `tabGoods Transfer Note` g ON g.name = gi.parent AND g.docstatus = 1
            WHERE gi.parenttype = 'Goods Transfer Note'
        ) gtn_items ON gtn_items.bale_barcode = pii.batch_no
        LEFT JOIN `tabGoods Transfer Note` gtn
            ON gtn.name = gtn_items.parent
        LEFT JOIN `tabItem Grade` ig
            ON ig.name = pii.grade
        WHERE pi.docstatus = 1
          AND pii.batch_no IS NOT NULL
          AND pii.batch_no != ''
          AND IFNULL(ig.rejected_grade, 0) = 0
          {conditions}
        ORDER BY pi.posting_date DESC, pi.name, pii.batch_no
    """, params, as_dict=True)

    return data
