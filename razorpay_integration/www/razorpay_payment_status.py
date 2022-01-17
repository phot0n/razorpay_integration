import frappe
from frappe.utils.password import get_decrypted_password

import json
from typing import Dict

from razorpay_integration.api import RazorpayPayment
from razorpay_integration.utils import run_callback


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
		frappe.form_dict["razorpay_payment_link_reference_id"],
		fieldname=["status", "payload", "razorpay_setting"]
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
	if not is_new_payment(context, log[0], title):
		return

	payload = json.loads(log[1])
	updated_status = verify_payment_and_run_callback(log[2], payload)
	payment_id = frappe.form_dict["razorpay_payment_id"]

	# updating the log
	log_doctype = frappe.qb.DocType(log_doctype)
	frappe.qb.update(
		log_doctype
	).set(
		log_doctype.status, updated_status
	).set(
		log_doctype.payment_id, payment_id
	).set(
		log_doctype.payload, None
	).where(
		log_doctype.name == frappe.form_dict["razorpay_payment_link_reference_id"]
	).run()

	update_context(
		context,
		title,
		get_message_based_on_status(updated_status),
		payload.get("redirect_to", "/")
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
		"Refund": """Payment Verification Failed!! Your Payment is being Refunded.
			Please wait for sometime for it to be reflected in your account !""",
		"Failed": "Payment Verification Failed!! Your Payment is currently under review !",
		"Refunded": "Your payment has been refunded and might take some time to reflect in your account !!",
		"Expired": "The Reference ID provided has been expired. Please start a new payment !"
	}

	return status_message[status]


def verify_payment_and_run_callback(razorpay_setting: str, razorpay_log_payload: Dict):
	api_secret = get_decrypted_password(
		"Razorpay Settings", razorpay_setting, fieldname="api_secret"
	)

	if not RazorpayPayment.verify_payment_signature(
		api_secret,
		**frappe.form_dict
	):
		status = "Failed"
		if frappe.db.get_value("Razorpay Settings", razorpay_setting, "enable_auto_refunds"):
			# automatically allows scheduler to pick this up in its next iteration
			status = "Refund"

		run_callback(razorpay_log_payload.get("on_failed_payment"))

	else:
		status = "Paid"
		run_callback(razorpay_log_payload.get("on_success_payment"))

	return status
