import frappe # type: ignore
from frappe.model.document import Document # type: ignore

@frappe.whitelist()
def reconcile_stock():
    reconcile_grns()

def reconcile_grns():
    grns = frappe.get_all("Goods Receiving Note", filters={"reconciled": 0}, fields=["name", "gtn_number"])
    
    for grn in grns:
        grn_doc = frappe.get_doc("Goods Receiving Note", grn.name)
        
        # Create Stock Entry
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Receipt"
        stock_entry.purpose = "Material Receipt"
        stock_entry.company = grn_doc.company
        stock_entry.to_warehouse = grn_doc.location_warehouse
        stock_entry.reference_no = grn.name
        stock_entry.set_posting_time = 1 
        stock_entry.custom_gtn_number = grn_doc.name  # cu
    
        for row in grn_doc.detail_table:  # Assuming the child table is named 'bale_details'
            gtn_detail = frappe.get_value("Goods Transfer Detail", {
                "parent": grn.gtn_number,
                "barcode": row.bale_barcode
            }, ["grade", "sub_grade", "price", "weight", "item_code", "target_warehouse"])
            
            if gtn_detail:
            #     grade, sub_grade, price, weight, item_code, warehouse = gtn_detail

            #     stock_entry.append("items", {
            #         "item_code": item_code,
            #         "qty": weight,
            #         "basic_rate": price,
            #         "amount": weight * price,
            #         "t_warehouse": warehouse,
            #     "use_serial_batch_fields": 1,
            #     "batch_no": row.bale_barcode,
            #     "description": f"Bale Barcode: {row.bale_barcode}",
            #     "lot_number": registration_code,
            #     "grade": detail.item_grade,
            #     "sub_grade": detail.item_sub_grade,                    
            #     })

                stock_entry.insert()
                stock_entry.submit()

        # Mark GRN as reconciled
        grn_doc.reconciled = 1
        grn_doc.save()
        frappe.db.commit()