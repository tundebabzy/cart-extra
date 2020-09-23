import frappe
from cart_extra.session import get_extra_cart_session, set_extra_cart_session


@frappe.whitelist(allow_guest=True)
def create_cart():
    session = get_extra_cart_session()
    set_extra_cart_session(session)


def create_lead_if_needed(name):
    if not frappe.db.exists('Lead', name):
        lead = frappe.new_doc('Lead')
        lead.lead_name = name
        # Lead source should be user defined in Shopping Cart settings
        lead.source = 'Website Visitor'
        lead.insert(ignore_permissions=True)
        frappe.db.commit()


def logout():
    sid = frappe.local.session.get(
        'ec_sid', frappe.local.request.cookies.get('ec_sid'))
    if sid:
        ec_sid = 'ec_session_{0}'.format(sid)
        frappe.cache().set_value(ec_sid, None)
        frappe.local.session['ec_sid'] = ''
        frappe.local.cookie_manager.set_cookie(
            'ec_sid', '')
