// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Cashier Balance Report"] = {
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
            fieldname: "cashier",
            label: "Cashier",
            fieldtype: "Link",
            options: "Mode of Payment",
        }
	]
};

