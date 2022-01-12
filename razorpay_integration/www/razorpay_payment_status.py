import frappe
from frappe.utils.password import get_decrypted_password

import json

from razorpay_integration.api.razorpay_payment import RazorpayPayment


def get_context(context):
	if not frappe.form_dict.get("razorpay_payment_link_reference_id"):
		frappe.redirect_to_message(
			frappe._("Information is missing"),
			frappe._("Link/URL is incomplete!")
		)
		frappe.local.flags.redirect_location = frappe.local.response.location

		raise frappe.Redirect

	redirect_to = "/"

	try:
		log = frappe.get_doc("Razorpay Payment Log", frappe.form_dict["razorpay_payment_link_reference_id"])
	except frappe.DoesNotExistError:
		handle_context(
			context,
			"Invalid Reference ID",
			"The reference ID does not exist !",
			redirect_to
		)

		return

	title = "Payment Verification Status"

	if is_handleable_status(context, log.status, title, redirect_to):
		return

	log.status = "Paid"
	message = "Payment Verification Successfull!!"
	if not RazorpayPayment.verify_payment_signature(
		get_decrypted_password("Razorpay Settings", log.razorpay_setting, fieldname="api_secret"),
		**frappe.form_dict
	):
		log.status = "Failed"
		if frappe.db.get_value("Razorpay Settings", log.razorpay_setting, "enable_auto_refunds"):
			log.status = "Refund"

		message = "Payment Verification Failed!! Any amount deducted will get refunded back!"

		# TODO: success redirection and fail redirection

	log.payment_id = frappe.form_dict["razorpay_payment_id"]
	log.save(ignore_permissions=True)

	handle_context(
		context,
		title,
		message,
		json.loads(log.payload).get("redirect_to", "/")
	)


def handle_context(ctx, title, message, redirect_to):
	ctx.title = title
	ctx.message = message
	ctx.redirect_to = redirect_to


def is_handleable_status(ctx, status, title, redirect_to):
	if status == "Created":
		return False

	elif status == "Paid":
		message = "The Status has already been verified and the Payment was Successful!"

	elif status == "Refund":
		message = "Your Payment is being Refunded. " + \
			"Please wait for sometime for it to be reflected in your account!"

	elif status == "Failed":
		message = "Your payment was not verified and is currently under review!"

	elif status == "Refunded":
		message = "Your payment has been refunded and might take some time to reflect in your account!!"

	else:
		# expired
		title = "Expired Reference ID"
		message = "The Reference ID provided has been expired. Please start a new payment!"

	handle_context(
		ctx,
		title,
		message,
		redirect_to
	)

	return True
