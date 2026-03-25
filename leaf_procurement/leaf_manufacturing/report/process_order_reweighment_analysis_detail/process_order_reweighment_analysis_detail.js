// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Process Order Reweighment Analysis Detail"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today()
		},
		{
			fieldname: "location",
			label: __("Location"),
			fieldtype: "Link",
			options: "Warehouse"
		}
	]
};
