# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

# def get_final_conditions(filters):
#     final_conditions = []
#     params = {}
#     if filters.get("depot"):
#         final_conditions.append("audited.location_warehouse = %(depot)s")
#         params["depot"] = filters.depot

#     if filters.get("gtn"):
#         final_conditions.append("gtn.gtn_number = %(gtn)s")
#         params["gtn"] = filters.gtn

#     return (" AND " + " AND ".join(final_conditions)) if final_conditions else "", params


def get_filters(filters):
    """Builds SQL conditions and parameters safely."""
    conditions = []

    params = {}
    if not filters:
        filters = frappe._dict()

    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("gtn.date BETWEEN %(from_date)s AND %(to_date)s")
        params["from_date"] = filters.from_date
        params["to_date"] = filters.to_date

    if filters.get("depot"):
        conditions.append("ba.location_warehouse = %(depot)s")
        params["depot"] = filters.depot

    if filters.get("gtn"):
        conditions.append("gtn.name = %(gtn)s")
        params["gtn"] = filters.gtn

    # Return the condition string and the parameters for the query
    return (" AND " + " AND ".join(conditions)) if conditions else "", params


def get_columns():
    return [
        {"label": "GTN Code", "fieldname": "gtn_code", "fieldtype": "Link", "options": "Goods Transfer Note", "width": 220},
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
    # final_conditions_str, final_params = get_final_conditions(filters)
    # params.update(final_params)

    # This optimized query uses subqueries to pre-aggregate data
    # and a HAVING clause to filter at the database level.
    data = frappe.db.sql(f"""
SELECT 
    gtn as gtn_code,
    max(l_warehouse) as depot_name,
    COUNT(DISTINCT bale_barcode) AS t_no_of_bale,
    SUM(advance_weight) AS gtn_adv_wt,
    COUNT(DISTINCT CASE WHEN re_weight IS NOT NULL THEN bale_barcode END) AS no_of_bale,
    SUM(CASE WHEN re_weight IS NOT NULL THEN advance_weight ELSE 0 END) AS advance_wt,
    SUM(CASE WHEN re_weight IS NOT NULL THEN re_weight ELSE 0 END) AS re_weighment,
    SUM(CASE WHEN re_weight IS NOT NULL THEN re_weight - advance_weight ELSE 0 END) AS diff
FROM (
    -- 👇 base detail query without GROUP BY
SELECT 
    gtn_items.bale_barcode AS bale_barcode,
    gtn.location_warehouse AS location_warehouse,
    ba.location_warehouse AS l_warehouse,
    gtn.date AS date,
    gtn.tsa_number AS tsa,
    gtn.name AS gtn,
    gtn.vehicle_number AS truck_number,
    gtn_items.weight AS advance_weight,
    bad.weight AS re_weight,
    (bad.weight - gtn_items.weight) AS weight_difference,
    bad.remarks AS remarks
FROM `tabGoods Transfer Note` gtn
INNER JOIN `tabGoods Transfer Note Items` gtn_items
    ON gtn_items.parent = gtn.name
LEFT JOIN `tabBale Audit Detail` bad
    ON bad.bale_barcode = gtn_items.bale_barcode
LEFT JOIN `tabBale Audit` ba
    ON bad.parent = ba.name
   AND ba.docstatus = 1
WHERE gtn.docstatus = 1
  AND gtn.date BETWEEN '2025-07-01' AND '2025-07-31'
ORDER BY gtn.name, gtn_items.bale_barcode
) t
GROUP BY gtn
ORDER BY gtn;


    """, params, as_dict=True)    
    # data = frappe.db.sql(f"""
    #     SELECT
    #         gtn.gtn_number AS gtn_code,
    #         audited.location_warehouse AS depot_name,
    #         gtn.total_bales AS t_no_of_bale,
    #         gtn.total_advance_weight AS gtn_adv_wt,
    #         IFNULL(audited.no_of_bale, 0) AS no_of_bale,
    #         IFNULL(audited.advance_wt, 0) AS advance_wt,
    #         IFNULL(audited.re_weighment, 0) AS re_weighment,
    #         IFNULL(audited.re_weighment - audited.advance_wt, 0) AS diff
    #     FROM (
    #         -- Subquery 1: Get totals for ALL bales grouped by GTN
    #         SELECT
    #             ba.name as gtn_number,
    #             COUNT(bad.bale_barcode) AS total_bales,
    #             SUM(ROUND(bad.weight, 2)) AS total_advance_weight
    #         FROM `tabGoods Transfer Note Items` AS bad
    #         inner JOIN `tabGoods Transfer Note` AS ba ON bad.parent = ba.name
    #         WHERE ba.docstatus = 1 {sql_conditions}
    #         GROUP BY ba.name 
    #     ) AS gtn
    #     INNER JOIN (
    #         -- Subquery 2: Get totals for audited bales having re_weight > 0
    #         SELECT
    #             bad.gtn_number,
    #             ba.location_warehouse,
    #             COUNT(bad.name) AS no_of_bale,
    #             SUM(ROUND(bad.advance_weight, 2)) AS advance_wt,
    #             SUM(ROUND(bad.weight, 2)) AS re_weighment
    #         FROM `tabBale Audit Detail` AS bad
    #         LEFT JOIN `tabBale Audit` AS ba ON bad.parent = ba.name
    #         WHERE ba.docstatus = 1 {sql_conditions}
    #         GROUP BY bad.gtn_number
    #         HAVING SUM(bad.weight) > 0
    #     ) AS audited ON gtn.gtn_number = audited.gtn_number
    #     where 1=1 {final_conditions_str}

    #     ORDER BY gtn.gtn_number
    # """, params, as_dict=True)


    return data