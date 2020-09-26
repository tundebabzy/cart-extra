import frappe
from cart_extra.session import get_extra_cart_session, set_extra_cart_session


@frappe.whitelist(allow_guest=True)
def create_cart():
    session = get_extra_cart_session()
    set_extra_cart_session(session)


def create_lead_if_needed(name):
    possible = frappe.get_all('Lead', filters={'lead_name': name})
    if not possible:
        lead = frappe.new_doc('Lead')
        lead.lead_name = name
        # Lead source should be user defined in Shopping Cart settings
        lead.source = 'Website Visitor'
        lead.insert(ignore_permissions=True)
        return lead


def logout():
    sid = frappe.local.session.get(
        'ec_sid', frappe.local.request.cookies.get('ec_sid'))
    if sid:
        ec_sid = 'ec_session_{0}'.format(sid)
        frappe.cache().set_value(ec_sid, None)
        frappe.local.session['ec_sid'] = ''
        frappe.local.session['cart_count'] = 0
        frappe.local.cookie_manager.set_cookie(
            'ec_sid', '')
        frappe.local.cookie_manager.set_cookie(
            'cart_count', 0)
