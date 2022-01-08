import frappe
from frappe.utils.password import get_decrypted_password

import json

from razorpay_integration.api.razorpay_payment import RazorpayPayment


def get_context(context):
	log = frappe.get_doc("Razorpay Payment Log", frappe.form_dict["razorpay_payment_link_reference_id"])

	log.status = "Paid"
	message = "Payment Verification Successfull!!"
	indicator = "green"
	if not RazorpayPayment.verify_payment_signature(
		get_decrypted_password("Razorpay Settings", log.razorpay_setting, fieldname="api_secret"),
		**frappe.form_dict
	):
		log.status = "Failed"
		message = "Payment Verification Failed!!"
		indicator = "red"

	log.payment_id = frappe.form_dict["razorpay_payment_id"]
	payload = log.payload
	log.payload = None
	log.save()

	context.message = message
	context.indicator = indicator
	context.redirect_to = json.loads(payload)["redirect_to"]
