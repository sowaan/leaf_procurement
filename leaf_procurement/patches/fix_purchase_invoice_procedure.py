import frappe # type: ignore

def execute():
    # Drop procedure if it exists
    frappe.db.sql("DROP PROCEDURE IF EXISTS fix_purchase_invoice_rates")

    # CALL fix_purchase_invoice_rates('TDP-2025-ACC-PINV-00003', 'Jamal Garhi-1 Depot', 'TOBACCO');

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
      JOIN (
          SELECT item, item_grade, item_sub_grade, location_warehouse, MAX(rate) AS rate
          FROM `tabItem Grade Price`
                  where location_warehouse = in_warehouse
          GROUP BY item, item_grade, item_sub_grade, location_warehouse
      ) igp
        ON pii.item_code = igp.item
      AND pii.grade = igp.item_grade
      AND pii.sub_grade = igp.item_sub_grade
      SET pii.rate = igp.rate,
          pii.price_list_rate = igp.rate,
          pii.base_price_list_rate = igp.rate,
          pii.base_rate = igp.rate,
          pii.net_rate = igp.rate,
          pii.amount = pii.qty * igp.rate,
          pii.base_amount = pii.qty * igp.rate,
          pii.net_amount = pii.qty * igp.rate,
          pii.base_net_amount = pii.qty * igp.rate
      WHERE pii.parent = in_invoice_no;

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

        SET @net_total = 0;
        SET @base_total = 0;

        -- Get totals from items
        SELECT 
            SUM(base_amount), 
            SUM(net_amount)
        INTO @base_total, @net_total
        FROM `tabPurchase Invoice Item`
        WHERE parent = in_invoice_no;

        -- Round values
        SET @rounded_total = ROUND(@net_total, 0);
        SET @rounding_adj = @rounded_total - @net_total;

        -- 5. Delete old Round Off GL entries as they will be recreated
        DELETE FROM `tabGL Entry`
        WHERE voucher_type = 'Purchase Invoice'
          AND voucher_no = in_invoice_no
          AND account = '5212 - Round Off - SG';
                                                      
        -- 5a. Update GL Entries (debit side)
        UPDATE `tabGL Entry`
        SET debit = @net_total, credit = 0
        WHERE voucher_type = 'Purchase Invoice'
          AND voucher_no = in_invoice_no
          AND account = '1410 - Stock In Hand - SG';

        -- 5b. Update GL Entries (credit side)
        UPDATE `tabGL Entry`
        SET credit = @rounded_total, debit = 0
        WHERE voucher_type = 'Purchase Invoice'
          AND voucher_no = in_invoice_no
          AND account = '2110 - Creditors - SG';

        -- 5c. Insert new Round Off GL entry

        -- Insert Round Off Entry if needed
        IF @rounding_adj <> 0 THEN
            INSERT INTO `tabGL Entry` (
                name, creation, modified, modified_by, owner,
                docstatus, parent, parentfield, parenttype,
                account, debit, credit, voucher_type, voucher_no, company
            ) VALUES (
                UUID(), NOW(), NOW(), 'Administrator', 'Administrator',
                1, NULL, NULL, NULL,
                '5212 - Round Off - SG',
                CASE WHEN @rounding_adj > 0 THEN @rounding_adj ELSE 0 END,
                CASE WHEN @rounding_adj < 0 THEN ABS(@rounding_adj) ELSE 0 END,
                'Purchase Invoice', in_invoice_no, 'Samsons Group'
            );
        END IF;                  

        -- 6. Update Purchase Invoice header totals
        UPDATE `tabPurchase Invoice`
        SET total = @net_total,
            base_total = @base_total,
            net_total = @net_total,
            base_net_total = @base_total,
            grand_total = @net_total,
            rounded_total = @rounded_total,
            base_grand_total = @base_total,
            rounding_adjustment = @rounding_adj,
            outstanding_amount = @rounded_total - paid_amount
        WHERE name = in_invoice_no;

        -- re-enable safe updates
        SET SQL_SAFE_UPDATES = 1;
    END
    """)
