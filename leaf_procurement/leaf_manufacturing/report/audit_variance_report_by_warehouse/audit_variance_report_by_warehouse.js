// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Audit Variance Report By Warehouse"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			default: "Today"
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			default: "Today"
		},
		{
			fieldname: "season",
			label: "Season",
			fieldtype: "Data"
		},
		{
			fieldname: "warehouse",
			label: "Warehouse",
			fieldtype: "Link",
			options: "Warehouse"
		}
	]
};
