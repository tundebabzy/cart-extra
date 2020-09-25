import frappe
from frappe.utils import cint, flt, get_fullname, cstr
from erpnext.shopping_cart.cart import update_cart as original_update_cart
from cart_extra.session import get_extra_cart_session
from cart_extra.utils import create_lead_if_needed
from erpnext.shopping_cart.doctype.shopping_cart_settings.\
    shopping_cart_settings import get_shopping_cart_settings
from erpnext.shopping_cart.cart import apply_cart_settings,\
    get_applicable_shipping_rules, decorate_quotation_doc,\
    get_shopping_cart_menu as get_shopping_cart_menu_original,\
    get_cart_quotation as get_cart_quotation_original,\
    place_order as place_order_original
import json


def set_cart_count(quotation=None):
    if cint(frappe.db.get_singles_value("Shopping Cart Settings", "enabled")):
        if not quotation:
            quotation = _get_cart_quotation()
        cart_count = cstr(len(quotation.get("items")))

        if hasattr(frappe.local, "cookie_manager"):
            frappe.local.cookie_manager.set_cookie("cart_count", cart_count)


@frappe.whitelist(allow_guest=True)
def update_cart(item_code, qty, with_items=False):
    if frappe.session.user != 'Guest':
        return original_update_cart(item_code, qty, with_items)
    else:
        session = get_extra_cart_session()
        create_lead_if_needed(session['token'])
        party = _party(session['token'])

    quotation = _get_cart_quotation(party=party)

    empty_card = False
    qty = flt(qty)
    if qty == 0:
        quotation_items = quotation.get(
            "items", {"item_code": ["!=", item_code]})

        if quotation_items:
            quotation.set("items", quotation_items)
        else:
            empty_card = True

    else:
        quotation_items = quotation.get("items", {"item_code": item_code})
        if not quotation_items:
            quotation.append("items", {
                "doctype": "Quotation Item",
                "item_code": item_code,
                "qty": qty
            })
        else:
            quotation_items[0].qty = qty

    apply_cart_settings(quotation=quotation)

    quotation.flags.ignore_permissions = True
    quotation.payment_schedule = []
    if not empty_card:
        quotation.save()
    else:
        quotation.delete()
        quotation = None

    set_cart_count(quotation)

    context = get_cart_quotation(quotation)

    if cint(with_items):
        return {
            "items": frappe.render_template(
                "templates/includes/cart/cart_items.html", context),
            "taxes": frappe.render_template(
                "templates/includes/order/order_taxes.html", context),
        }
    else:
        return {
            'name': quotation.name,
            'shopping_cart_menu': get_shopping_cart_menu(context)
        }


@frappe.whitelist(allow_guest=True)
def get_cart_quotation(doc=None):
    if frappe.session.user != 'Guest':
        return get_cart_quotation_original(doc)
    session = get_extra_cart_session()
    party = _party(session['token'])

    if not doc:
        quotation = _get_cart_quotation(party)
        doc = quotation
        set_cart_count(quotation)

    return {
        "doc": decorate_quotation_doc(doc),
        "shipping_addresses": [],
        "billing_addresses": [],
        "shipping_rules": get_applicable_shipping_rules(party)
    }


@frappe.whitelist(allow_guest=True)
def get_shopping_cart_menu(context=None):
    if frappe.session.user != 'Guest':
        return get_shopping_cart_menu_original(context)
    if not context:
        context = get_cart_quotation()
    return get_shopping_cart_menu_original(context=context)


