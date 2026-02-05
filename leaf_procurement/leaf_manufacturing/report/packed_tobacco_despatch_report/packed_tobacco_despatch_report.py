# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe import (_,utils)


def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    # -----------------------------
    # Columns
    # -----------------------------
    columns = [
        {
            "label": "TSA NO",
            "fieldname": "tsa_number",
            "fieldtype": "Data",            
            "width": 150,
        },
        {
            "label": "Receiving Location",
            "fieldname": "receiving_location",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 100,
        },
        {"label": "Grade", "fieldname": "prized_grade", "fieldtype": "Data", "width": 80},
        {"label": "Nos", "fieldname": "nos", "fieldtype": "Int", "width": 80},        
        {"label": "Kgs", "fieldname": "kgs", "fieldtype": "Float", "width": 120},
        
    ]

     # -----------------------------
    # Build conditions
    # -----------------------------
    conditions = []	
    params = {}

    if filters.get("location"):
        conditions.append("ts.location_from = %(location)s")
        params["location"] = filters.get("location")

    if filters.get("from_date"):
        conditions.append("ts.date >= %(from_date)s")
        params["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("ts.date <= %(to_date)s")
        params["to_date"] = filters.get("to_date")

    condition_str = " AND " + " AND ".join(conditions) if conditions else ""

    # -----------------------------
    # SQL Query
    # -----------------------------
    data = frappe.db.sql(
        f"""
        SELECT
            ts.tsa_number,
            ts.location_to AS receiving_location,            

            tsd.prized_grade AS prized_grade,            
            tsd.quantity AS nos,
            tsd.kgs AS kgs

        FROM `tabTobacco Shipment` ts
        LEFT JOIN `tabTobacco Shipment Detail` tsd
            ON ts.name = tsd.parent
        WHERE
            ts.docstatus = 1         
            {condition_str}        

        ORDER BY
            ts.date DESC
        """,
        params,
        as_dict=True,
    )

    return columns, data