# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "cart_extra"
app_title = "Cart Extra"
app_publisher = "Babatunde Akinyanmi"
app_description = "Custom app for ERPNext that adds a few extra features to the shopping cart"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "tundebabzy@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/cart_extra/css/cart_extra.css"
# app_include_js = "/assets/cart_extra/js/cart_extra.js"

# include js, css files in header of web template
# web_include_css = "/assets/cart_extra/css/cart_extra.css"
web_include_js = "/assets/cart_extra.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "cart_extra.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "cart_extra.install.before_install"
# after_install = "cart_extra.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "cart_extra.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"cart_extra.tasks.all"
# 	],
# 	"daily": [
# 		"cart_extra.tasks.daily"
# 	],
# 	"hourly": [
# 		"cart_extra.tasks.hourly"
# 	],
# 	"weekly": [
# 		"cart_extra.tasks.weekly"
# 	]
# 	"monthly": [
# 		"cart_extra.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "cart_extra.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# on_session_creation = "erpnext.shopping_cart.utils.set_cart_count"
on_logout = "cart_extra.utils.logout"

override_whitelisted_methods = {
    'erpnext.shopping_cart.cart.update_cart': 'cart_extra.shopping_cart.cart.update_cart',
    'erpnext.shopping_cart.cart.get_shopping_cart_menu': 'cart_extra.shopping_cart.cart.get_shopping_cart_menu',
    'erpnext.shopping_cart.cart.get_cart_quotation': 'cart_extra.shopping_cart.cart.get_cart_quotation',
    'erpnext.shopping_cart.product_info.get_product_info_for_website': 'cart_extra.shopping_cart.product_info.get_product_info_for_website',
    'erpnext.shopping_cart.cart.place_order': 'cart_extra.shopping_cart.cart.place_order'
}

fixtures = [
    'Lead Source'
]
