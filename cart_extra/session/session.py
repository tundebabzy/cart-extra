import secrets
import frappe
from frappe.utils import random_string


def get_extra_cart_session():
    sid = frappe.local.session.get(
        "ec_sid", frappe.local.request.cookies.get("ec_sid"))
    ec_sid = "ec_session_{0}".format(sid) if sid else None
    ec_session = get_guest_session(sid=ec_sid)

    if sid is not None and ip_has_changed(session=ec_session):
        sid = None
        ec_sid = None
        ec_session = None

    if ec_session is None:
        if not sid:
            sid = random_string(64)
            ec_sid = "ec_session_{0}".format(sid)

        ec_session = {
            "session_ip": frappe.local.request_ip,
            "token": secrets.token_urlsafe()
        }

        frappe.cache().set_value(ec_sid, ec_session)

    frappe.local.session["ec_sid"] = sid
    frappe.local.cookie_manager.set_cookie(
        "ec_sid", frappe.local.session["ec_sid"])

    return ec_session


def get_guest_session(sid=None):
    """
    returns the guest session if available
    """
    if sid is not None:
        return frappe.cache().get_value(sid)


def ip_has_changed(ec_sid=None, session=None):
    """
    return True if the ip address saved in the guest session is different from
    that in the incoming request
    """
    if ec_sid is None and session is None:
        return

    ec_session = session or frappe.cache().get_value(ec_sid)
    return ec_session.get("session_ip") != frappe.local.request_ip


def set_extra_cart_session(session):
    session = get_extra_cart_session()
    frappe.cache().set_value("ec_session_{0}".format(
        frappe.local.session["ec_sid"]), session)
    return session
