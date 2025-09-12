// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Grower Quota Vs Actual Purchase ToDate"] = {
	"filters": [
				{
			"fieldname": "date",
			"label": "Date",
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": "Today",
			"reqd": 1
		},
		{
			"fieldname": "grower",
			"label": "Grower",
			"fieldtype": "Link",
			"options": "Supplier"
		},
	]
};
