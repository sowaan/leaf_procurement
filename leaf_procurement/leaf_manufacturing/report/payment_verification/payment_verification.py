# Copyright (c) 2026, Sowaan and contributors
# For license information, please see license.txt

import frappe # type: ignore


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Grower Name", "fieldname": "grower_name", "fieldtype": "Data", "width": 160},
		{"label": "Father Name", "fieldname": "father_name", "fieldtype": "Data", "width": 140},
		{"label": "CNIC", "fieldname": "cnic", "fieldtype": "Data", "width": 140},
		{"label": "Payment Entry ID", "fieldname": "payment_entry_id", "fieldtype": "Link", "options": "Payment Entry", "width": 170},
		{"label": "Voucher No", "fieldname": "voucher_no", "fieldtype": "Data", "width": 160},
		{"label": "Purchase Date", "fieldname": "purchase_date", "fieldtype": "Date", "width": 120},
		{"label": "Due Date", "fieldname": "due_date", "fieldtype": "Date", "width": 120},
		{"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 140},
		{"label": "Weight (Kgs)", "fieldname": "weight", "fieldtype": "Float", "width": 130, "precision": 3},
		{"label": "Payment Date", "fieldname": "payment_date", "fieldtype": "Date", "width": 120},
		{"label": "Amount Paid", "fieldname": "amount_paid", "fieldtype": "Currency", "width": 140},
	]


def get_conditions(filters):
	conditions = ["pi.docstatus = 1", "pe.docstatus = 1", "pe.party_type = 'Supplier'"]
	params = {}

	if filters.get("from_date"):
		conditions.append("pe.posting_date >= %(from_date)s")
		params["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("pe.posting_date <= %(to_date)s")
		params["to_date"] = filters.to_date

	if filters.get("warehouse"):
		conditions.append(
			"""EXISTS (
				SELECT 1 FROM `tabPurchase Invoice Item` pii_f
				WHERE pii_f.parent = pi.name
				AND COALESCE(NULLIF(pii_f.warehouse, ''), NULLIF(pi.set_warehouse, '')) = %(warehouse)s
			)"""
		)
		params["warehouse"] = filters.warehouse

	if filters.get("depot"):
		conditions.append("supp.custom_location_warehouse = %(depot)s")
		params["depot"] = filters.depot

	if filters.get("season"):
		conditions.append(
			"""EXISTS (
				SELECT 1 FROM `tabPurchase Invoice Item` pii_s
				WHERE pii_s.parent = pi.name
				AND (IFNULL(pii_s.lot_number, '') LIKE %(season)s OR IFNULL(pii_s.from_lot_number, '') LIKE %(season)s)
			)"""
		)
		params["season"] = f"%{filters.season.strip()}%"

	return " AND ".join(conditions), params


def get_data(filters):
	conditions, params = get_conditions(filters)

	data = frappe.db.sql(
		f"""
		SELECT
			supp.supplier_name AS grower_name,
			supp.custom_father_name AS father_name,
			supp.custom_nic_number AS cnic,
			pe.name AS payment_entry_id,
				pi.name AS voucher_no,
			pi.posting_date AS purchase_date,
			pi.due_date AS due_date,
			pi.grand_total AS total_amount,
			(
				SELECT ROUND(SUM(pii.qty), 3)
				FROM `tabPurchase Invoice Item` pii
				WHERE pii.parent = pi.name
				AND pii.item_group = 'Products'
			) AS weight,
			pe.posting_date AS payment_date,
			per.allocated_amount AS amount_paid
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPayment Entry Reference` per
			ON per.reference_name = pi.name
			AND per.reference_doctype = 'Purchase Invoice'
		INNER JOIN `tabPayment Entry` pe
			ON pe.name = per.parent
		LEFT JOIN `tabSupplier` supp
			ON supp.name = pi.supplier
		WHERE {conditions}
		ORDER BY pe.posting_date DESC, supp.supplier_name ASC
		""",
		params,
		as_dict=True,
	)

	return data
