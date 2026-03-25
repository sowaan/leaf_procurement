frappe.query_reports["Process Order Listing Report"] = {
	"filters": [		
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
