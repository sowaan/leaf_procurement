# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_filters(filters):
    """Builds SQL conditions and parameters safely."""
    conditions = []
    params = {}
    if not filters:
        filters = frappe._dict()

    if filters.get("date"):
        conditions.append("gtn_base.date = %(date)s")
        params["date"] = filters.date

    if filters.get("depot"):
        conditions.append("gtn_base.location_warehouse = %(depot)s")
        params["depot"] = filters.depot

    # Return the condition string and the parameters for the query
    return (" AND " + " AND ".join(conditions)) if conditions else "", params


def get_columns():
    return [
        {"label": "GTN Code", "fieldname": "gtn_code", "fieldtype": "Link", "options": "Goods Transfer Note", "width": 150},
        {"label": "Depot Name", "fieldname": "depot_name", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"label": "Total No. of Bales", "fieldname": "t_no_of_bale", "fieldtype": "Int", "width": 130},
        {"label": "GTN Advance Weight", "fieldname": "gtn_adv_wt", "fieldtype": "Float", "width": 130},
        {"label": "Audit No. of Bales", "fieldname": "no_of_bale", "fieldtype": "Int", "width": 130},
        {"label": "Advance weight", "fieldname": "advance_wt", "fieldtype": "Float", "width": 130},
        {"label": "Re-weighment", "fieldname": "re_weighment", "fieldtype": "Float", "width": 130},
        {"label": "Difference", "fieldname": "diff", "fieldtype": "Float", "width": 130}
    ]

def get_data(filters):
    sql_conditions, params = get_filters(filters)

# SELECT
#     gtn.name AS gtn_code,
#     gtn.location_warehouse AS depot_name,
#     COUNT(gtni.bale_barcode) AS t_no_of_bale,
#     IFNULL(SUM(gtni.weight), 0) AS gtn_adv_wt,
#     COUNT(DISTINCT bad.bale_barcode) AS no_of_bale,
#     IFNULL(SUM(bad.advance_weight), 0) AS advance_weight,
#     IFNULL(SUM(bad.weight), 0) AS re_weighment,
#     IFNULL(SUM(bad.weight), 0) - IFNULL(SUM(bad.advance_weight), 0) AS diff
# FROM `tabGoods Transfer Note` AS gtn
# LEFT JOIN `tabGoods Transfer Note Items` AS gtni ON gtn.name = gtni.parent
# LEFT JOIN `tabBale Audit Detail` AS bad ON bad.bale_barcode = gtni.bale_barcode
# WHERE 
#     gtn.docstatus = 1
#    # AND gtn.date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
# GROUP BY gtn.name, gtn.location_warehouse
# ORDER BY gtn.name

    # This optimized query uses subqueries to pre-aggregate data
    # and a HAVING clause to filter at the database level.
    data = frappe.db.sql(f"""
        SELECT
            gtn.gtn_code,
            gtn.depot_name,
            gtn.t_no_of_bale,
            gtn.gtn_adv_wt,
            IFNULL(audited.no_of_bale, 0) AS no_of_bale,
            IFNULL(audited.advance_wt, 0) AS advance_wt,
            IFNULL(audited.re_weighment, 0) AS re_weighment,
            IFNULL(audited.re_weighment - audited.advance_wt, 0) AS diff
        FROM (
            -- Subquery 1: Get totals for ALL bales in each GTN
            SELECT
                gtn_base.name AS gtn_code,
                gtn_base.location_warehouse AS depot_name,
                COUNT(gtni.name) AS t_no_of_bale,
                SUM(gtni.weight) AS gtn_adv_wt
            FROM `tabGoods Transfer Note` AS gtn_base
            LEFT JOIN `tabGoods Transfer Note Items` AS gtni ON gtn_base.name = gtni.parent
            WHERE gtn_base.docstatus = 1 {sql_conditions}
            GROUP BY gtn_base.name
        ) AS gtn
        -- Use an INNER JOIN because we only want GTNs with audited bales
        INNER JOIN (
            -- Subquery 2: Get totals for ONLY the audited bales
            SELECT
                gtni.parent AS gtn_code,
                COUNT(bad.name) AS no_of_bale,
                SUM(gtni.weight) AS advance_wt,
                SUM(bad.weight) AS re_weighment
            FROM `tabBale Audit Detail` AS bad
            INNER JOIN `tabGoods Transfer Note Items` AS gtni ON bad.bale_barcode = gtni.bale_barcode
            GROUP BY gtni.parent
            -- OPTIMIZED: Filter groups here instead of in Python
            HAVING SUM(bad.weight) > 0
        ) AS audited ON gtn.gtn_code = audited.gtn_code
        ORDER BY gtn.gtn_code
    """, params, as_dict=True)

    return data