// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Reweighment Report Summary"] = {
	"filters": [
		{
			fieldname: "depot",
			fieldtype: "Link",
			label: __("Warehouse"),
			options: "Warehouse"			
		},
		{
            fieldname: "from_date",
            fieldtype: "Date",
            label: "From Date",
            mandatory: 1
        },
        {
            default: "Today",
            fieldname: "to_date",
            fieldtype: "Date",
            label: "To Date",
            mandatory: 1
        },
	]
};
