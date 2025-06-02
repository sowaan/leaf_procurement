# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	coloumns = get_coloumns()
	data = get_data(filters)
	return coloumns, data





def get_coloumns():
	columns = [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "GTN No", "fieldname": "gtn_no", "fieldtype": "Data", "width": 120},
        {"label": "TSA Number", "fieldname": "tsa_number", "fieldtype": "Data", "width": 140},
        {"label": "Veh No", "fieldname": "veh_no", "fieldtype": "Data", "width": 100},
        {"label": "Bale", "fieldname": "bale", "fieldtype": "Int", "width": 80},
        {"label": "KGs", "fieldname": "kgs", "fieldtype": "Float", "width": 100},
        {"label": "Receiving Whs", "fieldname": "receiving_whs", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"label": "Remarks", "fieldname": "remarks", "fieldtype": "Data", "width": 150},
    ]
	return columns





def get_data(filters):
    conditions = "WHERE gtn.docstatus = 1"
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND gtn.date BETWEEN %(from_date)s AND %(to_date)s"
    if filters.get("depot"):
        conditions += " AND gtn.location_warehouse = %(depot)s"

    query = f"""
        SELECT 
            gtn.date as date,
            gtn.name as gtn_no,
            gtn.tsa_number as tsa_number,
            gtn.vehicle_number as veh_no,
            COUNT(gtni.name) as bale,
            SUM(gtni.weight) as kgs,
            gtn.receiving_location as receiving_whs,
            gtn.remarks as remarks
        FROM `tabGoods Transfer Note` gtn
        LEFT JOIN `tabGoods Transfer Note Items` gtni ON gtni.parent = gtn.name
        {conditions}
        GROUP BY gtn.name
        ORDER BY gtn.date DESC
    """

    return frappe.db.sql(query, filters, as_dict=True)