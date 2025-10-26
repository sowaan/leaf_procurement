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
        {
            "label": "Depot",
            "fieldname": "custom_location_warehouse",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Supplier Name",
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "width": 200
        },        {
            "label": "Father Name",
            "fieldname": "custom_father_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "NIC Number",
            "fieldname": "custom_nic_number",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": "Mobile No",
            "fieldname": "mobile_no",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": "Village",
            "fieldname": "custom_village",
            "fieldtype": "Data",
            "width": 140
        },        
        {
            "label": "Custom Quota Allowed",
            "fieldname": "custom_quota_allowed",
            "fieldtype": "Float",
            "width": 150
        },
        {
            "label": "Total Qty",
            "fieldname": "total_qty",
            "fieldtype": "Float",
            "width": 150
        },
		        {
            "label": "Balance Quantity",
            "fieldname": "balance_qty",
            "fieldtype": "Float",
            "width": 150
        },
]


def get_data(filters):
    # This block safely builds the conditions and parameters for the query
    conditions = []
    params = filters.copy()
    
    if filters.get("date") and filters.get("to_date"):
        conditions.append("pi.posting_date BETWEEN %(date)s AND %(to_date)s")
    elif filters.get("date"):
        conditions.append("pi.posting_date >= %(date)s")
    elif filters.get("to_date"):
        conditions.append("pi.posting_date <= %(to_date)s")
    if filters.get("depot"):
        conditions.append("th.custom_location_warehouse = %(depot)s")    
    if filters.get("grower"):
        conditions.append("th.name = %(grower)s")  
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # This single query performs all filtering, aggregation, and calculation
    query = f"""
SELECT  th.custom_location_warehouse, th.name, th.supplier_name ,
       th.custom_father_name ,
       th.custom_nic_number ,
       th.mobile_no , th.custom_village,
       th.custom_quota_allowed ,
       sum(pi.total_qty) AS total_qty,
       th.custom_quota_allowed - sum(pi.total_qty) AS balance_qty
  FROM `tabSupplier` AS th
 INNER JOIN `tabPurchase Invoice` AS pi
    ON th.name = pi.supplier
     {where_clause}
 GROUP BY  th.custom_location_warehouse, th.name, th.supplier_name,
          th.custom_father_name,
          th.custom_nic_number,
          th.mobile_no,th.custom_village
        ORDER BY
            th.supplier_name
    """

    return frappe.db.sql(query, params, as_dict=True)
