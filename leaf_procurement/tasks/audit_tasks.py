import frappe # type: ignore

@frappe.whitelist()
def update_bale_audit_detail():
    
    try:
        batch_size=5000
        affected = frappe.db.sql("""
            UPDATE `tabBale Audit Detail` AS bad
            JOIN `tabGoods Transfer Note Items` AS gtni
                ON bad.bale_barcode = gtni.bale_barcode
            JOIN `tabGoods Transfer Note` AS gtn
                ON gtni.parent = gtn.name
            SET 
                bad.gtn_number = gtn.name,
                bad.truck_number = gtn.vehicle_number,
                bad.tsa_number = gtn.tsa_number,
                bad.advance_weight = gtni.weight
            WHERE 
                bad.gtn_number IS NULL
                AND bad.bale_barcode IS NOT NULL
            LIMIT %s
        """, (batch_size,))

        frappe.db.commit()
        frappe.logger().info(f"Updated {affected} Bale Audit Detail rows via GTN patch")

        frappe.log_error("Updated Bale Audit Detail", f"Updated {affected} Bale Audit Detail rows via GTN patch")


    except Exception as e:
        frappe.logger().error(f"Error updating Bale Audit Detail: {e}")


@frappe.whitelist()
def update_gtn_with_bale_audit():
    try:
        batch_size=5000
        affected =frappe.db.sql("""
            UPDATE `tabGoods Transfer Note Items` AS gtni
            JOIN `tabBale Audit Detail` AS bad
                ON gtni.bale_barcode = bad.bale_barcode
            SET 
                gtni.audit_weight = bad.weight,
                gtni.audit_remarks = bad.bale_remarks
            WHERE 
                gtni.audit_weight IS NULL
                AND gtni.bale_barcode IS NOT NULL
            LIMIT %s
        """, (batch_size,))

        frappe.db.commit()
        # print(f"⚡ {affected} rows updated in Bale Audit Detail via Bale patch")
        frappe.logger().info(f"Updated {affected} GTN Items via Bale Audit patch")
        frappe.log_error("Updated GTN Detail", f"Updated {affected} Bale Audit Detail rows via GTN patch")


    except Exception as e:
        frappe.logger().error(f"Error updating Bale Audit Detail: {e}")
