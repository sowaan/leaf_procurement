// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Reweighment Report Summary"] = {
	"filters": [
		{
            fieldname: "from_date",
            fieldtype: "Date",
            label: "From Date",
            default: "Today",
            mandatory: 1
        },
        {
            fieldname: "to_date",
            fieldtype: "Date",
            label: "To Date",
            default: "Today",
            mandatory: 1
        },
        {
			fieldname: "depot",
			fieldtype: "Link",
			label: __("Warehouse"),
			options: "Warehouse"	,
                        "get_query": function() {
                return {
                    filters: {
                        "custom_is_depot": 0
                    }
                }
            }		
		},
        {
			fieldname: "gtn",
			fieldtype: "Link",
			label: __("GTN umber"),
			options: "Goods Transfer Note"			
		},	
        // {
        //     default: "Today",
        //     fieldname: "to_date",
        //     fieldtype: "Date",
        //     label: "To Date",
        //     mandatory: 1
        // },
	]
};
