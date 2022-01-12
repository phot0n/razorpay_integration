import frappe
from frappe.utils.data import flt, cint
from frappe.utils.password import get_decrypted_password

from razorpay_integration.api.razorpay_payment import RazorpayPayment
from razorpay_integration.utils import get_epoch_time


def refund_payments() -> None:
	log_doctype = "Razorpay Payment Log"
	setting_doctype = "Razorpay Settings"

	logs = frappe.get_all(
		log_doctype,
		filters={
			"status": "Refund",
			"refund_id": "",
			"payment_id": ["!=", ""] # adding this for additional check
		},
		fields=["name", "payment_id", "razorpay_setting", "amount"]
	)

	log_doctype = frappe.qb.DocType("Razorpay Payment Log")
	for log in logs:
		api_key = frappe.db.get_value(
			setting_doctype,
			log.razorpay_setting,
			fieldname=["api_key"]
		)

		try:
			response = RazorpayPayment(
				api_key,
				get_decrypted_password(
					setting_doctype,
					log.razorpay_setting,
					fieldname="api_secret"
				),
				ignore_validation=True
			).refund_payment(log.payment_id, cint(log.amount * 100))
		except Exception:
			continue

		frappe.qb.update(
			log_doctype
		).set(
			log_doctype.refund_id, response["id"]
		).set(
			log_doctype.refund_amount, flt(log.amount)
		).where(
			log_doctype.name == log.name
		).run()


def update_payment_log_status_in_payment_log_for_expired_links() -> None:
	log_doctype = frappe.qb.DocType("Razorpay Payment Log")

	frappe.qb.update(
		log_doctype
	).set(
		log_doctype.status, "Expired"
	).where(
		(log_doctype.status == "Created") &
		(log_doctype.valid_till[1:get_epoch_time()])
	).run()
