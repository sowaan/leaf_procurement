// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Packed Stock Status"] = {
	"filters": [		
		{
			"location": "location",
			"fieldname": "location",
			"fieldtype": "Link",
			"label": "Manufacturing Location",
			"mandatory": 0,
			"options": "Warehouse",
			"wildcard_filter": 0,

		},		
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "Shipment Date From",
			"mandatory": 0,
			"wildcard_filter": 0
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "Shipment Date TO",
			"mandatory": 0,
			"wildcard_filter": 0
		}
	]
};
