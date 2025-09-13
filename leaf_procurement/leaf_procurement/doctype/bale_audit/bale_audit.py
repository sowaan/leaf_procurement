# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore
from frappe.model.document import Document # type: ignore
from datetime import datetime
from frappe import _, ValidationError 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore
from leaf_procurement.leaf_procurement.api.bale_audit_utils import get_gtn_datails_for_bale  # type: ignore
# from frappe.utils import today, add_days

# bale_audit.py


# def get_permission_query_conditions(user=None):
#     if not user:
#         return ""

#     from frappe.utils import today, add_days
#     two_days_ago = add_days(today(), -2)
#     return f"""(`tabBale Audit`.`date` BETWEEN '{two_days_ago}' AND '{today()}')"""


class BaleAudit(Document):
    def before_save(self):
        # If any bale barcode is changed/added, fetch GTN details
        for row in self.get("detail_table", []):
            if row.bale_barcode and not row.gtn_number:
                gtn_details = get_gtn_datails_for_bale(row.bale_barcode)
                row.gtn_number = gtn_details.get("gtn_name")
                row.tsa_number = gtn_details.get("tsa_number")
                row.truck_number = gtn_details.get("vehicle_number")
                row.advance_weight = gtn_details.get("weight")
                # Store fetched barcode to detect changes later
                if row.advance_weight and row.weight:
                    try:
                        row.difference = round(
                            float(row.weight) - float(row.advance_weight), 2
                        )
                    except Exception:
                        row.difference = None
                else:
                    row.difference = None



    def autoname(self):
        # If explicitly set from sync (servername)
        if getattr(self, "skip_autoname", False) :
            self.name = self.servername
            # self._update_series_from_name()
            return
        
        if not self.location_shortcode:
            frappe.throw(_("Location Shortcode is required to generate name"))

        # Ensure self.date exists
        if not self.date:
            frappe.throw("Date is required for generating name")

        # Check live flag from settings
        live_server = frappe.db.get_single_value("Leaf Procurement Settings", "live_server")

        # Format date
        doc_date = datetime.strptime(str(self.date), "%Y-%m-%d")
        date_part = doc_date.strftime("%Y%m%d")

        # Build prefix
        prefix = f"{self.location_shortcode}-AUD-{date_part}-"

        # Add LIVE- if this is from live server
        if live_server:
            prefix = "LV-" + prefix
        else:
            prefix = "" + prefix

        # Normal autoname
        self.name = make_autoname(prefix + ".######")
        # self._update_series_from_name()

    # def _update_series_from_name(self):
    #     """Ensure tabSeries counter is >= last number in the name."""
    #     try:
    #         parts = self.name.split("-")
    #         last_number = int(parts[-1]) if parts[-1].isdigit() else None
    #         if not last_number:
    #             return

    #         prefix = "-".join(parts[:-1]) + "-"
    #         frappe.db.sql("""
    #             INSERT INTO tabSeries (name, current) VALUES (%s, %s)
    #             ON DUPLICATE KEY UPDATE current = GREATEST(current, VALUES(current))
    #         """, (prefix, last_number))
    #     except Exception as e:
    #         frappe.log_error(f"Series update failed for {self.name}: {str(e)}", "BaleAudit Autoname")

    def on_submit(self):
        # if check validations is false, no need to check validations
        # as this is a sync operation

        if not self.check_validations:
            return
        
        day_open = frappe.get_all("Audit Day Setup",
            filters={
                "location_warehouse": self.location_warehouse,
                "date": self.date,
                "day_open_time": ["is", "set"],
                "day_close_time": ["is", "not set"]
            },
            fields=["name"]
        )

        if not day_open:
            frappe.throw(_("⚠️ Audit not permitted because the day is either not opened or already closed for location: " + self.location_warehouse))
        
        invalid_barcodes = []
        # ✅ validate barcodes in detail table
        for row in self.get("detail_table", []):
            if row.bale_barcode and not row.bale_barcode.isdigit():
                invalid_barcodes.append(f"Row {row.idx}: {row.bale_barcode}")
        
        if invalid_barcodes:
            error_message = _("The following Bale Barcodes are invalid (only digits allowed):") + "<br><br>"
            error_message += "<br>".join(invalid_barcodes)
            frappe.throw(error_message)
   #def validate(self):
        # if not self.detail_table or len(self.detail_table) == 0:
        #     frappe.throw(_("Please add at least one row in the Bale Audit Detail table."))