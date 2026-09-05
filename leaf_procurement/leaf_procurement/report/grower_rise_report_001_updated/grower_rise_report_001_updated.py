# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    inc_rej_bales = filters.get("include_rejected_bales", False)
    depot = filters.get("warehouse")

    grade_filter = ""
    if not inc_rej_bales:
        grade_filter = " AND LOWER(pii.grade) != 'reject'"

    depot_filter = ""
    if depot:
        # Depot values in the data are inconsistently formatted (e.g. "CTS-1 - CTS"
        # vs "CTS 2 - CTS" - hyphen vs space), so match with hyphens and spaces
        # normalized to the same character rather than requiring an exact string.
        depot_filter = " AND REPLACE(supp.custom_location_warehouse, '-', ' ') LIKE REPLACE(CONCAT('%%', %(depot)s, '%%'), '-', ' ')"

    raw_data = frappe.db.sql(f"""
        WITH base_data AS (
            SELECT
                pi.posting_date,
                pii.qty,
                pii.rate,
                pii.name AS item_name,
                supp.custom_location_warehouse AS depot_name,
                supp.name AS grower_id,
                supp.supplier_name AS grower_name
            FROM `tabPurchase Invoice` pi
            JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
            LEFT JOIN `tabSupplier` supp ON pi.supplier = supp.name
            LEFT JOIN `tabWarehouse` wh ON wh.name = supp.custom_location_warehouse
            WHERE pi.docstatus = 1
                AND pii.item_group = 'Products'
                AND pi.posting_date >= %(from_date)s
                AND pi.posting_date < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
                AND wh.custom_is_depot = 1
                {grade_filter}
                {depot_filter}
        ),
        depot_agg AS (
            SELECT
                bd.depot_name,
                bd.grower_id,
                bd.grower_name,

                -- Today's Aggregates
                SUM(CASE WHEN bd.posting_date >= %(to_date)s AND bd.posting_date < DATE_ADD(%(to_date)s, INTERVAL 1 DAY) THEN bd.qty * bd.rate ELSE 0 END) AS amount_today,
                SUM(CASE WHEN bd.posting_date >= %(to_date)s AND bd.posting_date < DATE_ADD(%(to_date)s, INTERVAL 1 DAY) THEN bd.qty ELSE 0 END) AS kgs_today,
                COUNT(CASE WHEN bd.posting_date >= %(to_date)s AND bd.posting_date < DATE_ADD(%(to_date)s, INTERVAL 1 DAY) THEN bd.item_name ELSE NULL END) AS bales_today,

                -- To-Date Aggregates
                SUM(bd.qty * bd.rate) AS amount_todate,
                SUM(bd.qty) AS kgs_todate,
                COUNT(bd.item_name) AS bales_todate
            FROM base_data bd
            GROUP BY bd.depot_name, bd.grower_id, bd.grower_name
        )
        SELECT
            da.depot_name,
            da.grower_id,
            da.grower_name,

            -- Today Columns
            da.bales_today,
            da.kgs_today,
            da.amount_today,
            CASE WHEN da.kgs_today > 0 THEN da.amount_today / da.kgs_today ELSE NULL END AS avg_today,
            CASE
                WHEN SUM(da.amount_today) OVER () > 0 THEN
                    (da.amount_today * 100.0 / SUM(da.amount_today) OVER ())
                ELSE NULL
            END AS percentage_today,

            -- ToDate Columns
            da.bales_todate,
            da.kgs_todate,
            da.amount_todate,
            CASE WHEN da.kgs_todate > 0 THEN da.amount_todate / da.kgs_todate ELSE NULL END AS avg_todate,
            CASE
                WHEN SUM(da.amount_todate) OVER () > 0 THEN
                    (da.amount_todate * 100.0 / SUM(da.amount_todate) OVER ())
                ELSE NULL
            END AS percentage_todate

        FROM depot_agg da
        ORDER BY da.depot_name, da.grower_name
    """, {
        "from_date": from_date,
        "to_date": to_date,
        "depot": depot,
    }, as_dict=True)

    columns = [
        {"label": "Depot Name", "fieldname": "depot_name", "fieldtype": "Link", "options": "Warehouse", "width": 120},
        {"label": "Grower ID", "fieldname": "grower_id", "fieldtype": "Link", "options": "Supplier", "width": 120},
        {"label": "Grower Name", "fieldname": "grower_name", "fieldtype": "Data", "width": 140},

        # Today
        {"label": "Bales (Today)", "fieldname": "bales_today", "fieldtype": "Int", "width": 120},
        {"label": "Kgs (Today)", "fieldname": "kgs_today", "fieldtype": "Float", "width": 110},
        {"label": "Amount (Today)", "fieldname": "amount_today", "fieldtype": "Currency", "width": 120},
        {"label": "Avg (Today)", "fieldname": "avg_today", "fieldtype": "Currency", "width": 110},
        {"label": "% (Today)", "fieldname": "percentage_today", "fieldtype": "Percent", "width": 100},

        # ToDate
        {"label": "Bales (ToDate)", "fieldname": "bales_todate", "fieldtype": "Int", "width": 120},
        {"label": "Kgs (ToDate)", "fieldname": "kgs_todate", "fieldtype": "Float", "width": 110},
        {"label": "Amount (ToDate)", "fieldname": "amount_todate", "fieldtype": "Currency", "width": 120},
        {"label": "Avg (ToDate)", "fieldname": "avg_todate", "fieldtype": "Currency", "width": 110},
        {"label": "% (ToDate)", "fieldname": "percentage_todate", "fieldtype": "Percent", "width": 100},
    ]

    total_bales_today = total_kgs_today = total_amount_today = total_percentage_today = 0
    total_bales_todate = total_kgs_todate = total_amount_todate = total_percentage_todate = 0

    for row in raw_data:
        total_bales_today += row.bales_today or 0
        total_kgs_today += row.kgs_today or 0
        total_amount_today += row.amount_today or 0
        total_bales_todate += row.bales_todate or 0
        total_kgs_todate += row.kgs_todate or 0
        total_amount_todate += row.amount_todate or 0
        total_percentage_today += row.percentage_today or 0
        total_percentage_todate += row.percentage_todate or 0

    total_avg_today = (total_amount_today / total_kgs_today) if total_kgs_today else 0
    total_avg_todate = (total_amount_todate / total_kgs_todate) if total_kgs_todate else 0

    raw_data.append({
        "depot_name": "Total",
        "grower_name": "",
        "grower_id": "",
        "bales_today": total_bales_today,
        "kgs_today": total_kgs_today,
        "amount_today": total_amount_today,
        "avg_today": total_avg_today,
        "percentage_today": round(total_percentage_today),
        "bales_todate": total_bales_todate,
        "kgs_todate": total_kgs_todate,
        "amount_todate": total_amount_todate,
        "avg_todate": total_avg_todate,
        "percentage_todate": round(total_percentage_todate),
        "is_total_row": 1
    })

    return columns, raw_data
