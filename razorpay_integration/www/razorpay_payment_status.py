import frappe
from frappe.utils.password import get_decrypted_password

import json

from razorpay_integration.api import RazorpayPayment


def get_context(context):
	if not frappe.form_dict.get("razorpay_payment_link_reference_id"):
		frappe.redirect_to_message(
			frappe._("Information is missing"),
			frappe._("Link/URL is incomplete!")
		)
		frappe.local.flags.redirect_location = frappe.local.response.location

		raise frappe.Redirect

	try:
		log = frappe.get_doc("Razorpay Payment Log", frappe.form_dict["razorpay_payment_link_reference_id"])
	except frappe.DoesNotExistError:
		handle_context(
			context,
			"Invalid Reference ID",
			"The reference ID does not exist !",
			"/"
		)

		return

	title = "Payment Verification Status"

	if is_handleable_status(context, log.status, title, "/"):
		return

	verify_payment_and_run_callbacks(log)

	log.payment_id = frappe.form_dict["razorpay_payment_id"]
	log.save(ignore_permissions=True)

	handle_context(
		context,
		title,
		get_message_based_on_status(log.status),
		json.loads(log.payload).get("redirect_to", "/")
	)


def handle_context(ctx, title, message, redirect_to):
	ctx.title = title
	ctx.message = message
	ctx.redirect_to = redirect_to


def is_handleable_status(ctx, status, title, redirect_to):
	if status == "Created":
		return False

	elif status == "Expired":
		title = "Expired Reference ID"

	handle_context(
		ctx,
		title,
		get_message_based_on_status(status),
		redirect_to
	)

	return True


def get_message_based_on_status(status):
	status_message = {
		"Paid": "The Status has been verified and the Payment was Successful !",
		"Refund": """Payment Verification Failed!! Your Payment is being Refunded.
			Please wait for sometime for it to be reflected in your account !""",
		"Failed": "Payment Verification Failed!! Your Payment is currently under review !",
		"Refunded": "Your payment has been refunded and might take some time to reflect in your account !!",
		"Expired": "The Reference ID provided has been expired. Please start a new payment !"
	}

	return status_message[status]


def verify_payment_and_run_callbacks(razorpay_log_object):
	api_secret = get_decrypted_password(
		"Razorpay Settings", razorpay_log_object.razorpay_setting, fieldname="api_secret"
	)
	# sending a request to get the payment link entity to get "notes" key
	response = RazorpayPayment(
		frappe.db.get_value("Razorpay Settings", razorpay_log_object.razorpay_setting, "api_key"),
		api_secret,
		ignore_validation=True
	).get_or_create_payment_link(payment_link_id=frappe.form_dict["razorpay_payment_link_id"])

	if not RazorpayPayment.verify_payment_signature(
		api_secret,
		**frappe.form_dict
	):
		razorpay_log_object.status = "Failed"
		if frappe.db.get_value(
			"Razorpay Settings", razorpay_log_object.razorpay_setting, "enable_auto_refunds"
		):
			# this will automatically allow scheduler to pick this up in its next iteration
			razorpay_log_object.status = "Refund"

		on_faliure = response["notes"]["on_faliure"]
		if on_faliure:
			frappe.get_attr(on_faliure)()

	else:
		razorpay_log_object.status = "Paid"
		on_success = response["notes"]["on_success"]
		if on_success:
			frappe.get_attr(on_success)()
