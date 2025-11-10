# Tobacco Reclassification Grade × Warehouse Pivot (FAST SQL VERSION)

import frappe


def execute(filters=None):
    filters = frappe._dict(filters or {})

    warehouses = get_warehouses()
    columns = get_columns(warehouses)
    data = get_data(filters, warehouses)

    return columns, data


# ---------------------------------------
# 1. Load active warehouses (fast)
# ---------------------------------------
def get_warehouses():
    return frappe.db.sql("""
        SELECT name, custom_short_code
        FROM `tabWarehouse`
        WHERE disabled = 0
          AND IFNULL(custom_is_depot, 0) = 0
        ORDER BY name
    """, as_dict=True)


# ---------------------------------------
# 2. Build report columns (pivot)
# ---------------------------------------
def get_columns(warehouses):
    columns = [
        {
            "label": "Reclassification Grade",
            "fieldname": "reclassification_grade",
            "fieldtype": "Data",
            "width": 180
        }
    ]

    for wh in warehouses:
        short = wh.custom_short_code or wh.name.replace(" ", "_")
        columns.append({
            "label": f"{wh.name} Qty",
            "fieldname": f"{short}_qty",
            "fieldtype": "Float",
            "precision": 2,
            "width": 120
        })
        columns.append({
            "label": f"{wh.name} Bales",
            "fieldname": f"{short}_bales",
            "fieldtype": "Int",
            "width": 90
        })

    columns.append({
        "label": "Total Qty",
        "fieldname": "total_qty",
        "fieldtype": "Float",
        "precision": 2,
        "width": 130
    })
    columns.append({
        "label": "Total Bales",
        "fieldname": "total_bales",
        "fieldtype": "Int",
        "width": 90
    })

    return columns


# ---------------------------------------
# 3. FAST: One SQL Query to pivot stock
# ---------------------------------------
def get_data(filters, warehouses):
    # Build warehouse SUM() parts dynamically
    wh_sql_parts = []
    for wh in warehouses:
        name = wh.name.replace("'", "''")
        short = wh.custom_short_code or wh.name.replace(" ", "_")

        wh_sql_parts.append(f"""
            SUM(CASE WHEN sle.warehouse = '{name}' THEN sle.actual_qty ELSE 0 END) AS `{short}_qty`,
            SUM(CASE WHEN sle.warehouse = '{name}' THEN 1 ELSE 0 END) AS `{short}_bales`
        """)

    wh_sql = ",\n".join(wh_sql_parts)

    # Date filters
    condition = ""
    params = {"item": "Tobacco"}
    if filters.get("from_date") and filters.get("to_date"):
        condition = "AND sle.posting_date BETWEEN %(from_date)s AND %(to_date)s"
        params.update({
            "from_date": filters.from_date,
            "to_date": filters.to_date
        })

    # FINAL QUERY
    query = f"""
        SELECT
            sle.reclassification_grade,
            {wh_sql},
            SUM(sle.actual_qty) AS total_qty,
            SUM(1) AS total_bales
        FROM `tabStock Ledger Entry` sle
        WHERE sle.item_code = %(item)s
          AND sle.is_cancelled = 0
          AND IFNULL(sle.reclassification_grade, '') != ''
          {condition}
        GROUP BY sle.reclassification_grade
        ORDER BY sle.reclassification_grade
    """

    return frappe.db.sql(query, params, as_dict=True)
