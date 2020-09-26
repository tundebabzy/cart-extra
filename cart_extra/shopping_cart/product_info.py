import frappe
from cart_extra.shopping_cart.cart import _get_cart_quotation
from erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings \
    import get_shopping_cart_settings, show_quantity_in_website
from erpnext.utilities.product import get_price, get_qty_in_stock
from erpnext.shopping_cart.product_info import\
    get_product_info_for_website as get_product_info_for_website_original


@frappe.whitelist(allow_guest=True)
def get_product_info_for_website(item_code, skip_quotation_creation=False):
    """get product price / stock info for website"""
    if frappe.session.user != 'Guest':
        return get_product_info_for_website_original(item_code, skip_quotation_creation)

    cart_quotation = _get_cart_quotation()
    cart_settings = get_shopping_cart_settings()

    price = get_price(
        item_code,
        cart_quotation.selling_price_list,
        cart_settings.default_customer_group,
        cart_settings.company
    )

    stock_status = get_qty_in_stock(item_code, "website_warehouse")

    product_info = {
        "price": price,
        "stock_qty": stock_status.stock_qty,
        "in_stock": stock_status.in_stock if stock_status.is_stock_item else 1,
        "qty": 0,
        "uom": frappe.db.get_value("Item", item_code, "stock_uom"),
        "show_stock_qty": show_quantity_in_website(),
        "sales_uom": frappe.db.get_value("Item", item_code, "sales_uom")
    }

    if product_info["price"]:
        if frappe.session.user != "Guest":
            item = cart_quotation.get({"item_code": item_code})
            if item:
                product_info["qty"] = item[0].qty

    return {
        "product_info": product_info,
        "cart_settings": cart_settings
    }
