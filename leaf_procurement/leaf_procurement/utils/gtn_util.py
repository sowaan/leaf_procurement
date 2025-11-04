import frappe # type: ignore
from frappe import _ # type: ignore

BATCH_SIZE = 5000

@frappe.whitelist()
def update_all_reclassification_grades():
    """
    MAIN FUNCTION:
    1. Update Stock Entry Detail (SED) from GTN → GTN Items
    2. Update Stock Entry Detail (SED) from GRN → GTN Items
    3. Update Stock Ledger Entry (SLE) from updated SED via Serial & Batch Bundle
    Safely processes in batches of 5000 with commits to avoid locking.
    """

    frappe.logger().info("🚀 Starting FULL reclassification update (GTN + GRN → SED → SLE)...")

    # 1. Update SED from GTN
    sed_gtn = _update_sed_from_gtn()

    # 2. Update SED from GRN
    sed_grn = _update_sed_from_grn()

    # 3. Update SLE from SED
    sle_updated = _update_sle_from_sed()

    frappe.db.commit()

    return {
        "status": "success",
        "sed_updated_from_gtn": sed_gtn,
        "sed_updated_from_grn": sed_grn,
        "sle_updated": sle_updated
    }


# -------------------------------------------------------------------------
# 1) Update SED from GTN
# -------------------------------------------------------------------------
def _update_sed_from_gtn():

    total = 0
    offset = 0

    while True:
        rows = frappe.db.sql("""
            SELECT sed.name AS sed_name,
                   gtni.reclassification_grade AS new_grade
            FROM `tabStock Entry Detail` sed
            INNER JOIN `tabStock Entry` se ON se.name = sed.parent
            INNER JOIN `tabGoods Transfer Note` gtn ON gtn.name = se.custom_gtn_number
            INNER JOIN `tabGoods Transfer Note Items` gtni
                ON gtni.parent = gtn.name
               AND gtni.bale_barcode = sed.batch_no
            WHERE sed.reclassification_grade IS NULL
            LIMIT %s OFFSET %s
        """, (BATCH_SIZE, offset), as_dict=True)

        if not rows:
            break

        frappe.logger().info(f"Updating SED (GTN) batch offset {offset}, count {len(rows)}")

        for r in rows:
            frappe.db.set_value(
                "Stock Entry Detail",
                r.sed_name,
                "reclassification_grade",
                r.new_grade,
                update_modified=False
            )
            total += 1

        frappe.db.commit()
        offset += BATCH_SIZE

    frappe.logger().info(f"✅ Completed SED updates from GTN: {total}")
    return total


# -------------------------------------------------------------------------
# 2) Update SED from GRN
# -------------------------------------------------------------------------
def _update_sed_from_grn():

    total = 0
    offset = 0

    while True:
        rows = frappe.db.sql("""
            SELECT sed.name AS sed_name,
                   gtni.reclassification_grade AS new_grade
            FROM `tabStock Entry Detail` sed
            INNER JOIN `tabStock Entry` se ON se.name = sed.parent
            INNER JOIN `tabGoods Receiving Note` grn ON grn.name = se.custom_gtn_number
            INNER JOIN `tabGoods Transfer Note Items` gtni
                ON gtni.parent = grn.name
               AND gtni.bale_barcode = sed.batch_no
            WHERE sed.reclassification_grade IS NULL
            LIMIT %s OFFSET %s
        """, (BATCH_SIZE, offset), as_dict=True)

        if not rows:
            break

        frappe.logger().info(f"Updating SED (GRN) batch offset {offset}, count {len(rows)}")

        for r in rows:
            frappe.db.set_value(
                "Stock Entry Detail",
                r.sed_name,
                "reclassification_grade",
                r.new_grade,
                update_modified=False
            )
            total += 1

        frappe.db.commit()
        offset += BATCH_SIZE

    frappe.logger().info(f"✅ Completed SED updates from GRN: {total}")
    return total


# -------------------------------------------------------------------------
# 3) Update SLE from updated SED (batch)
# -------------------------------------------------------------------------
def _update_sle_from_sed():

    total = 0
    offset = 0

    while True:
        rows = frappe.db.sql("""
            SELECT sle.name AS sle_name,
                   sed.reclassification_grade AS new_grade
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabSerial and Batch Entry` sbbe
                ON sbbe.parent = sle.serial_and_batch_bundle
            INNER JOIN `tabStock Entry Detail` sed
                ON sed.parent = sle.voucher_no
               AND sed.batch_no = sbbe.batch_no
            WHERE sle.voucher_type = 'Stock Entry'
              AND sbbe.batch_no IS NOT NULL
              AND (sle.reclassification_grade IS NULL
                   OR sle.reclassification_grade != sed.reclassification_grade)
            LIMIT %s OFFSET %s
        """, (BATCH_SIZE, offset), as_dict=True)

        if not rows:
            break

        frappe.logger().info(f"Updating SLE batch offset {offset}, count {len(rows)}")

        for r in rows:
            frappe.db.set_value(
                "Stock Ledger Entry",
                r.sle_name,
                "reclassification_grade",
                r.new_grade,
                update_modified=False
            )
            total += 1

        frappe.db.commit()
        offset += BATCH_SIZE

    frappe.logger().info(f"✅ Completed SLE updates: {total}")
    return total


@frappe.whitelist()
def force_submit_gtn(gtn_name, skip_stock_entry=True):

    if frappe.session.user != "Administrator":
        frappe.throw(_("Only Administrator is allowed to perform this operation."))

    try:
        
        gtn_doc = frappe.get_doc("Goods Transfer Note", gtn_name)

        if gtn_doc.docstatus == 1:
            return f"GTN {gtn_name} is already submitted."

        # Temporarily disable link validation
        frappe.flags.ignore_links = True
        frappe.flags.ignore_validate_update_after_submit = True

        # Bypass standard validation
        gtn_doc.flags.ignore_validate = True
        gtn_doc.flags.ignore_validate_update_after_submit = True
        gtn_doc.flags.ignore_links = True
        gtn_doc.flags.ignore_permissions = True
        gtn_doc.skip_stock_entry = skip_stock_entry
        # Submit document
        gtn_doc.submit()
        frappe.db.commit()

        frappe.flags.ignore_links = False
        frappe.msgprint(f"✅ Successfully submitted GTN: {gtn_name}")
        return f"Successfully submitted GTN: {gtn_name}"

    except Exception as e:
        frappe.log_error(title="Force Submit GTN Failed", message=frappe.get_traceback())
        frappe.throw(f"❌ Failed to submit GTN {gtn_name}: {str(e)}")