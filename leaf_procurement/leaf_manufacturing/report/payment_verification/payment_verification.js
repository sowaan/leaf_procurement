// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Payment Verification"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			default: frappe.datetime.month_start()
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			default: frappe.datetime.get_today()
		},
		{
			fieldname: "warehouse",
			label: "Warehouse",
			fieldtype: "Link",
			options: "Warehouse"
		},
		{
			fieldname: "depot",
			label: "Depot",
			fieldtype: "Link",
			options: "Warehouse"
		},
		{
			fieldname: "season",
			label: "Season",
			fieldtype: "Data"
		}
	]
};
