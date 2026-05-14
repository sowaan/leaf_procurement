// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Audit Master Report"] = {
	"filters": [
		{
			fieldname: "from_date",
			fieldtype: "Date",
			label: __("From Date"),
			default: frappe.datetime.get_today(),
			mandatory: 1
		},
		{
			fieldname: "to_date",
			fieldtype: "Date",
			label: __("To Date"),
			default: frappe.datetime.get_today(),
			mandatory: 1
		},
		{
			fieldname: "warehouse",
			fieldtype: "Link",
			label: __("Warehouse"),
			options: "Warehouse",
			get_query: function () {
				return {
					filters: { is_group: 0, custom_is_depot: 0 }
				};
			}
		},
		{
			fieldname: "gtn",
			fieldtype: "Link",
			label: __("GTN"),
			options: "Goods Transfer Note"
		},
		{
			fieldname: "gtn_status",
			fieldtype: "Select",
			label: __("GTN Status"),
			options: "All\nWith GTN\nWithout GTN",
			default: "All"
		}
	]
};
