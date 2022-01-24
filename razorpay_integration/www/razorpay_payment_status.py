import frappe
from frappe.utils.password import get_decrypted_password

import json
from typing import Dict
from urllib.parse import urlencode

from razorpay_integration.api import RazorpayPayment
from razorpay_integration.utils import run_callback


no_cache = 1

def get_context(context):
	if not frappe.form_dict.get("razorpay_payment_link_reference_id") or len(frappe.form_dict) < 5:
		frappe.redirect_to_message(
			frappe._("Information is missing"), frappe._("Link/URL is incomplete!")
		)
		frappe.local.flags.redirect_location = frappe.local.response.location

		raise frappe.Redirect

	log_doctype = "Razorpay Payment Log"
	log = frappe.db.get_value(
		log_doctype,
		frappe.form_dict.razorpay_payment_link_reference_id,
		fieldname=[
			"status", "payload", "razorpay_setting", "reference_doctype", "reference_docname"
		],
		as_dict=True
	)
	if not log:
		update_context(
			context,
			"Invalid Reference ID",
			"The reference ID does not exist !",
			"/"
		)
		return

	title = "Payment Verification Status"
	if not is_new_payment(context, log.status, title):
		return

	payload = json.loads(log.payload)
	updated_status = verify_payment_and_run_callback(log.razorpay_setting, payload)
	payment_id = frappe.form_dict.razorpay_payment_id

	update_payment_log(updated_status, payment_id)

	# NOTE: this is for backwards compatibility
	# as on_payment_authorized methods are used in erpnext
	backwards_redirect_to = None
	if updated_status == "Paid":
		backwards_redirect_to = run_on_payment_authorized_method(log.reference_doctype, log.reference_docname)

	redirect_to = backwards_redirect_to or payload.get("redirect_to", "/")
	if payload.get("redirect_message"):
		redirect_to += "&" + urlencode({"redirect_message": payload["redirect_message"]})

	update_context(
		context,
		title,
		get_message_based_on_status(updated_status),
		redirect_to
	)


def update_context(ctx, title: str, message: str, redirect_to: str):
	ctx.title = title
	ctx.message = message
	ctx.redirect_to = redirect_to


def is_new_payment(ctx, status, title):
	if status == "Created":
		return True

	# status was already set and user has revisited the page
	if status == "Expired":
		# we generally won't encounter expired ref id in the verification page
		title = "Expired Reference ID"

	update_context(
		ctx,
		title,
		get_message_based_on_status(status),
		"/"
	)

	return False


def get_message_based_on_status(status: str):
	status_message = {
		"Paid": "The Status has been verified and the Payment was Successful !",
		"Refund": "Your Payment is being Refunded. Please wait for sometime for it to be reflected in your account !",
		"Failed": "Payment Verification Failed!! Your Payment is currently under review !",
		"Refunded": "Your payment has been Refunded and might take some time to reflect in your account !!",
		"Expired": "The Reference ID provided has been expired. Please start a new payment !"
	}

	return status_message[status]


def verify_payment_and_run_callback(razorpay_setting: str, razorpay_log_payload: Dict):
	api_secret = get_decrypted_password(
		"Razorpay Settings", razorpay_setting, fieldname="api_secret"
	)

	status = "Paid"
	if not RazorpayPayment.verify_payment_signature(
		api_secret,
		razorpay_payment_link_id=frappe.form_dict.razorpay_payment_link_id,
		razorpay_payment_link_reference_id=frappe.form_dict.razorpay_payment_link_reference_id,
		razorpay_payment_link_status=frappe.form_dict.razorpay_payment_link_status,
		razorpay_payment_id=frappe.form_dict.razorpay_payment_id,
		razorpay_signature=frappe.form_dict.razorpay_signature
	):
		status = "Failed"
		if frappe.db.get_value("Razorpay Settings", razorpay_setting, "enable_auto_refunds"):
			# automatically allows scheduler to pick this up in its next iteration
			status = "Refund"

	run_callback(
		razorpay_log_payload.get("on_success" if status == "Paid" else "on_failure")
	)

	return status


def update_payment_log(updated_status: str, payment_id: str):
	# updating the log
	log_doctype = frappe.qb.DocType("Razorpay Payment Log")
	frappe.qb.update(
		log_doctype
	).set(
		log_doctype.status, updated_status
	).set(
		log_doctype.payment_id, payment_id
	).set(
		log_doctype.payload, None
	).where(
		log_doctype.name == frappe.form_dict.razorpay_payment_link_reference_id
	).run()

	# currently without explicit commit the log isn't updating
	frappe.db.commit()


def run_on_payment_authorized_method(reference_doctype: str, reference_docname: str):
	redirect_to = None
	try:
		redirect_to = frappe.get_doc(
			reference_doctype, reference_docname
		).run_method("on_payment_authorized", "Completed")
	except Exception as e:
		frappe.log_error(e)

	return redirect_to
