app_name = "leaf_procurement"
app_title = "Leaf Procurement"
app_publisher = "Sowaan"
app_description = "Tobaco purchase and process system"
app_email = "amir.baloch@sowaan.com"
app_license = "mit"

fixtures = [
	{
        "doctype":"Custom Field",
		"filters":[
			[
				"module", "=", "Leaf Procurement"
			]
		]
	},
	{
        "doctype":"Inventory Dimension",
		"filters":[
			[
				"name", "in", ("Sub Grade","Grade", "Lot Number", "Reclassification Grade")
			]
		]
	},
    {
        "doctype":"Custom HTML Block",
		"filters":[
			[
				"name", "in", ("Leaf Buying Day Block", "Bale Audit Day Block")
        
			]
		]
	},
    {
        "doctype":"Property Setter",
		"filters":[
			[
				"name", "in", (
                    "Supplier-naming_series-options", 
                    "Purchase Invoice-naming_series-options",
                    "Supplier-main-quick_entry",
                    "Supplier-mobile_no-reqd",
                    "Supplier-main-search_fields",
                    "Supplier-main-field_order",
					"Supplier-main-fields",
                    "Supplier-naming_series-depends_on",
                    "Supplier-supplier_group-hidden",
                    "Supplier-supplier_type-hidden",
                    "Supplier-is_transporter-hidden",
                    "Supplier-default_currency-hidden",
                    "Supplier-default_currency-default",
                    "Purchase Invoice-status-allow_on_submit",
                    "Purchase Invoice-status-options"
                    )
			]
		]
	},
    {
        "doctype":"Role",
		"filters":[
			[
				"name", "in", (
                    "Bale Registrar",
                    "Bale Purchaser",
                    "Bale Weigher",
                    "LP Audit Officer",
                    "Bale Dispatcher",
                    "Bale Receiver"
                    )
			]
		]
	},
    {
        "doctype":"Custom DocPerm",
		"filters":[
			[
				"role", "in", (
                    "Bale Registrar",
                    "Bale Purchaser",
                    "Bale Weigher",
                    "LP Audit Officer",
                    "Bale Dispatcher",
                    "Bale Receiver",
                    "System Manager"
                    )
			]
		]
	},
    {
        "doctype":"Module Profile",
		"filters":[
			[
				"name", "in", (
                    "Leaf Procurement User"
                    )
			]
		]
	},     
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "leaf_procurement",
# 		"logo": "/assets/leaf_procurement/logo.png",
# 		"title": "Leaf Procurement",
# 		"route": "/leaf_procurement",
# 		"has_permission": "leaf_procurement.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/leaf_procurement/css/leaf_procurement.css"
# app_include_js = "/assets/leaf_procurement/js/leaf_procurement.js"

# include js, css files in header of web template
# web_include_css = "/assets/leaf_procurement/css/leaf_procurement.css"
# web_include_js = "/assets/leaf_procurement/js/leaf_procurement.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "leaf_procurement/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Supplier" : "public/js/supplier.js",
    "Purchase Invoice" : "public/js/purchase_invoice.js",
    "Driver" : "public/js/driver.js",
}
doctype_list_js = {"Purchase Invoice" : "public/js/purchase_invoice_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "leaf_procurement/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "leaf_procurement.utils.jinja_methods",
# 	"filters": "leaf_procurement.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "leaf_procurement.install.before_install"
after_install = "leaf_procurement.install.after_install"

# Uninstallation
# ------------

before_uninstall = "leaf_procurement.uninstall.before_uninstall"
# after_uninstall = "leaf_procurement.uninstall.after_uninstall"

after_migrate = [
    "leaf_procurement.setup.setup_hooks.set_supplier_naming_series"
]


# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "leaf_procurement.utils.before_app_install"
# after_app_install = "leaf_procurement.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "leaf_procurement.utils.before_app_uninstall"
# after_app_uninstall = "leaf_procurement.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "leaf_procurement.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Supplier": {
        "validate": "leaf_procurement.leaf_procurement.custom.doctype.supplier.supplier.validate_unique_nic"
    },
    "Purchase Invoice": {
        "on_cancel":     "leaf_procurement.leaf_procurement.events.purchase_invoice_hooks.on_cancel_purchase_invoice",
        "before_cancel": "leaf_procurement.leaf_procurement.events.purchase_invoice_hooks.before_cancel_purchase_invoice",
        "before_submit": "leaf_procurement.leaf_procurement.events.purchase_invoice_hooks.before_submit_purchase_invoice",
        "autoname": "leaf_procurement.leaf_procurement.events.purchase_invoice_hooks.autoname_purchase_invoice"
    }
}


# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    "cron":{
        "*/15 * * * *":[
            "leaf_procurement.tasks.sync.hybrid_sync"
        ]
    }
# 	"all": [
# 		"leaf_procurement.tasks.all"
# 	],
# 	"daily": [
# 		"leaf_procurement.tasks.daily"
# 	],
# 	"hourly": [
# 		"leaf_procurement.tasks.hourly"
# 	],
# 	"weekly": [
# 		"leaf_procurement.tasks.weekly"
# 	],
# 	"monthly": [
# 		"leaf_procurement.tasks.monthly"
# 	],
}

# Testing
# -------

# before_tests = "leaf_procurement.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "leaf_procurement.event.get_events"
# }
override_doctype_class = {
    "Warehouse": "leaf_procurement.leaf_procurement.overrides.warehouse.CustomWarehouse",
    "Supplier": "leaf_procurement.leaf_procurement.overrides.supplier.CustomSupplier",
    "Driver": "leaf_procurement.leaf_procurement.overrides.driver.CustomDriver",
    #"Purchase Invoice": "leaf_procurement.leaf_procurement.overrides.purchase_invoice.CustomPurchaseInvoice"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "leaf_procurement.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["leaf_procurement.utils.before_request"]
# after_request = ["leaf_procurement.utils.after_request"]

# Job Events
# ----------
# before_job = ["leaf_procurement.utils.before_job"]
# after_job = ["leaf_procurement.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"leaf_procurement.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
