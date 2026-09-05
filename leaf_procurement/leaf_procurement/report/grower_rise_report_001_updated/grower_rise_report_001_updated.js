// Copyright (c) 2026, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Grower Rise Report 001 Updated"] = {
    onload: function(report) {
        const warehouse_filter = report.get_filter("warehouse");
        if (warehouse_filter) {
            warehouse_filter.get_query = function() {
                return {
                    filters: { custom_is_depot: 1 }
                };
            };
        }
    }
};
