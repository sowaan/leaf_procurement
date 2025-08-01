// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Reweighting Detail Report(GTN)"] = {
	"filters": [
		{
			fieldname: "date",
			fieldtype: "Date",
			label: "Date",
			default: "Today",
			mandatory: 1
		},
		{
			fieldname: "depot",
			fieldtype: "Link",
			label: __("Warehouse"),
			options: "Warehouse"
			// mandatory: 1
			
		},
        // {
        //     default: "Today",
        //     fieldname: "to_date",
        //     fieldtype: "Date",
        //     label: "To Date",
        //     mandatory: 1
        // }
	]
};
