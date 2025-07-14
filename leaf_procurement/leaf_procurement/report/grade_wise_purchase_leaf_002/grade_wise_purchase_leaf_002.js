// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Grade Wise Purchase Leaf 002"] = {
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
        // {
        //     fieldname: "grade_type",
        //     label: "Grade Type",
        //     fieldtype: "Select",
        //     options: ["Buying Grade", "Reclassification Grade"].join("\n"),
        //     default: "Buying Grade",
        //     reqd: 1
        // },
        {
            fieldname: "warehouse",
            label: "Warehouse",
            fieldtype: "Link",
            options: "Warehouse"
        },
        {
            fieldname: "item_grade",
            label: "Item Grade",
            fieldtype: "Link",
            options: "Item Grade"
        },
        {
            fieldname: "item_sub_grade",
            label: "Item Sub Grade",
            fieldtype: "Link",
            options: "Item Sub Grade"
        },
        {
            fieldname: "reclassification_grade",
            label: "Reclassification Grade",
            fieldtype: "Link",
            options: "Reclassification Grade"
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
