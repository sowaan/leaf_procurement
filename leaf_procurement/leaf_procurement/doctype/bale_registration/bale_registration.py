# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe 	#type: ignore
from frappe.model.document import Document 	#type: ignore
from frappe import _, ValidationError 	#type: ignore
from frappe.model.naming import make_autoname # type: ignore
from frappe.utils import flt, nowdate # type: ignore
from erpnext.accounts.utils import get_fiscal_year # type: ignore
from datetime import datetime



class BaleRegistration(Document):
    def autoname(self):
        today = datetime.strptime(self.date, "%Y-%m-%d")
        date_part = today.strftime("%d%m%Y")
        current_year_short = today.strftime("%y")
        fy = get_fiscal_year(today)
        fy_start_year_short = fy[1].strftime("%y")
        fy_end_year_short = fy[2].strftime("%y")
        prefix = f"{self.location_short_code}-{date_part}-{fy_start_year_short}-{fy_end_year_short}-"
        self.name = make_autoname(prefix + ".######")
          
    def on_submit(self):
        # if check validations is false, no need to check validations
        # as this is a sync operation
        if not self.check_validations:
            return
	
        
        day_open = frappe.get_all("Day Setup",
            filters={
                "date": self.date,
                "day_open_time": ["is", "set"],
                "day_close_time": ["is", "not set"]
            },
            fields=["name"]
        )

        if not day_open:
            frappe.throw(_("⚠️ You cannot register bales because the day is either not opened or already closed."))

        expected_count = self.lot_size
        entered_count = len(self.bale_registration_detail or [])
        if flt(entered_count) > flt(expected_count):
            frappe.msgprint(
                msg=_("⚠️ The number of bales entered is <b>{0}</b>, but the maximum number of bales allowed in a lot is <b>{1}</b> for Bale Registration.".format(
                    entered_count, expected_count
                )),
                title=_("Mismatch in Bale Count"),
                indicator='orange'
            )
            raise ValidationError
        
        invalid_barcodes = []

        for row in self.bale_registration_detail:
            if not row.bale_barcode.isdigit() or len(row.bale_barcode) != flt(self.barcode_length):
                invalid_barcodes.append(row.bale_barcode)

        invalid_barcodes_list = "<br>".join(invalid_barcodes)

        if invalid_barcodes:
            frappe.msgprint(
                msg=_("⚠️ The following barcodes are invalid (must be <b>{0}</b> digits and only numeric values are allowed for barcode).<br><br>{1}".format(
                    self.barcode_length, invalid_barcodes_list
                )),
                title=_("Incorrect Barcodes Found"),
                indicator='orange'
            )
            raise ValidationError
        
        