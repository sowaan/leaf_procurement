import frappe
from frappe.utils import getdate

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "Cashier", "fieldname": "mode_of_payment", "fieldtype": "Link", "options": "Mode of Payment", "width": 150},
        {"label": "Amount Received", "fieldname": "amount_received", "fieldtype": "Currency", "width": 150},
        {"label": "Encashed (No. of Vouchers)", "fieldname": "voucher_count", "fieldtype": "Int", "width": 220},
        {"label": "Encashed (Amount)", "fieldname": "encashed_amount", "fieldtype": "Currency", "width": 180},
        {"label": "Cash Balance with Cashier", "fieldname": "cash_balance", "fieldtype": "Currency", "width": 210}
    ]

def get_data(filters):
    conditions = ["docstatus = 1"]
    if filters.get("from_date"):
        conditions.append("posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("posting_date <= %(to_date)s")
    if filters.get("cashier"):
        conditions.append("mode_of_payment = %(cashier)s")

    conditions_str = " AND ".join(conditions)

    return frappe.db.sql(f"""
        SELECT
            pe.posting_date,
            pe.mode_of_payment,
            COALESCE(SUM(pe.paid_amount), 0) AS amount_received,
            COALESCE(COUNT(DISTINCT pe.name), 0) AS voucher_count,
            COALESCE(SUM(ge.debit), 0) AS encashed_amount,
            (COALESCE(SUM(pe.paid_amount), 0) - COALESCE(SUM(ge.debit), 0)) AS cash_balance
        FROM (SELECT * FROM `tabPayment Entry` WHERE {conditions_str}) pe
        JOIN `tabGL Entry` ge 
            ON pe.name = ge.voucher_no 
            AND ge.voucher_type = 'Payment Entry'
            AND ge.is_cancelled = 0
            AND ge.debit > 0
        GROUP BY pe.mode_of_payment
        ORDER BY pe.posting_date, pe.mode_of_payment
    """, filters, as_dict=True)
