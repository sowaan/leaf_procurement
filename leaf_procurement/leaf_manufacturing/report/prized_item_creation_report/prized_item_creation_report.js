// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Prized Item Creation Report"] = {
	"filters": [
		{
			"fieldname": "process_order",
			"fieldtype": "Link",
			"label": "Process Order",
			"mandatory": 0,
			"options": "Process Order",
			"wildcard_filter": 0,
			get_query: function () {
				return {
					filters: {
						docstatus: 1
					}
				}
			}
		},
		{
			"location": "location",
			"fieldname": "location",
			"fieldtype": "Link",
			"label": "Location",
			"mandatory": 0,
			"options": "Warehouse",
			"wildcard_filter": 0,

		},
		{
			"fieldname": "prized_grade",
			"fieldtype": "Link",
			"label": "Prized Grade",
			"mandatory": 0,
			"options": "Prized Grade",
			"wildcard_filter": 0
		},
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",
			"mandatory": 0,
			"wildcard_filter": 0
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",
			"mandatory": 0,
			"wildcard_filter": 0
		}
	]
};
