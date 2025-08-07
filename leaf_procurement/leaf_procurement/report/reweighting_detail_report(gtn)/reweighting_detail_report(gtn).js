// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Reweighting Detail Report(GTN)"] = {
	"filters": [
		{
			fieldname: "from_date",
			fieldtype: "Date",
			label: __("From Date"),
			default: "Today",
			mandatory: 1
		},
		{
			fieldname: "to_date",
            fieldtype: "Date",
            label: __("To Date"),
            default: "Today",
            mandatory: 1
        },
		{
			fieldname: "gtn",
            fieldtype: "Link",
            label: __("GTN"),
            options: "Goods Transfer Note",
		},
		{
			fieldname: "depot",
			fieldtype: "MultiSelectList",
			label: __("Depot"),
			options: "Warehouse",
			get_data: function (txt) {
				return frappe.db.get_link_options("Warehouse", txt, {
					is_group: 0,
					custom_is_depot: 1,
				});
			},
			
		},
		{
			fieldname: "warehouse",
			fieldtype: "MultiSelectList",
			label: __("Warehouse"),
			options: "Warehouse",
			get_data: function (txt) {
				return frappe.db.get_link_options("Warehouse", txt, {
					is_group: 0,
					custom_is_depot: 0,
				});
			},
			
		},
        
	]
};
