frappe.provide("leaf_procurement.setup");

frappe.pages["setup-wizard"].on_page_load = function (wrapper) {
	if (frappe.sys_defaults.company) {
		frappe.set_route("desk");
		return;
	}
};

frappe.setup.on("before_load", function () {
	leaf_procurement.setup.slides_settings.map(frappe.setup.add_slide);
});


leaf_procurement.setup.slides_settings = [
	{
		// Organization
		name: "leaf_procurement_setup",
		title: __("Setup Leaf Procurement"),
		icon: "fa fa-stock-overflow",
		fields: [
			{
				fieldname: "server_url",
				label: __("Server URL"),
				fieldtype: "Data",
				default: "https://samsons.sowaanerp.com",
				reqd: 1,
			},
			{ fieldtype: "Section Break" },
			{
				fieldname: "api_key",
				label: __("API Key"),
				fieldtype: "Data",
				reqd: 1,
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "api_secret",
				label: __("API Secret"),
				fieldtype: "Data",
				reqd: 1,
			},
			{ fieldtype: "Section Break", label: __("Defaults") },
			{
				fieldname: "lot_size",
				label: __("Lot Size"),
				fieldtype: "Int",
				default: 12,
				reqd: 1,
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "barcode_length",
				label: __("Barcode Length"),
				fieldtype: "Int",
				default: 11,
				reqd: 1,
			},
		],

	},
];
