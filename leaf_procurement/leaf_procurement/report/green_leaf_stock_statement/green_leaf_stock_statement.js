// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Green Leaf Stock Statement"] = {
	"filters": [
		{
			fieldname: "from_date",
			fieldtype: "Date",
			label: __("From Date"),
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			mandatory: 1
		},
		{
			fieldname: "to_date",
            fieldtype: "Date",
            label: __("To Date"),
            default: "Today",
            mandatory: 1
        },
	]
};
