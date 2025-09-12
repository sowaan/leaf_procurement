// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["PAYMENT 04"] = {
	"filters": [
 {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1,
            
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "supplier",
            "label": __("Grower"),
            "fieldtype": "Link",
            "options": "Supplier",
            "reqd": 0
        },
        {
            "fieldname": "warehouse",
            "label": __("Leaf Buying Depot"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "reqd": 0
        },
        // {
        //     "fieldname": "status",
        //     "label": __("Invoice Status"),
        //     "fieldtype": "Select",
        //     "options": [
        //         "",
        //         "Draft",
        //         "Submitted",
        //         "Paid",
        //         "Partly Paid",
        //         "Unpaid",
        //         "Overdue",
        //         "Cancelled"
        //     ]
        // }
	]
};
