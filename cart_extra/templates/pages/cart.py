import frappe
from cart_extra.shopping_cart.cart import get_cart_quotation
no_cache = 1
no_sitemap = 1


def get_context(context):
    context.update(get_cart_quotation())