@frappe.whitelist(allow_guest=True)
def place_order(billing_address=None, shipping_address=None):
    if frappe.session.user != 'Guest':
        return place_order_original()

    if isinstance(billing_address, str):
        billing_address = json.loads(billing_address)
    if isinstance(shipping_address, str):
        shipping_address = json.loads(shipping_address)

    quotation = _get_cart_quotation()

    _update_lead_name(quotation.party_name)
    _add_addresses(
        shipping_address, billing_address, quotation.party_name, quotation)

    cart_settings = frappe.db.get_value(
        "Shopping Cart Settings", None,
        ["company", "allow_items_not_in_stock"], as_dict=1)
    quotation.company = cart_settings.company
    if not quotation.get("customer_address"):
        throw(_("{0} is required").format(
            _(quotation.meta.get_label("customer_address"))))

    quotation.flags.ignore_permissions = True
    quotation.submit()

    if quotation.quotation_to == 'Lead' and quotation.party_name:
        # company used to create customer accounts
        frappe.defaults.set_user_default("company", quotation.company)

    from erpnext.selling.doctype.quotation.quotation import _make_sales_order
    sales_order = frappe.get_doc(_make_sales_order(
        quotation.name, ignore_permissions=True))
    sales_order.payment_schedule = []

    if not cart_settings.allow_items_not_in_stock:
        for item in sales_order.get("items"):
            item.reserved_warehouse, is_stock_item = frappe.db.get_value(
                "Item", item.item_code, ["website_warehouse", "is_stock_item"])

            if is_stock_item:
                item_stock = get_qty_in_stock(
                    item.item_code, "website_warehouse")
                if item.qty > item_stock.stock_qty[0][0]:
                    throw(
                        _("Only {0} in stock for item {1}").format(
                            item_stock.stock_qty[0][0], item.item_code))

    sales_order.flags.ignore_permissions = True
    sales_order.insert()
    sales_order.submit()

    if hasattr(frappe.local, "cookie_manager"):
        frappe.local.cookie_manager.delete_cookie("cart_count")

    return sales_order.name


def _add_address(address_type, address, lead_name):
    doc = frappe.new_doc('Address')
    doc.address_type = address_type
    doc.address_line1 = address['address_line1']
    doc.address_line2 = address['address_line2']
    doc.city = address['city']
    doc.pincode = address['pincode']
    doc.state = address['state']
    doc.email_id = address['email_id']
    doc.phone = address['phone']
    doc.append('links', {
        'link_doctype': 'Lead',
        'link_name': lead_name
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _add_addresses(address_shipping, address_billing, lead_name, quotation):
    shipping_address_name = _add_address(
        'Shipping', address_shipping, lead_name)
    billing_address_name = _add_address('Billing', address_billing, lead_name)
    quotation.customer_address = billing_address_name
    quotation.shipping_address_name = shipping_address_name


def _get_cart_quotation(party=None):
    '''
    Return the open Quotation of type "Shopping Cart" or make a new one
    '''
    lead = None
    lead_name = None
    if not party:
        session = get_extra_cart_session()
        lead = create_lead_if_needed(session['token'])
        party = _party(session['token'])
    elif party and party['name']:
        lead = create_lead_if_needed(party['name'])

    if not lead:
        lead_name = frappe.db.sql(
            '''
            select name from `tabLead` where lead_name = %s order by creation
            desc limit 1
            ''',
            (party['name'],), as_dict=True
        )

    quotation = None
    if lead_name or lead.lead_name:
        quotation = frappe.get_all(
            "Quotation", fields=["name"],
            filters={
                "party_name": lead.name if lead else lead_name[0].name,
                "order_type": "Shopping Cart",
                "docstatus": 0
            },
            order_by="modified desc", limit_page_length=1)

    if quotation:
        qdoc = frappe.get_doc("Quotation", quotation[0].name)
    else:
        company = frappe.db.get_value(
            "Shopping Cart Settings", None, ["company"])
        qdoc = frappe.get_doc({
            "doctype": "Quotation",
            "naming_series":
                get_shopping_cart_settings().quotation_series or "QTN-CART-",
            "quotation_to": party['doctype'],
            "company": company,
            "order_type": "Shopping Cart",
            "status": "Draft",
            "docstatus": 0,
            "__islocal": 1,
            "party_name": lead_name[0].name if lead_name else lead.name
        })

        # qdoc.contact_person = frappe.db.get_value("Contact", {"email_id": frappe.session.user})
        # qdoc.contact_email = frappe.session.user

        qdoc.flags.ignore_permissions = True
        qdoc.run_method("set_missing_values")
        apply_cart_settings(party, qdoc)

    return qdoc


def _party(name):
    return {
        'name': name,
        'doctype': 'Lead'
    }


def _update_lead_name(name):
    lead = frappe.get_doc("Lead", name)
    lead.lead_name = name
    lead.save(ignore_permissions=True)
