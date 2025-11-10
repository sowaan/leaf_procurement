// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Green Leaf Stock Statement"] = {
	"filters": [

		{
			fieldname: "to_date",
            fieldtype: "Date",
            label: __("As Of Date"),
            default: "Today",
            mandatory: 1
        },
	]
};
