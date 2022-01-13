import frappe

import json

from razorpay_integration.api.context_handler import handle_get_context


@handle_get_context
def get_context(context, razorpay_log_object, status):
	title = "Payment Verification Status"

	if not status:
		# status was alread set and user has revisited the page
		if razorpay_log_object.status == "Expired":
			title = "Expired Reference ID"

		update_context_obj(
			context,
			title,
			get_message_based_on_status(razorpay_log_object.status),
			"/"
		)
		return

	razorpay_log_object.status = status
	razorpay_log_object.payment_id = frappe.form_dict["razorpay_payment_id"]
	razorpay_log_object.save(ignore_permissions=True)

	# not really working without explicit commit
	frappe.db.commit()

	update_context_obj(
		context,
		title,
		get_message_based_on_status(razorpay_log_object.status),
		json.loads(razorpay_log_object.payload).get("redirect_to", "/")
	)


def update_context_obj(ctx, title, message, redirect_to):
	ctx.title = title
	ctx.message = message
	ctx.redirect_to = redirect_to


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
