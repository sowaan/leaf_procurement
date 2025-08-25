import frappe

def execute(filters=None):
    columns = [
        # {"label": "Voucher Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
        {"label": "Voucher", "fieldname": "voucher_no", "fieldtype": "Link", "options": "Purchase Invoice", "width": 230},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 80},
        {"label": "Grower", "fieldname": "supplier_id", "fieldtype": "Link", "options": "Supplier", "width": 180},
        {"label": "Supplier Name", "fieldname": "supplier_name", "fieldtype": "Data", "width": 120},
        {"label": "NIC Number", "fieldname": "custom_nic_number", "fieldtype": "Data", "width": 100},
        {"label": "Mobile No", "fieldname": "mobile_no", "fieldtype": "Data", "width": 100},
        {"label": "Leaf Buying Depot", "fieldname": "leaf_buying_depot", "fieldtype": "Link", "options": "Warehouse", "width": 180},
        {"label": "Net Total", "fieldname": "net_total", "fieldtype": "Currency", "width": 120},
        {"label": "Total Quantity", "fieldname": "total_qty", "fieldtype": "Float", "width": 100},
        {"label": "Outstanding Amount", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 120},
        # {"label": "Payment Entry", "fieldname": "payment_entry", "fieldtype": "Link", "options": "Payment Entry", "width": 150},
        {"label": "Payment Date", "fieldname": "payment_date", "fieldtype": "Date", "width": 100},
        # {"label": "Invoice Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]

    filters = frappe._dict(filters or {})

    conditions = "WHERE pi.docstatus = 1"
    values = {}

    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s"
        values.update({"from_date": filters.from_date, "to_date": filters.to_date})

    if filters.get("supplier"):
        conditions += " AND pi.supplier = %(supplier)s"
        values["supplier"] = filters.supplier

    if filters.get("warehouse"):
        conditions += " AND sup.custom_location_warehouse = %(warehouse)s"
        values["warehouse"] = filters.warehouse

    # if filters.get("status"):
    #     conditions += " AND pi.status = %(status)s"
    #     values["status"] = filters.status

    query = f"""
SELECT 
    'Purchase Invoice' AS voucher_type,
    pi.name AS voucher_no,
    pi.posting_date,
    pi.supplier AS supplier_id,
    sup.custom_nic_number,
    sup.mobile_no,
    sup.custom_location_warehouse AS leaf_buying_depot,
    pi.supplier_name,
    pi.net_total,
    pi.total_qty,
    pi.outstanding_amount,
    pi.status,
    latest.latest_payment_date AS payment_date
FROM `tabPurchase Invoice` pi
LEFT JOIN `tabSupplier` sup 
    ON sup.name = pi.supplier
LEFT JOIN (
    SELECT 
        per.reference_name,
        MAX(pe.posting_date) AS latest_payment_date
    FROM `tabPayment Entry Reference` per
    INNER JOIN `tabPayment Entry` pe 
        ON pe.name = per.parent
        AND pe.docstatus = 1
    WHERE per.reference_doctype = 'Purchase Invoice'
    GROUP BY per.reference_name
) AS latest 
    ON latest.reference_name = pi.name
{conditions}
ORDER BY pi.posting_date DESC


    """

    data = frappe.db.sql(query, values, as_dict=True)
    return columns, data
