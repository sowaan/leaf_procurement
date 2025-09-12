// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Incorrect Invoices"] = {
	"filters": [
        {
            "fieldname": "warehouse",
            "label": "Depot",
            "fieldtype": "Link",
            "options": "Warehouse",
            "reqd": 0,
            "get_query": function() {
                return {
                    filters: {
                        "custom_is_depot": 1
                    }
                }
            }
        }
	],
	onload: function(report) {
		// Add button
		report.page.add_inner_button(__("Correct Invoices"), function() {
			let filters = report.get_values();
			frappe.call({
				method: "leaf_procurement.leaf_procurement.report.incorrect_invoices.incorrect_invoices.correct_invoices",
				args: { filters: filters },
				callback: function(r) {
					if(!r.exc) {
						frappe.msgprint(__("Invoices corrected successfully"));
						report.refresh();
					}
				}
			});
		});
	}	
};
