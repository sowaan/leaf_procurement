# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe  # type: ignore


def execute(filters=None):    
    
    if not filters:
        filters = frappe._dict()

    # -----------------------------
    # Columns
    # -----------------------------
    columns = [
        {
            "label": "Packed Grade",
            "fieldname": "prized_grade",
            "fieldtype": "Link",
            "options": "Prized Grade",
            "width": 150,
        },        
        {"label": "Packing Type", "fieldname": "packing_type", "fieldtype": "Data", "width": 80},        
        {"label": "Quantity", "fieldname": "quantity", "fieldtype": "Float", "width": 120},
        {"label": "Kgs", "fieldname": "kgs", "fieldtype": "Float", "width": 120}
        
    ]

    # -----------------------------
    # Build conditions
    # -----------------------------
    conditions = []
    params = {}

    if filters.get("process_order"):
        conditions.append("po.name = %(process_order)s")
        params["process_order"] = filters.get("process_order")

    if filters.get("from_date"):
        conditions.append("po.date >= %(from_date)s")
        params["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("po.date <= %(to_date)s")
        params["to_date"] = filters.get("to_date")
        
    condition_str = " AND " + " AND ".join(conditions) if conditions else ""

	
    # -----------------------------
    # SQL Query
    # -----------------------------
    data = frappe.db.sql(
        f"""
        SELECT            
            pice.prized_grade,
            pice.packing_type AS packing_type,
            pice.quantity AS quantity,
            pice.kgs kgs

        FROM `tabProcess Order` po
        JOIN `tabPrized Item Creation` pic
            ON po.name = pic.process_order
            AND pic.docstatus = 1
        LEFT JOIN `tabPrized Item Creation Entry` pice
            ON pice.parent = pic.name
            AND pice.parenttype = 'Prized Item Creation'
			AND pice.docstatus = 1
        WHERE
            po.docstatus = 1
            {condition_str}    

        ORDER BY
            po.date DESC
        """,
        params,
        as_dict=True,
    )   

    return columns, data