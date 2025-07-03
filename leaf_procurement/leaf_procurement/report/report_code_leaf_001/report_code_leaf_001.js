// Copyright (c) 2025, Sowaan and contributors
// For license information, please see license.txt

frappe.query_reports["Report Code Leaf 001"] = {
    after_datatable_render(datatable) {
        console.log("✅ Styling last row with background");

        const allRows = datatable.bodyScrollable.querySelectorAll(".dt-row");

        if (allRows.length > 0) {
            const lastRow = allRows[allRows.length - 1];
            lastRow.style.fontWeight = "bold";

            // Set background on each cell
            const cells = lastRow.querySelectorAll(".dt-cell");
            cells.forEach(cell => {
                cell.style.backgroundColor = "#e0e0e0"; // Light gray
            });
        }
    }
};
