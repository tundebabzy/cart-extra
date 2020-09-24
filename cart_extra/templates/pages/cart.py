import frappe
from cart_extra.shopping_cart.cart import get_cart_quotation
no_cache = 1
no_sitemap = 1


print('---------------------------8888------------------')
def get_context(context):
    print('overriden the context')
    context.update(get_cart_quotation())
