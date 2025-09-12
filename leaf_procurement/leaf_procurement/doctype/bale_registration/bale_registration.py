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
        if getattr(self, "skip_autoname", False):
            self.name = self.servername
            return
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
        self.bale_status = "In Buying"
        frappe.db.set_value(self.doctype, self.name, "bale_status", "In Buying")

    def validate(self):
        #NOTE: change this to ValidateYearlyQuota after the current fiscal year is closed.
        validate(self)

# TODO: this function needs to be disabled after the current fiscal year is closed.
# Reason: It checks the total weight against the supplier's quota for the current fiscal year.
def validate(doc, method=None):
    if not doc.supplier_grower:
        return

    # Step 1: Get Supplier Quota
    quota = frappe.db.get_value("Supplier", doc.supplier_grower, "custom_quota_allowed") or 0

    # Step 2: Get Total Weight of All Bale Weight Detail Entries for this supplier
    total_weight = frappe.db.sql("""
        SELECT SUM(d.weight)
        FROM `tabBale Weight Detail` d
        JOIN `tabBale Weight Info` i ON d.parent = i.name
        WHERE i.supplier_grower = %s AND i.docstatus = 1
    """, (doc.supplier_grower,), as_list=True)[0][0] or 0

    if total_weight > quota:
        frappe.throw(_(
            "Total weight for supplier '{0}' exceeds allowed quota.\nQuota: {1}, Current Total: {2}"
        ).format(doc.supplier_grower, quota, total_weight))

# TODO: Enable this code after the current fiscal year is closed.
# NOTE: This enforces supplier quota checks across fiscal years.
# Status: Tested and working.
# Reason for delay: Prevents disruption before year-end; only required when 
# users start registering bales for the same supplier in the next fiscal year.
def validateYearlyQuota(doc, method=None):
    if not doc.supplier_grower or not doc.date:
        return

    # Step 1: Find fiscal year for this doc.date
    fiscal_year = frappe.db.sql("""
        SELECT year_start_date, year_end_date
        FROM `tabFiscal Year`
        WHERE %s BETWEEN year_start_date AND year_end_date
          AND disabled = 0
        ORDER BY year_start_date DESC
        LIMIT 1
    """, (doc.date,), as_dict=True)

    if not fiscal_year:
        frappe.throw(_("No active Fiscal Year found for date {0}").format(doc.date))

    year_start = fiscal_year[0].year_start_date
    year_end = fiscal_year[0].year_end_date

    # Step 2: Get Supplier Quota
    quota = frappe.db.get_value("Supplier", doc.supplier_grower, "custom_quota_allowed") or 0

    # Step 3: Get Total Weight in this fiscal year
    total_weight = frappe.db.sql("""
        SELECT SUM(d.weight)
        FROM `tabBale Weight Detail` d
        JOIN `tabBale Weight Info` i ON d.parent = i.name
        WHERE i.supplier_grower = %s
          AND i.docstatus = 1
          AND i.date BETWEEN %s AND %s
    """, (doc.supplier_grower, year_start, year_end), as_list=True)[0][0] or 0

    # Step 4: Compare quota
    if total_weight > quota:
        frappe.throw(_(
            "Total weight for supplier '{0}' in Fiscal Year {1} - {2} exceeds allowed quota.\nQuota: {3}, Current Total: {4}"
        ).format(doc.supplier_grower, year_start, year_end, quota, total_weight))
