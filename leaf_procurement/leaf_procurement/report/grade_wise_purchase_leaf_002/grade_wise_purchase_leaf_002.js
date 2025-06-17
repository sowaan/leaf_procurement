// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Grade Wise Purchase Leaf 002"] = {
	"filters": [
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
        {
            default: "Buying Grade",
            fieldname: "grade_type",
            fieldtype: "Select",
            label: "Grade Type",
            mandatory: 1,
            options: "Buying Grade\nReclassification Grade"
        },
        {
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "MultiSelectList",
			options: "Supplier",
			get_data: function (txt) {
				return frappe.db.get_link_options("Supplier", txt);
			},
		}

	]
};
