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
			"red",
			redirect_to
		)

		return

	title = "Payment Verification Status"

	if is_handleable_status(context, log.status, title, redirect_to):
		return

	log.status = "Paid"
	message = "Payment Verification Successfull!!"
	indicator = "green"
	if not RazorpayPayment.verify_payment_signature(
		get_decrypted_password("Razorpay Settings", log.razorpay_setting, fieldname="api_secret"),
		**frappe.form_dict
	):
		log.status = "Refund"
		message = "Payment Verification Failed!! Any amount deducted will get refunded back!"
		indicator = "red"

	log.payment_id = frappe.form_dict["razorpay_payment_id"]
	log.save(ignore_permissions=True)

	handle_context(
		context,
		title,
		message,
		indicator,
		json.loads(log.payload).get("redirect_to", "/")
	)


def handle_context(ctx, title, message, indicator, redirect_to):
	ctx.title = title
	ctx.message = message
	ctx.indicator = indicator
	ctx.redirect_to = redirect_to


def is_handleable_status(ctx, status, title, redirect_to):
	if status == "Created":
		return False

	elif status == "Paid":
		handle_context(
			ctx,
			title,
			"The Status has already been verified and the Payment was Successful!",
			"green",
			redirect_to
		)

	elif status =="Refund":
		handle_context(
			ctx,
			title,
			"Your Payment is being Refunded. Please wait for sometime for it to be reflected in your account!",
			"green",
			redirect_to
		)

	else:
		# expired
		handle_context(
			ctx,
			"Expired Reference ID",
			"The Reference ID provided has been expired. Please start a new payment!",
			"red",
			redirect_to
		)

	return True
