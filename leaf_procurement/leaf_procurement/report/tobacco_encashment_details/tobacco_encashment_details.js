// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Tobacco Encashment Details"] = {
	"filters": [
		{
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
		{
            fieldname: "depot",
            label: "Depot",
            fieldtype: "Link",
            options: "Warehouse",
        }
	]
};
