import frappe
from frappe.utils.password import get_decrypted_password

from functools import wraps

from razorpay_integration.api import RazorpayPayment


def handle_get_context(fn):
	if not frappe.form_dict.get("razorpay_payment_link_reference_id"):
		redirect_handler("Information is missing", "Link/URL is incomplete!")

	@wraps(fn)
	def wrapper(context):
		try:
			log = frappe.get_doc("Razorpay Payment Log", frappe.form_dict["razorpay_payment_link_reference_id"])
		except frappe.DoesNotExistError:
			redirect_handler("Invalid Reference ID", "The reference ID does not exist !")

		status = None
		if log.status == "Created":
			status = verify_payment_and_run_callbacks(log)

		return fn(context, log, status)

	return wrapper


def redirect_handler(title: str, message: str):
	frappe.redirect_to_message(
		frappe._(title), frappe._(message)
	)
	frappe.local.flags.redirect_location = frappe.local.response.location

	raise frappe.Redirect


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
		status = "Failed"

		if frappe.db.get_value(
			"Razorpay Settings", razorpay_log_object.razorpay_setting, "enable_auto_refunds"
		):
			# this will automatically allow scheduler to pick this up in its next iteration
			status = "Refund"

		on_faliure = response["notes"]["on_faliure"]
		if on_faliure:
			frappe.get_attr(on_faliure)()

	else:
		status = "Paid"
		on_success = response["notes"]["on_success"]
		if on_success:
			frappe.get_attr(on_success)()

	return status