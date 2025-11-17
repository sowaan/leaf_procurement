# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from frappe.model.naming import make_autoname # type: ignore
from erpnext.stock.doctype.batch.batch import get_batch_qty # type: ignore


class GoodsReceivingNote(Document):
    def autoname(self):
        """Override the default method to set a custom name."""
        if getattr(self, "skip_autoname", False):
            # print("Skipping autoname for CustomSupplier", self.servername)
            self.name = self.servername
            return  
        
        from datetime import datetime

        year = datetime.today().strftime('%Y') 
        
        # settings = frappe.get_doc("Leaf Procurement Settings")
        # self.location_short_code = frappe.db.get_value(
        #     "Warehouse",
        #     #settings.get("location_warehouse"),
        #     self.location_warehouse,
        #     "custom_short_code"
        # )
        prefix = f"{self.location_shortcode or 'SAM'}-GRN-{year}-"

        self.name = make_autoname(prefix + ".######")

    def on_submit(self):
        create_stock_entry_from_gtn(self)

        
def create_stock_entry_from_gtn(grn_doc):
    if not grn_doc.location_warehouse or not grn_doc.transit_location:
        frappe.throw("Dispatch and Receiving Warehouse must be set.")

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"
    stock_entry.company = grn_doc.company
    stock_entry.add_to_transit = False
    stock_entry.to_warehouse = grn_doc.location_warehouse
    # stock_entry.from_warehouse = grn_doc.transit_location
    stock_entry.custom_receiving_warehouse = grn_doc.dispatch_location

    stock_entry.purpose = "Material Transfer"
    stock_entry.custom_gtn_number = grn_doc.name  # custom field if needed

    bad_items = []
    # frappe.log_error("Starting Stock Entry creation",f"Creating Stock Entry for default item {grn_doc.default_item}")
    for row in grn_doc.detail_table:
        try:
            batch_info = get_batch_qty(batch_no=row.bale_barcode, item_code=grn_doc.default_item)
            if not batch_info:
                warehouse = grn_doc.transit_location
            else:
                info = batch_info[0]
                warehouse = info["warehouse"]

            # frappe.log_error("Error found",f"Error submitting Stock Entry for GRN {grn_doc.default_item}-{row.bale_barcode}: {batch_info}")
            # info = batch_info[0]
            # warehouse = info["warehouse"]         
            item = {
                "item_code": grn_doc.default_item,
                "qty": row.weight,
                "basic_rate": row.rate,
                "s_warehouse": warehouse,
                # "t_warehouse": gtn_doc.receiving_location,
                "use_serial_batch_fields": 1,
                "batch_no": row.bale_barcode,
                "lot_number": row.lot_number,
                "grade": row.item_grade,
                "sub_grade": row.item_sub_grade,            
                "to_lot_number": row.lot_number,
                "to_grade": row.item_grade,
                "to_sub_grade": row.item_sub_grade, 
                "reclassification_grade": row.reclassification_grade,     
                "doctype": "Stock Entry Detail",
                "parentfield": "items",
                "parenttype": "Stock Entry"
            }
            stock_entry.append("items", item)
        except Exception as e:
            frappe.log_error(f"Error processing bale {row.bale_barcode} in GRN {grn_doc.name}: {str(e)}")
            bad_items.append({
                "batch_no": row.bale_barcode,
                "reason": str(e),
                "item_code": grn_doc.default_item
            })
            continue  # Skip this item and move to next

    if bad_items:
        error_messages = []
        for bad in bad_items:
            msg = f"Batch No: {bad['batch_no']}, Reason: {bad['reason']}"
            error_messages.append(msg)
        full_error_message = "Errors encountered while creating Stock Entry:\n" + "\n".join(error_messages)
        frappe.throw(full_error_message)
        return  # Stop further processing if there are bad items
    
    try:
        stock_entry.flags.ignore_mandatory = True
        # ✅ Save as draft first — so ERPNext processes the valuation properly
        stock_entry.save(ignore_permissions=True)

        # ✅ Now reload (to simulate UI reload)
        stock_entry.reload()
        stock_entry.submit()
    except Exception as e:
        frappe.log_error(f"Error submitting Stock Entry for GRN {grn_doc.name}: {str(e)}")
        frappe.throw(f"Failed to submit Stock Entry for GRN {grn_doc.name}: {str(e)}")
