# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_filters(filters):
    if not filters:
        filters = frappe._dict()

    conditions = ""
    params = {}

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
        {"label": "Depot", "fieldname": "purchase_center", "fieldtype": "Link", "options": "Warehouse", "width": 200},
        {"label": "GTN Bales", "fieldname": "gtn_bales", "fieldtype": "Int", "width": 110},
        {"label": "GTN KGs", "fieldname": "gtn_kgs", "fieldtype": "Float", "width": 120},
        {"label": "Voucher Bales", "fieldname": "voucher_bales", "fieldtype": "Int", "width": 130},
        {"label": "Voucher KGs", "fieldname": "voucher_kgs", "fieldtype": "Float", "width": 120},
        {"label": "Bale Diff", "fieldname": "bale_diff", "fieldtype": "Int", "width": 110},
        {"label": "KG Diff", "fieldname": "kg_diff", "fieldtype": "Float", "width": 120},
    ]


def get_data(filters):
    conditions, params = get_filters(filters)

    show_rejected = (filters or {}).get("show_rejected")
    voucher_filter = "1=1" if show_rejected else "IFNULL(ig.rejected_grade, 0) = 0"

    rows = frappe.db.sql(f"""
        SELECT
            supp.custom_location_warehouse AS purchase_center,
            COUNT(CASE WHEN {voucher_filter} THEN pii.batch_no END)                      AS voucher_bales,
            SUM(CASE WHEN {voucher_filter} THEN pii.qty ELSE 0 END)                      AS voucher_kgs,
            COUNT(CASE WHEN gtn.name IS NOT NULL
                            AND IFNULL(ig.rejected_grade, 0) = 0 THEN pii.batch_no END)  AS gtn_bales,
            SUM(CASE WHEN gtn.name IS NOT NULL
                          AND IFNULL(ig.rejected_grade, 0) = 0
                          THEN IFNULL(gtn_items.weight, 0) ELSE 0 END)                   AS gtn_kgs
        FROM `tabPurchase Invoice` pi
        INNER JOIN `tabPurchase Invoice Item` pii
            ON pii.parent = pi.name
        LEFT JOIN `tabSupplier` supp
            ON supp.name = pi.supplier
        LEFT JOIN `tabItem Grade` ig
            ON ig.name = pii.grade
        LEFT JOIN (
            SELECT gi.bale_barcode, gi.weight, gi.parent
            FROM `tabGoods Transfer Note Items` gi
            INNER JOIN `tabGoods Transfer Note` g ON g.name = gi.parent AND g.docstatus = 1
            WHERE gi.parenttype = 'Goods Transfer Note'
        ) gtn_items ON gtn_items.bale_barcode = pii.batch_no
        LEFT JOIN `tabGoods Transfer Note` gtn
            ON gtn.name = gtn_items.parent
        WHERE pi.docstatus = 1
          AND pii.batch_no IS NOT NULL
          AND pii.batch_no != ''
          {conditions}
        GROUP BY supp.custom_location_warehouse
        ORDER BY supp.custom_location_warehouse
    """, params, as_dict=True)

    data = []
    for r in rows:
        if not r.purchase_center:
            continue
        voucher_bales = r.voucher_bales or 0
        voucher_kgs = r.voucher_kgs or 0
        gtn_bales = r.gtn_bales or 0
        gtn_kgs = r.gtn_kgs or 0
        data.append({
            "purchase_center": r.purchase_center,
            "gtn_bales": gtn_bales,
            "gtn_kgs": round(gtn_kgs, 3),
            "voucher_bales": voucher_bales,
            "voucher_kgs": round(voucher_kgs, 3),
            "bale_diff": voucher_bales - gtn_bales,
            "kg_diff": round(voucher_kgs - gtn_kgs, 3),
        })

    if data:
        data.append({
            "purchase_center": "Total",
            "gtn_bales": sum(r["gtn_bales"] for r in data),
            "gtn_kgs": round(sum(r["gtn_kgs"] for r in data), 3),
            "voucher_bales": sum(r["voucher_bales"] for r in data),
            "voucher_kgs": round(sum(r["voucher_kgs"] for r in data), 3),
            "bale_diff": sum(r["bale_diff"] for r in data),
            "kg_diff": round(sum(r["kg_diff"] for r in data), 3),
        })

    return data
