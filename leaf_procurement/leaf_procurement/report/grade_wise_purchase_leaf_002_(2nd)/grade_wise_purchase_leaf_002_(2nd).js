frappe.query_reports["Grade Wise Purchase Leaf 002 (2nd)"] = {
    filters: [
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
            fieldname: "warehouse",
            label: "Warehouse",
            fieldtype: "Link",
            options: "Warehouse"
        },
        {
            fieldname: "grade_type",
            label: "Grade Type",
            fieldtype: "Select",
            options: ["Item Grade", "Reclassification Grade"].join("\n"),
            default: "Item Grade",
            reqd: 1
        },
        {
			fieldname: "grade",
			label: "Grade",
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				const doctype = frappe.query_report.get_filter_value("grade_type");
				if (!doctype) return [];
		
				return frappe.db.get_link_options(doctype, txt);
			},
			depends_on: "eval:doc.grade_type"
		},		
        {
            fieldname: "supplier",
            label: "Supplier",
            fieldtype: "MultiSelectList",
            options: "Supplier",
            get_data: function (txt) {
                return frappe.db.get_link_options("Supplier", txt);
            }
        },
        {
            fieldname: "include_rejected_bales",
            label: "Include Rejected Bales",
            fieldtype: "Check"
        }
    ],

    after_datatable_render(datatable) {
        const rows = datatable.bodyScrollable.querySelectorAll(".dt-row");

        if (rows.length > 0) {
            const lastRow = rows[rows.length - 1];
            lastRow.style.fontWeight = "bold";

            const cells = lastRow.querySelectorAll(".dt-cell");
            cells.forEach(cell => {
                cell.style.backgroundColor = "#e0e0e0";
            });
        }
    }
};
