import frappe
from collections import defaultdict

def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Depot Description", "fieldname": "depot_description", "fieldtype": "Data", "width": 200},
        {"label": "Total Purchase - Nos Of Vouchers", "fieldname": "total_vouchers", "fieldtype": "Int", "width": 200},
        {"label": "Total Purchase - Kgs", "fieldname": "total_kgs", "fieldtype": "Float", "width": 150},
        {"label": "Total Purchase - Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 200},
        {"label": "Encashed - Nos Of Vouchers", "fieldname": "encashed_vouchers", "fieldtype": "Int", "width": 200},
        {"label": "Encashed - Kgs", "fieldname": "encashed_kgs", "fieldtype": "Float", "width": 150},
        {"label": "Encashed - Amount", "fieldname": "encashed_amount", "fieldtype": "Currency", "width": 200},
        {"label": "Payable - Nos Of Vouchers", "fieldname": "payable_vouchers", "fieldtype": "Int", "width": 200},
        {"label": "Payable - Kgs", "fieldname": "payable_kgs", "fieldtype": "Float", "width": 150},
        {"label": "Payable - Amount", "fieldname": "payable_amount", "fieldtype": "Currency", "width": 150},
    ]

def get_data(filters):
    conditions = ["docstatus = 1"]
    pii_conditions = ["1=1"]
    if filters.get("from_date"):
        conditions.append("posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("posting_date <= %(to_date)s")
    if filters.get("depot"):
        pii_conditions.append("warehouse = %(depot)s")

    condition_str = " AND ".join(conditions)
    pii_conditions = " AND ".join(pii_conditions)

    raw_data = frappe.db.sql(f"""
        SELECT
            DISTINCT pi.name AS voucher,
            pi_item.warehouse AS depot_description,
            pi.total_qty AS qty,
            pi.grand_total AS amount,
            pi.status AS status
        FROM (SELECT * FROM `tabPurchase Invoice` WHERE {condition_str}) pi
        JOIN (SELECT * FROM `tabPurchase Invoice Item` WHERE {pii_conditions}) pi_item ON pi.name = pi_item.parent
        GROUP BY pi.name, pi_item.warehouse
    """, filters, as_dict=True)

    results = {}
    for row in raw_data:
        if not row.depot_description:
            continue
        depot = row.depot_description
        if depot not in results:
            results[depot] = {
                "depot_description": depot,
                "total_vouchers": set(),
                "total_kgs": 0,
                "total_amount": 0,
                "encashed_vouchers": set(),
                "encashed_kgs": 0,
                "encashed_amount": 0,
                "payable_vouchers": set(),
                "payable_kgs": 0,
                "payable_amount": 0
            }

        r = results[depot]

        r["total_vouchers"].add(row.voucher)
        r["total_kgs"] += row.qty
        r["total_amount"] += row.amount

        if row.status == "Paid":
            r["encashed_vouchers"].add(row.voucher)
            r["encashed_kgs"] += row.qty
            r["encashed_amount"] += row.amount
        else:
            r["payable_vouchers"].add(row.voucher)
            r["payable_kgs"] += row.qty
            r["payable_amount"] += row.amount

    for depot, r in results.items():
        r["total_vouchers"] = len(r["total_vouchers"])
        r["encashed_vouchers"] = len(r["encashed_vouchers"])
        r["payable_vouchers"] = len(r["payable_vouchers"])

    return list(results.values())
