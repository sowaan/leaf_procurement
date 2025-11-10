import frappe

def execute(filters=None):
    filters = filters or {}
    columns, data = get_report_data(filters)
    return columns, data


def get_report_data(filters):

    # -------------------------------------------------------------------------
    # 1. Load active, non-depot warehouses WITH short codes
    # -------------------------------------------------------------------------
    warehouses = frappe.db.sql("""
        SELECT wh.name, wh.custom_short_code
        FROM `tabWarehouse` wh
        WHERE wh.disabled = 0
          AND IFNULL(wh.custom_is_depot, 0) = 0
          AND wh.custom_short_code IS NOT NULL
        ORDER BY wh.name
    """, as_dict=True)

    if not warehouses:
        frappe.throw("No warehouses found with custom_short_code and non-depot flag.")

    # -------------------------------------------------------------------------
    # Build initial columns
    # -------------------------------------------------------------------------
    columns = [
        {"label": "Grade", "fieldname": "grade", "fieldtype": "Data", "width": 150}
    ]

    wh_sql_parts = []
    wh_params = []

    # -------------------------------------------------------------------------
    # 2. Build warehouse pivot columns USING short_code
    # -------------------------------------------------------------------------
    for wh in warehouses:
        wh_name = wh.name
        short = wh.custom_short_code.strip()

        safe_wh_name = wh_name.replace("'", "''")  # make literal SQL safe

        wh_sql_parts.append(f"""
            SUM(CASE WHEN sle.warehouse = '{safe_wh_name}' THEN ABS(sle.actual_qty) ELSE 0 END) AS {short}_kgs,
            SUM(CASE WHEN sle.warehouse = '{safe_wh_name}' THEN 1 ELSE 0 END) AS {short}_bales
        """)

        wh_params += [wh_name, wh_name]

        # Add visible report columns
        columns.append({
            "label": f"{wh_name} Bales",
            "fieldname": f"{short}_bales",
            "fieldtype": "Float",
            "precision": 0,
            "width": 90
        })

        columns.append({
            "label": f"{wh_name} KGs",
            "fieldname": f"{short}_kgs",
            "fieldtype": "Float",
            "precision": 2,
            "width": 110
        })

    wh_sql = ",\n".join(wh_sql_parts)

    # -------------------------------------------------------------------------
    # 3. WHERE filters
    # -------------------------------------------------------------------------
    conditions = ["sle.is_cancelled = 0"]
    params = {}

    # if filters.get("company"):
    #     conditions.append("sle.company = %s")
    #     params.append(filters["company"])

    # if filters.get("from_date") and filters.get("to_date"):
    #     conditions.append("sle.posting_date BETWEEN %(from_date)s AND %(to_date)s")
    #     params["from_date"] = filters["from_date"]
    #     params["to_date"] = filters["to_date"]
    # else:
    if filters.get("to_date"):
        conditions.append("sle.posting_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]
    
    where_clause = " AND ".join(conditions)
    frappe.log_error("Warehouse Pivot Where Clause", where_clause)
    # -------------------------------------------------------------------------
    # 4. Final SQL Pivot Query
    # -------------------------------------------------------------------------
    query = f"""
        SELECT
            sle.reclassification_grade AS grade,
            {wh_sql},
            SUM(ABS(sle.actual_qty)) AS total_kgs,
            COUNT(sle.name) AS total_bales
        FROM `tabStock Ledger Entry` sle
        WHERE {where_clause}
          AND IFNULL(sle.reclassification_grade, '') != ''
        GROUP BY sle.reclassification_grade
        ORDER BY sle.reclassification_grade
    """
    frappe.log_error("Warehouse Pivot Query", query)
    final_params = params

    data = frappe.db.sql(query, final_params, as_dict=True)

    # -------------------------------------------------------------------------
    # 5. Final Totals Column
    # -------------------------------------------------------------------------
    columns.append({
        "label": "Total Bales",
        "fieldname": "total_bales",
        "fieldtype": "Float",
        "precision": 0,
        "width": 110
    })

    columns.append({
        "label": "Total KGs",
        "fieldname": "total_kgs",
        "fieldtype": "Float",
        "precision": 2,
        "width": 110
    })

    # Debugging
    # frappe.log_error("Warehouse Pivot Using Short Codes", f"Query:\n{query}\nParams:\n{final_params}")

    return columns, data
