// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["GLT ISSUANCE AUDIT"] = {
	onload(report) {
		report.page.add_inner_message(
			'<span style="font-size:12px; color: #e67e22; font-weight:500;">' +
			'&#9432; If a bale has multiple audit entries, only the latest audit record is used for the Re-weight column.' +
			'</span>'
		);
	},
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
			fieldname: "shift",
			label: __("Shift"),
			fieldtype: "Select",
			options: "\nA\nB\nC",
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
			get_query: () => ({
				filters: { custom_is_depot: 0 },
			}),
		},
		{
			fieldname: "purchase_center",
			label: __("Purchase Center (Depot)"),
			fieldtype: "Link",
			options: "Warehouse",
			get_query: () => ({
				filters: { custom_is_depot: 1 },
			}),
		},
		{
			fieldname: "audit_status",
			label: __("Audit Status"),
			fieldtype: "Select",
			options: "\nWith Audit\nWithout Audit",
		},
	],
};
