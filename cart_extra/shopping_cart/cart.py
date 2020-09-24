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
    get_cart_quotation as get_cart_quotation_original


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

    # addresses = get_address_docs(party=party)

    # if not doc.customer_address and addresses:
    #     update_cart_address("customer_address", addresses[0].name)

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


def _get_cart_quotation(party=None):
    '''
    Return the open Quotation of type "Shopping Cart" or make a new one
    '''
    lead = None
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
                "party_name": lead.lead_name if lead else lead_name[0].name,
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
            "party_name": lead_name[0].name
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
