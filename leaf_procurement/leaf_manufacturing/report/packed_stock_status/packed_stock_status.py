import frappe  # type: ignore


def execute(filters=None):
	if not filters:
		filters = frappe._dict()

	# -----------------------------
	# Columns
	# -----------------------------
	columns = [
		{"label": "Packed Grade", "fieldname": "prized_grade", "fieldtype": "Data", "width": 150},

		{"label": "Total Purchased Nos", "fieldname": "production_qty", "fieldtype": "Float", "width": 120},
		{"label": "Total Purchased KGs", "fieldname": "production_kgs", "fieldtype": "Float", "width": 120},

		{"label": "Total Despatch Nos", "fieldname": "shipment_qty", "fieldtype": "Float", "width": 120},
		{"label": "Total Despatch KGs", "fieldname": "shipment_kgs", "fieldtype": "Float", "width": 120},

		{"label": "Closing Stock Nos", "fieldname": "qty_diff", "fieldtype": "Float", "width": 120},
		{"label": "Closig Stock KGs", "fieldname": "kgs_diff", "fieldtype": "Float", "width": 120},
	]

	# -----------------------------
	# Conditions
	# -----------------------------
	params = {}   

	shipment_location_condition = ""
	if filters.get("location"):
		shipment_location_condition = " AND ts.location_from = %(location)s"
		params["location"] = filters.location

	shipment_date_condition = ""
	if filters.get("from_date"):
		shipment_date_condition += " AND ts.date >= %(from_date)s"
		params["from_date"] = filters.from_date

	if filters.get("to_date"):
		shipment_date_condition += " AND ts.date <= %(to_date)s"
		params["to_date"] = filters.to_date


	# -----------------------------
	# SQL (NO CARTESIAN PRODUCT)
	# -----------------------------
	data = frappe.db.sql(
		f"""
		SELECT
			COALESCE(ship.prized_grade, prod.prized_grade) AS prized_grade,

			IFNULL(ship.shipment_qty, 0) AS shipment_qty,
			IFNULL(prod.production_qty, 0) AS production_qty,
			IFNULL(prod.production_qty, 0) - IFNULL(ship.shipment_qty, 0) AS qty_diff,

			IFNULL(ship.shipment_kgs, 0) AS shipment_kgs,
			IFNULL(prod.production_kgs, 0) AS production_kgs,
			IFNULL(prod.production_kgs, 0) - IFNULL(ship.shipment_kgs, 0) AS kgs_diff

		FROM
		(
			/* -------- SHIPMENT (OUT) -------- */
			SELECT
				tsd.prized_grade,
				SUM(tsd.quantity) AS shipment_qty,
				SUM(tsd.kgs) AS shipment_kgs
			FROM `tabTobacco Shipment` ts
			JOIN `tabTobacco Shipment Detail` tsd
				ON ts.name = tsd.parent
			WHERE                
					ts.docstatus = 1
					{shipment_location_condition}
					{shipment_date_condition}
			GROUP BY tsd.prized_grade
		) ship

		LEFT JOIN
		(
			/* -------- PRODUCTION (IN) -------- */
			SELECT
				pice.prized_grade,
				SUM(pice.quantity) AS production_qty,
				SUM(pice.kgs) AS production_kgs
			FROM `tabPrized Item Creation` pic
			JOIN `tabPrized Item Creation Entry` pice
				ON pic.name = pice.parent
			WHERE                
					pic.docstatus = 1										
			GROUP BY pice.prized_grade
		) prod
		ON prod.prized_grade = ship.prized_grade

		ORDER BY prized_grade
		""",
		params,
		as_dict=True,
	)

	return columns, data
