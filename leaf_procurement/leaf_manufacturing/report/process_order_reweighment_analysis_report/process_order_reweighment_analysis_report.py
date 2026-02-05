# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe  # type: ignore


def execute(filters=None):
    if not filters:
        filters = frappe._dict()

    # -----------------------------
    # Columns
    # -----------------------------
    columns = [
        {
            "label": "PO Order No",
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Process Order",
            "width": 150,
        },
        {
            "label": "PO Date",
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 100,
        },
        {"label": "Shift", "fieldname": "shift", "fieldtype": "Data", "width": 80},
        {"label": "Nos", "fieldname": "nos", "fieldtype": "Int", "width": 80},
        {"label": "Purchase Kgs", "fieldname": "purchase_kgs", "fieldtype": "Float", "width": 120},
        {"label": "Reweight Kgs", "fieldname": "reweight_kgs", "fieldtype": "Float", "width": 120},
        {"label": "Loss Kgs", "fieldname": "loss_kgs", "fieldtype": "Float", "width": 120},
        {"label": "Loss %", "fieldname": "loss_percentage", "fieldtype": "Percent", "width": 100},
    ]

    # -----------------------------
    # Build conditions
    # -----------------------------
    conditions = []
    params = {}

    if filters.get("location"):
        conditions.append("po.location = %(location)s")
        params["location"] = filters.get("location")

    if filters.get("from_date"):
        conditions.append("po.date >= %(from_date)s")
        params["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions.append("po.date <= %(to_date)s")
        params["to_date"] = filters.get("to_date")

    condition_str = " AND " + " AND ".join(conditions) if conditions else ""

    # -----------------------------
    # SQL Query
    # -----------------------------
    data = frappe.db.sql(
        f"""
        SELECT
            po.name,
            po.date AS date,
            po.shift,

            COUNT(cd.name) AS nos,
            SUM(cd.purchase_weight) AS purchase_kgs,
            SUM(cd.reweight) AS reweight_kgs,
            SUM(cd.gain_loss) AS loss_kgs

        FROM `tabProcess Order` po
        LEFT JOIN `tabLeaf Consumption` lc
            ON lc.process_order = po.name
        LEFT JOIN `tabLeaf Consumption Detail` cd
            ON cd.parent = lc.name
            AND cd.parenttype = 'Leaf Consumption'

        WHERE
            po.docstatus = 1
            {condition_str}

        GROUP BY
            po.name, po.date, po.shift

        ORDER BY
            po.date DESC
        """,
        params,
        as_dict=True,
    )

    # -----------------------------
    # Final calculations
    # -----------------------------
    for row in data:
        reweight = row.reweight_kgs or 0
        loss = row.loss_kgs or 0
        row["loss_percentage"] = (loss / reweight * 100) if reweight else 0

    return columns, data