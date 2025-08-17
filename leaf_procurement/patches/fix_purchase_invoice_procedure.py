import frappe # type: ignore

def execute():
    # Drop procedure if it exists
    frappe.db.sql("DROP PROCEDURE IF EXISTS fix_purchase_invoice_rates")

    # Now create procedure
    frappe.db.sql("""
    CREATE PROCEDURE fix_purchase_invoice_rates(
        IN in_invoice_no VARCHAR(255),
        IN in_warehouse VARCHAR(255),
        IN in_item_code VARCHAR(255)
    )
    BEGIN
        -- disable safe updates for bulk updates
        SET SQL_SAFE_UPDATES = 0;

        -- 1. Update Purchase Invoice Items
        UPDATE `tabPurchase Invoice Item` pii
        JOIN `tabItem Grade Price` igp 
          ON pii.item_code = igp.item
         AND pii.grade = igp.item_grade
         AND pii.sub_grade = igp.item_sub_grade
         AND igp.location_warehouse = in_warehouse
        SET pii.rate = igp.rate,
            pii.price_list_rate = igp.rate,
            pii.base_price_list_rate = igp.rate,
            pii.base_rate = igp.rate,
            pii.net_rate = igp.rate,
            pii.amount = pii.qty * igp.rate,
            pii.base_amount = pii.qty * igp.rate,
            pii.net_amount = pii.qty * igp.rate,
            pii.base_net_amount = pii.qty * igp.rate
        WHERE pii.parent = in_invoice_no
          AND pii.item_code = in_item_code;

        -- 2. Update Serial & Batch Entry rows
        UPDATE `tabSerial and Batch Entry` sbbe
        JOIN `tabSerial and Batch Bundle` sbb
          ON sbb.name = sbbe.parent
         AND sbb.voucher_type = 'Purchase Invoice'
         AND sbb.voucher_no = in_invoice_no
        JOIN `tabPurchase Invoice Item` pii
          ON pii.parent = sbb.voucher_no
         AND pii.item_code = sbb.item_code
         AND pii.batch_no = sbbe.batch_no
        SET sbbe.incoming_rate = pii.rate,
            sbbe.stock_value_difference = pii.rate * pii.qty;

        -- 3. Recompute Bundle parent totals
        UPDATE `tabSerial and Batch Bundle` sbb
        JOIN (
            SELECT parent,
                   SUM(qty * incoming_rate) AS total_amount,
                   SUM(qty) AS total_qty
            FROM `tabSerial and Batch Entry`
            GROUP BY parent
        ) x ON x.parent = sbb.name
        SET sbb.total_amount = x.total_amount,
            sbb.avg_rate = CASE WHEN x.total_qty = 0 THEN 0 ELSE x.total_amount / x.total_qty END
        WHERE sbb.voucher_type = 'Purchase Invoice'
          AND sbb.voucher_no = in_invoice_no;

        -- 4. Update Stock Ledger Entries
        UPDATE `tabStock Ledger Entry` sle
        JOIN `tabPurchase Invoice Item` pii
          ON sle.voucher_no = pii.parent
         AND sle.item_code = pii.item_code
         AND sle.item_grade = pii.grade
         AND sle.item_sub_grade = pii.sub_grade
        SET sle.incoming_rate = pii.rate,
            sle.valuation_rate = pii.rate,
            sle.stock_value = (sle.actual_qty * pii.rate),
            sle.stock_value_difference = (sle.actual_qty * pii.rate)
        WHERE sle.voucher_type = 'Purchase Invoice'
          AND sle.voucher_no = in_invoice_no
          AND sle.item_code = in_item_code;

        -- 5a. Update GL Entries (debit side)
        UPDATE `tabGL Entry`
        SET debit = (
                SELECT SUM(base_amount) 
                FROM `tabPurchase Invoice Item` 
                WHERE parent = in_invoice_no
            ),
            debit_in_account_currency = (
                SELECT SUM(base_amount) 
                FROM `tabPurchase Invoice Item` 
                WHERE parent = in_invoice_no
            ),
            debit_in_transaction_currency = (
                SELECT SUM(base_amount) 
                FROM `tabPurchase Invoice Item` 
                WHERE parent = in_invoice_no
            ),
            credit = 0,
            credit_in_account_currency = 0,
            credit_in_transaction_currency = 0
        WHERE voucher_type = 'Purchase Invoice'
          AND voucher_no = in_invoice_no
          AND debit > 0;

        -- 5b. Update GL Entries (credit side)
        UPDATE `tabGL Entry`
        SET credit = (
                SELECT SUM(base_amount) 
                FROM `tabPurchase Invoice Item` 
                WHERE parent = in_invoice_no
            ),
            credit_in_account_currency = (
                SELECT SUM(base_amount) 
                FROM `tabPurchase Invoice Item` 
                WHERE parent = in_invoice_no
            ),
            credit_in_transaction_currency = (
                SELECT SUM(base_amount) 
                FROM `tabPurchase Invoice Item` 
                WHERE parent = in_invoice_no
            ),
            debit = 0,
            debit_in_account_currency = 0,
            debit_in_transaction_currency = 0
        WHERE voucher_type = 'Purchase Invoice'
          AND voucher_no = in_invoice_no
          AND credit > 0;

        -- re-enable safe updates
        SET SQL_SAFE_UPDATES = 1;
    END
    """)
