// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["GLT Summary"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
		},

		{
			fieldname: "location",
			label: __("GLT (Location)"),
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "shift",
			label: __("Shift"),
			fieldtype: "Select",
			options: "\nA\nB\nC",
		},
		{
			fieldname: "season",
			label: __("Season (Year)"),
			fieldtype: "Int",
			description: "e.g. 2024",
		},
	],
};
