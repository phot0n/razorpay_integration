# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.data import cint, flt
from frappe.utils.password import get_decrypted_password

import json
import math
import time


def get_epoch_time() -> int:
	# returns the current epoch time
	return math.ceil(time.time())

def add_to_epoch(seconds: int) -> int:
	# adds seconds to the current epoch time
	return get_epoch_time() + seconds

def convert_epoch_to_timestamp(epoch_time: int):
	# converts any given epoch time to human readable datetime
	return time.ctime(epoch_time)


@frappe.whitelist()
def get_payment_url(
	razorpay_setting_name: str,
	amount: float,
	reference_docname: str,
	reference_doctype: str,
	**kwargs
):
	from razorpay_integration.api import RazorpayPayment

	# NOTE: this is done for local setups otherwise razorpay
	# throws a valdation error for email
	kwargs["payer_email"] = kwargs.get("payer_email", frappe.session.user) if (
				kwargs.get("payer_email", frappe.session.user) not in ("Guest", "Administrator")
			) else ""
	kwargs["payer_name"] = kwargs.get("payer_name", frappe.utils.get_fullname(frappe.session.user))

	log = frappe.get_doc(
		doctype="Razorpay Payment Log",
		status="Created",
		razorpay_setting=razorpay_setting_name,
		reference_doctype=reference_doctype,
		reference_docname=reference_docname,
		description=kwargs.get("description"),
		amount=flt(amount),
		payload=json.dumps(
			dict(
				redirect_to=kwargs.get("redirect_to", "/"),
				on_success_payment=kwargs.get("on_success_payment", ""),
				on_failed_payment=kwargs.get("on_failed_payment", "")
			)
		)
	).insert(ignore_permissions=True)

	# use log name as reference id in payment link
	kwargs["reference_id"] = log.name

	# razorpay assumes amount precision upto 2 places
	# and needs it to be specified as a whole (int)
	kwargs["amount"] = cint(amount * 100)

	razorpay_response = RazorpayPayment(
		frappe.db.get_value("Razorpay Settings", razorpay_setting_name, "api_key"),
		get_decrypted_password("Razorpay Settings", razorpay_setting_name, fieldname="api_secret")
	).get_or_create_payment_link(**kwargs)

	log.payment_link_id = razorpay_response.get("id")
	log.payment_url = razorpay_response.get("short_url")
	log.valid_till = razorpay_response.get("expire_by")
	log.customer = json.dumps(razorpay_response.get("customer"))
	log.save(ignore_permissions=True)

	return razorpay_response.get("short_url")


def run_callback(method_string: str, **kwargs):
	if not method_string:
		return

	try:
		frappe.get_attr(method_string)(**kwargs)
	except Exception as e:
		frappe.log_error(method_string + " : " + e, title=frappe._("Callback Error"))
		frappe.throw(e)
