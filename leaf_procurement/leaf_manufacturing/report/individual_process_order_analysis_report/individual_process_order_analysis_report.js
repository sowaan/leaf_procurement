// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Individual Process Order Analysis Report"] = {
	filters: [		
		{
        fieldname: "process_order",
        label: "Process Order",
        fieldtype: "Link",
        options: "Process Order"        
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
