// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Purchase Vs GTN"] = {
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
			fieldname: "purchase_center",
			fieldtype: "Link",
			label: __("Purchase Center"),
			options: "Warehouse",
			get_query: function () {
				return {
					filters: { is_group: 0, custom_is_depot: 1 }
				};
			}
		},
		{
			fieldname: "show_rejected",
			fieldtype: "Check",
			label: __("Include Rejected Bales in Voucher"),
			default: 0
		}
	]
};
