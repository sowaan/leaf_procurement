import frappe
from frappe.utils import getdate

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Cashier", "fieldname": "mode_of_payment", "fieldtype": "Link", "options": "Mode of Payment", "width": 150},
        {"label": "Amount Received", "fieldname": "amount_issued", "fieldtype": "Currency", "width": 150},
        {"label": "Encashed (No. of Vouchers)", "fieldname": "voucher_count", "fieldtype": "Int", "width": 220},
        {"label": "Encashed (Amount)", "fieldname": "encashed_amount", "fieldtype": "Currency", "width": 180},
        {"label": "Cash Balance with Cashier", "fieldname": "cash_balance", "fieldtype": "Currency", "width": 210}
    ]

def get_data(filters):
    # conditions = ["docstatus = 1"]
    # if filters.get("from_date"):
    #     conditions.append("posting_date >= %(from_date)s")
    # if filters.get("to_date"):
    #     conditions.append("posting_date <= %(to_date)s")
    # if filters.get("cashier"):
    #     conditions.append("mode_of_payment = %(cashier)s")

    # conditions_str = " AND ".join(conditions)

    # sqlquery = frappe.db.sql(f"""
    #     SELECT
    #         pe.posting_date,
    #         pe.mode_of_payment,
    #         COALESCE(SUM(ge.debit), 0) AS amount_received,
    #         COALESCE(COUNT(DISTINCT pe.name), 0) AS voucher_count,
    #         COALESCE(SUM(pe.paid_amount), 0) AS encashed_amount,
    #         0 AS cash_balance
    #     FROM (SELECT * FROM `tabPayment Entry` WHERE {conditions_str}) pe
    #     JOIN `tabGL Entry` ge 
    #         ON pe.name = ge.voucher_no 
    #         AND ge.account = pe.paid_from
    #         AND ge.voucher_type = 'Payment Entry'
    #         AND ge.is_cancelled = 0
    #     GROUP BY pe.mode_of_payment
    #     ORDER BY pe.posting_date, pe.mode_of_payment
    # """, filters, as_dict=True)
    filters = frappe._dict(filters or {})

    pe_conditions = ["pe.docstatus = 1"]
    je_conditions = ["je.docstatus = 1"]

    if filters.get("from_date"):
        pe_conditions.append("pe.posting_date >= %(from_date)s")
        je_conditions.append("je.posting_date >= %(from_date)s")

    if filters.get("to_date"):
        pe_conditions.append("pe.posting_date <= %(to_date)s")
        je_conditions.append("je.posting_date <= %(to_date)s")

    if filters.get("cashier"):
        pe_conditions.append("pe.mode_of_payment = %(cashier)s")
        je_conditions.append("mop.name = %(cashier)s")

    pe_conditions_str = " AND ".join(pe_conditions)
    je_conditions_str = " AND ".join(je_conditions)

    # 🔹 outer filter for cashiers
    outer_conditions = []
    if filters.get("cashier"):
        outer_conditions.append("mop.name = %(cashier)s")
    outer_conditions_str = f"WHERE {' AND '.join(outer_conditions)}" if outer_conditions else ""

    sqlquery = frappe.db.sql(f"""
        SELECT
            mop.name AS mode_of_payment,
            COALESCE(pe_data.amount_received, 0) AS amount_received,
            COALESCE(pe_data.voucher_count, 0) AS voucher_count,
            COALESCE(pe_data.encashed_amount, 0) AS encashed_amount,
            COALESCE(je_data.amount_issued, 0) AS amount_issued,
            (COALESCE(je_data.amount_issued, 0) - COALESCE(pe_data.encashed_amount, 0)) AS cash_balance
        FROM `tabMode of Payment` mop
        -- Encashed Vouchers (Payment Entry)
        LEFT JOIN (
            SELECT
                pe.mode_of_payment,
                COALESCE(SUM(ge.debit), 0) AS amount_received,
                COUNT(DISTINCT pe.name) AS voucher_count,
                SUM(pe.paid_amount) AS encashed_amount
            FROM `tabPayment Entry` pe
            JOIN `tabGL Entry` ge 
                ON pe.name = ge.voucher_no 
                AND ge.voucher_type = 'Payment Entry'
                AND ge.account = pe.paid_from
                AND ge.is_cancelled = 0
            WHERE {pe_conditions_str}
            GROUP BY pe.mode_of_payment
        ) pe_data ON mop.name = pe_data.mode_of_payment

        -- Payments Issued by Cashier (Journal Entry)
        LEFT JOIN (
            SELECT
                mop.name AS mode_of_payment,
                SUM(jea.debit) - SUM(jea.credit) AS amount_issued
            FROM `tabJournal Entry Account` jea
            JOIN `tabJournal Entry` je
                ON jea.parent = je.name    
            JOIN `tabMode of Payment Account` mop_acc
                ON jea.account = mop_acc.default_account
            JOIN `tabMode of Payment` mop
                ON mop_acc.parent = mop.name
            WHERE {je_conditions_str}
            GROUP BY mop.name
        ) je_data ON mop.name = je_data.mode_of_payment
        {outer_conditions_str}
        ORDER BY mop.name;
    """, filters, as_dict=True)

    # recompute balance
    # for row in sqlquery:
    #     row.cash_balance = (row.amount_received or 0) - (row.encashed_amount or 0)

    return sqlquery
