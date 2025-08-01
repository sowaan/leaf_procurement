// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Reweighment Report"] = {
	"filters": [
		
		{
            fieldname: "date",
            fieldtype: "Date",
            label: "Date",
            mandatory: 1,
            default: "Today",
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
