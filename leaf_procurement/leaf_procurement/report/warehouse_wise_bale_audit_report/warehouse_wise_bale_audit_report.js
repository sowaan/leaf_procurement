// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["WAREHOUSE WISE BALE AUDIT REPORT"] = {
	"filters": [
		{
			"fieldname": "date",
			"label": "Date",
			"fieldtype": "Date",
			"default": "Today",
			"reqd": 1
		},
		// {
		// 	"fieldname": "to_date",
		// 	"label": "To Date",
		// 	"fieldtype": "Date",
		// 	"reqd": 1
		// },
		{
			"fieldname": "grade",
			"label": "Item Grade",
			"fieldtype": "Link",
			"options": "Item Grade"
		},
		{
			"fieldname": "sub_grade",
			"label": "Item Sub Grade",
			"fieldtype": "Link",
			"options": "Item Sub Grade"
		},
		{
			"fieldname": "warehouse",
			"label": "Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse"
		}
	]
};
