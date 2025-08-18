import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_report_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Invoice No", "fieldname": "invoice_no", "fieldtype": "Link", "options": "Purchase Invoice", "width": 150},
        {"label": "Invoice Date", "fieldname": "invoice_date", "fieldtype": "Date", "width": 120},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Batch No", "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 120},
        {"label": "Grade", "fieldname": "grade", "fieldtype": "Data", "width": 100},
        {"label": "Sub Grade", "fieldname": "sub_grade", "fieldtype": "Data", "width": 120},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 180},
        {"label": "Invoice Rate", "fieldname": "invoice_rate", "fieldtype": "Currency", "width": 120},
        {"label": "IGP Rate", "fieldname": "igp_rate", "fieldtype": "Currency", "width": 120},
    ]


def get_report_data(filters=None):
    conditions = ""
    if filters and filters.get("warehouse"):
        conditions += f" AND pii.warehouse = {frappe.db.escape(filters.get('warehouse'))}"

    query = f"""
            SELECT 
            pii.parent AS invoice_no,
            pi.posting_date AS invoice_date,
            pii.item_code,
            pii.batch_no,
            pii.grade,
            pii.sub_grade,
            pii.warehouse,
            pii.rate AS invoice_rate,
            igp.rate AS igp_rate
        FROM `tabPurchase Invoice Item` pii
        JOIN `tabPurchase Invoice` pi
        ON pi.name = pii.parent
        JOIN (
            SELECT 
                item, 
                item_grade, 
                item_sub_grade, 
                location_warehouse, 
                rate
            FROM `tabItem Grade Price`
            
        ) igp
        ON pii.item_code = igp.item
        AND pii.grade = igp.item_grade
        AND pii.sub_grade = igp.item_sub_grade
        AND igp.location_warehouse = CASE 
                WHEN pii.warehouse IN ('Buner-1 Depot','Buner-2 Depot','Mansehra Depot') 
                    THEN pii.warehouse
                ELSE 'Jamal Garhi-1 Depot'
            END
        WHERE pii.rate <> igp.rate
        {conditions}
        ORDER BY pii.warehouse, pi.posting_date, pii.parent, pii.item_code;

        """
    # query = f"""
    #     SELECT 
    #         pii.parent AS invoice_no,
    #         pi.posting_date AS invoice_date,
    #         pii.item_code,
    #         pii.batch_no,
    #         pii.grade,
    #         pii.sub_grade,
    #         pii.warehouse,
    #         pii.rate AS invoice_rate,
    #         igp.rate AS igp_rate
    #     FROM `tabPurchase Invoice Item` pii
    #     JOIN `tabPurchase Invoice` pi
    #       ON pi.name = pii.parent
    #     JOIN (
    #         SELECT 
    #             item, 
    #             item_grade, 
    #             item_sub_grade, 
    #             location_warehouse, 
    #             MAX(rate) AS rate
    #         FROM `tabItem Grade Price`
    #         GROUP BY item, item_grade, item_sub_grade, location_warehouse
    #     ) igp
    #       ON pii.item_code = igp.item
    #      AND pii.grade = igp.item_grade
    #      AND pii.sub_grade = igp.item_sub_grade
    #     WHERE pii.rate <> igp.rate
    #       AND pii.warehouse NOT IN ('Buner-1 Depot','Buner-2 Depot','Mansehra Depot')
    #       {conditions}
    #     ORDER BY pii.warehouse, pi.posting_date, pii.parent, pii.item_code
    # """

    return frappe.db.sql(query, as_dict=True)


@frappe.whitelist()
def correct_invoices(filters=None):
    """
    Runs stored procedure for all records matching current report filters
    and logs corrections with old/new rates
    """
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)

    records = get_report_data(filters)
    # Ensure sorted by invoice_no
    records.sort(key=lambda r: r.get("invoice_no"))

    last_invoice = None
    for r in records:
        old_rate = r.get("invoice_rate")
        new_rate = r.get("igp_rate")

        # Log item correction
        log = frappe.get_doc({
            "doctype": "Invoice Correction Log",
            "invoice_no": r.get("invoice_no"),
            "item_code": r.get("item_code"),
            "batch_no": r.get("batch_no"),
            "warehouse": r.get("warehouse"),
            "grade": r.get("grade"),
            "sub_grade": r.get("sub_grade"),
            "old_rate": old_rate,
            "new_rate": new_rate
        })
        log.insert(ignore_permissions=True)

        rate_location = "Jamal Garhi-1 Depot"  # Hardcoded warehouse for procedure call

        if r.get("warehouse") in ("Buner-1 Depot", "Buner-2 Depot", "Mansehra Depot"):
            rate_location = r.get("warehouse")

        # Call procedure only once per invoice
        if r.get("invoice_no") != last_invoice:
            frappe.db.sql("CALL fix_purchase_invoice_rates(%s, %s, %s)", (
                r.get("invoice_no"),
                rate_location,
                "TOBACCO"  # procedure handles all items anyway
            ))
            last_invoice = r.get("invoice_no")
        # frappe.db.commit()
        # return
    frappe.db.commit()
    return f"✅ Corrected {len(set([r.get('invoice_no') for r in records]))} invoices and logged {len(records)} items."

