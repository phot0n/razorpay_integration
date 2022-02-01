import frappe
from frappe.utils.data import flt
from frappe.utils.password import get_decrypted_password

import json

from razorpay_integration.api import RazorpayPayment


__version__ = '0.0.1'



@frappe.whitelist()
def get_payment_url(
	razorpay_setting_name: str,
	amount: float,
	reference_docname: str,
	reference_doctype: str,
	**kwargs
):
	"""
	Some Acceptable kwargs:
		payload (dict): attach any key-value pair
		redirect_to (str): url for where you want to redirect on payment verification
		on_success (str): string-ed method path for running on successful verification of payment
		on_faliure (str): stringed method path for running on verification faliure of payment
		redirect_message (str): redirect message for appending to redirect url
		payer_email (str): email of payer
		payer_name (str): name of payer
		description (str): description of the payment
	"""

	# NOTE: this is done for local setups otherwise razorpay
	# throws a valdation error for email
	kwargs["payer_email"] = kwargs.get("payer_email", frappe.session.user) if (
				kwargs.get("payer_email", frappe.session.user) not in ("Guest", "Administrator")
			) else ""
	kwargs["payer_name"] = kwargs.get("payer_name", frappe.utils.get_fullname(frappe.session.user))

	kwargs["payload"] = kwargs.get("payload") or {}
	# this will override these existing payload keys
	# hence these are to be specified separately
	kwargs["payload"].update(
		{
			"redirect_to": kwargs.get("redirect_to", "/"),
			"on_success": kwargs.get("on_success"),
			"on_failure": kwargs.get("on_failure"),
			"redirect_message": kwargs.get("redirect_message")
		}
	)

	log = frappe.get_doc(
		doctype="Razorpay Payment Log",
		status="Created",
		razorpay_setting=razorpay_setting_name,
		reference_doctype=reference_doctype,
		reference_docname=reference_docname,
		description=kwargs.get("description"),
		amount=flt(amount),
		payload=json.dumps(kwargs["payload"])
	).insert(ignore_permissions=True)

	# use log name as reference id in payment link
	kwargs["reference_id"] = log.name

	# razorpay assumes amount precision upto 2 places
	# and needs it to be specified as a whole (int)
	kwargs["amount"] = int(amount * 100)

	# TODO: figure out a better way to avoid these 2 db calls
	razorpay_response = RazorpayPayment(
		kwargs.get("api_key", frappe.db.get_value("Razorpay Settings", razorpay_setting_name, "api_key")),
		get_decrypted_password("Razorpay Settings", razorpay_setting_name, fieldname="api_secret")
	).get_or_create_payment_link(**kwargs)

	log.payment_link_id = razorpay_response.get("id")
	log.payment_url = razorpay_response.get("short_url")
	log.valid_till = razorpay_response.get("expire_by")
	log.customer = json.dumps(razorpay_response.get("customer"))
	log.save(ignore_permissions=True)

	return razorpay_response.get("short_url")
