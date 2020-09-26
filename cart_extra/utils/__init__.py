import frappe
from frappe import _
from cart_extra.session import get_extra_cart_session, set_extra_cart_session
from erpnext.accounts.doctype.payment_request.payment_request import\
    get_amount, get_gateway_details
from erpnext.accounts.party import get_party_account, get_party_bank_account


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


def make_payment_request(**args):
	"""Make payment request"""

	args = frappe._dict(args)

	ref_doc = frappe.get_doc(args.dt, args.dn)
	grand_total = get_amount(ref_doc)
	if args.loyalty_points and args.dt == "Sales Order":
		from erpnext.accounts.doctype.loyalty_program.loyalty_program import validate_loyalty_points
		loyalty_amount = validate_loyalty_points(ref_doc, int(args.loyalty_points))
		frappe.db.set_value("Sales Order", args.dn, "loyalty_points", int(args.loyalty_points), update_modified=False)
		frappe.db.set_value("Sales Order", args.dn, "loyalty_amount", loyalty_amount, update_modified=False)
		grand_total = grand_total - loyalty_amount

	gateway_account = get_gateway_details(args) or frappe._dict()

	bank_account = (get_party_bank_account(args.get('party_type'), args.get('party'))
		if args.get('party_type') else '')

	existing_payment_request = None
	if args.order_type == "Shopping Cart":
		existing_payment_request = frappe.db.get_value("Payment Request",
			{"reference_doctype": args.dt, "reference_name": args.dn, "docstatus": ("!=", 2)})

	if existing_payment_request:
		frappe.db.set_value("Payment Request", existing_payment_request, "grand_total", grand_total, update_modified=False)
		pr = frappe.get_doc("Payment Request", existing_payment_request)
	else:
		if args.order_type != "Shopping Cart":
			existing_payment_request_amount = \
				get_existing_payment_request_amount(args.dt, args.dn)

			if existing_payment_request_amount:
				grand_total -= existing_payment_request_amount

		pr = frappe.new_doc("Payment Request")
		pr.update({
			"payment_gateway_account": gateway_account.get("name"),
			"payment_gateway": gateway_account.get("payment_gateway"),
			"payment_account": gateway_account.get("payment_account"),
			"payment_request_type": args.get("payment_request_type"),
			"currency": "USD",
			"grand_total": grand_total,
			"email_to": args.recipient_id or ref_doc.owner,
			"subject": _("Payment Request for {0}").format(args.dn),
			"message": gateway_account.get("message") or get_dummy_message(ref_doc),
			"reference_doctype": args.dt,
			"reference_name": args.dn,
			"party_type": args.get("party_type") or "Customer",
			"party": args.get("party") or ref_doc.get("customer"),
			"bank_account": bank_account
		})

		if args.order_type == "Shopping Cart" or args.mute_email:
			pr.flags.mute_email = True

		if args.submit_doc:
			pr.insert(ignore_permissions=True)
			pr.submit()

	if args.order_type == "Shopping Cart":
		frappe.db.commit()

	if args.return_doc:
		return pr

	return pr.get_payment_url()

