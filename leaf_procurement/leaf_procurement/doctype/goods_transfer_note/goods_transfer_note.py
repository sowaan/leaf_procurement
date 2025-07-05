# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import uuid
import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from frappe import _ # type: ignore
from frappe.model.naming import make_autoname # type: ignore

class GoodsTransferNote(Document):
    def autoname(self):
        """Override the default method to set a custom name."""
        if getattr(self, "skip_autoname", False):
            # print("Skipping autoname for CustomSupplier", self.servername)
            self.name = self.servername
            return  
        
        from datetime import datetime

        year = datetime.today().strftime('%Y') 
        
        settings = frappe.get_doc("Leaf Procurement Settings")
        self.location_short_code = frappe.db.get_value(
            "Warehouse",
            settings.get("location_warehouse"),
            "custom_short_code"
        )
        
        prefix = f"{self.location_short_code}-GTN-{year}-"

        self.name = make_autoname(prefix + ".######")

    def before_insert(doc):
        if not doc.custom_sync_id:
            doc.custom_sync_id = str(uuid.uuid4())    
            
    def before_save(self):
        self.gtn_barcode = f"{self.name}"       

    def on_submit(self):

        create_stock_entry_from_gtn(self)
    # def on_update(self):
    #     create_stock_entry_from_gtn(self)

    def validate(self):
        check_bale_already_exists(self)
        ensure_unique_tsa_per_warehouse(self)

def check_bale_already_exists(doc):
    duplicate_barcodes = []

    for item in doc.bale_registration_detail:
        exists = frappe.db.exists(
            "Goods Transfer Note Items",
            {
                "bale_barcode": item.bale_barcode,
                "parent": ["!=", doc.name]
            }
        )

        if exists:
            # Check if parent GTN is submitted
            parent_status = frappe.db.get_value("Goods Transfer Note", exists, "docstatus")

            duplicate_barcodes.append(item.bale_barcode)
            

    if duplicate_barcodes:
        frappe.throw(
            _("The following bale barcodes already exist in submitted Goods Transfer Notes:\n{0}").format(
                ", ".join(duplicate_barcodes)
            ),
            title=_("Duplicate TSA Number")
        )
def ensure_unique_tsa_per_warehouse(self):
    if not self.tsa_number or not self.location_warehouse:
        return

    duplicate = frappe.db.exists(
        "Goods Transfer Note",
        {
            "tsa_number": self.tsa_number,
            "location_warehouse": self.location_warehouse,
            "name": ["!=", self.name]
        }
    )

    if duplicate:
        frappe.throw(
            _("TSA Number <b>{0}</b> is already used in warehouse <b>{1}</b>. TSA Number must be unique per warehouse.").format(
                self.tsa_number, self.location_warehouse
            ),
            title=_("Duplicate TSA Number")
        )

def create_stock_entry_from_gtn(gtn_doc):
    if not gtn_doc.location_warehouse or not gtn_doc.receiving_location:
        frappe.throw("Dispatch and Receiving Warehouse must be set.")

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"
    stock_entry.company = gtn_doc.company
    stock_entry.add_to_transit = True
    stock_entry.from_warehouse = gtn_doc.location_warehouse
    stock_entry.to_warehouse = gtn_doc.transit_location
    stock_entry.custom_receiving_warehouse = gtn_doc.receiving_location
    
    stock_entry.posting_date = gtn_doc.date 
    stock_entry.posting_time = "23:55:00"
    stock_entry.purpose = "Material Transfer"
    stock_entry.custom_gtn_number = gtn_doc.name  # custom field if needed
    stock_entry.set_posting_time = 1
    stock_entry.skip_future_date_validation = True


    for row in gtn_doc.bale_registration_detail:

        stock_entry.append("items", {
            "item_code": gtn_doc.default_item,
            "qty": row.weight,
            "basic_rate": row.rate,
            # "s_warehouse": gtn_doc.location_warehouse,
            # "t_warehouse": gtn_doc.receiving_location,
            "use_serial_batch_fields": 1,
            "batch_no": row.bale_barcode,
			"lot_number": row.lot_number,
			"grade": row.item_grade,
			"sub_grade": row.item_sub_grade,            
			"to_lot_number": row.lot_number,
			"to_grade": row.item_grade,
			"to_sub_grade": row.item_sub_grade,   
		})

    stock_entry.insert()
    stock_entry.submit()


