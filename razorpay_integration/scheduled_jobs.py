import frappe
from frappe.utils.data import flt, cint
from frappe.utils.password import get_decrypted_password

from razorpay_integration.api.razorpay_payment import RazorpayPayment


def refund_payments() -> None:
	logs = frappe.get_all(
		"Razorpay Payment Log",
		filters={
			"status": "Refund",
			"refund_id": "",
			"payment_id": ["!=", ""] # adding this for additional check
		},
		fields=["name", "payment_id", "razorpay_setting", "amount"]
	)

	for log in logs:
		api_key = frappe.db.get_value(
			"Razorpay Settings",
			log.razorpay_setting,
			fieldname=["api_key"]
		)

		response = RazorpayPayment(
			api_key,
			get_decrypted_password(
				"Razorpay Settings",
				log.razorpay_setting,
				fieldname="api_secret"
			)
		).refund_payment(log.payment_id, cint(log.amount))

		frappe.db.set_value(
			"Razorpay Payment Log",
			log.name,
			"refund_id",
			response["id"]
		)
		frappe.db.set_value(
			"Razorpay Payment Log",
			log.name,
			"refund_amount",
			flt(log.amount)
		)


def update_expired_payment_link_status_in_payment_log() -> None:
	pass
