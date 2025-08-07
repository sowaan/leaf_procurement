import frappe # type: ignore

def execute():
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
    """)
    frappe.logger().info(f"{affected} rows updated in Bale Audit Detail via GTN patch")
