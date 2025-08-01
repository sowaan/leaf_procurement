# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    # The get_data function now returns the final, calculated data directly
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Data", "width": 150},
        {"label": "Number of Bales", "fieldname": "number_of_bales", "fieldtype": "Int", "width": 130},
        {"label": "Item Grade", "fieldname": "item_grade", "fieldtype": "Data", "width": 100},
        {"label": "Item Sub Grade", "fieldname": "item_sub_grade", "fieldtype": "Data", "width": 120},
        {"label": "Advance Weight (Kgs)", "fieldname": "advance_weight", "fieldtype": "Float", "width": 150},
        {"label": "Re-Weight (Kgs)", "fieldname": "re_weight", "fieldtype": "Float", "width": 140},
        {"label": "Difference (Kgs)", "fieldname": "difference", "fieldtype": "Float", "width": 130},
        {"label": "Variance (%)", "fieldname": "variance_percent", "fieldtype": "Percent", "width": 120},
    ]


def get_data(filters):
    # This block safely builds the conditions and parameters for the query
    conditions = []
    params = filters.copy()

    if filters.get("date"):
        conditions.append("grn.date = %(date)s")
    if filters.get("warehouse"):
        conditions.append("grn.location_warehouse = %(warehouse)s")
    if filters.get("grade"):
        conditions.append("gtni.item_grade = %(grade)s")
    if filters.get("sub_grade"):
        conditions.append("gtni.item_sub_grade = %(sub_grade)s")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # This single query performs all filtering, aggregation, and calculation
    query = f"""
        SELECT
            grn.location_warehouse AS warehouse,
            COUNT(gtni.name) AS number_of_bales,
            gtni.item_grade,
            gtni.item_sub_grade,
            SUM(gtni.weight) AS advance_weight,
            SUM(IFNULL(bad.weight, 0)) AS re_weight,
            -- Calculation moved directly into SQL
            (SUM(IFNULL(bad.weight, 0)) - SUM(gtni.weight)) AS difference,
            -- Variance calculation moved into SQL with protection against division by zero
            CASE
                WHEN SUM(gtni.weight) > 0
                THEN ((SUM(IFNULL(bad.weight, 0)) - SUM(gtni.weight)) / SUM(gtni.weight)) * 100
                ELSE 0
            END AS variance_percent
        FROM `tabGoods Receiving Note` AS grn
        -- This join logic is preserved from your original query
        INNER JOIN `tabGoods Transfer Note Items` AS gtni ON grn.name = gtni.parent
        LEFT JOIN `tabBale Audit Detail` AS bad ON gtni.bale_barcode = bad.bale_barcode
        {where_clause}
        GROUP BY
            grn.location_warehouse,
            gtni.item_grade,
            gtni.item_sub_grade
        ORDER BY
            grn.location_warehouse,
            gtni.item_grade
    """

    return frappe.db.sql(query, params, as_dict=True)
