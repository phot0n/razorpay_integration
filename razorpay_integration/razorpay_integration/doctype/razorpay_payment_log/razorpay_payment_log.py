# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class RazorpayPaymentLog(Document):
	def autoname(self):
		# NOTE: setting a time based hash name so as to avoid collision
		# b/w reference id's used in payment links - as we're not sure if the ref id's
		# should be unique across all accounts or just that account (i'm kinda thinking former)
		self.name = frappe.generate_hash("Razorpay Payment Log", length=40)


@frappe.whitelist()
def update_payment_log_status_to_refund(docname: str) -> None:
	log = frappe.qb.DocType("Razorpay Payment Log")
	frappe.qb.update(
		log
	).set(
		log.status, "Refund"
	).where(
		log.name == docname
	).run()


@frappe.whitelist()
def update_failed_payment_log_status_to_refund() -> str:
	if not frappe.db.exists({
		"doctype": "Razorpay Payment Log",
		"status": "Failed"
	}):
		return "No Failed Payments to add to scheduler"

	log = frappe.qb.DocType("Razorpay Payment Log")
	frappe.qb.update(
		log
	).set(
		log.status, "Refund"
	).where(
		log.status == "Failed"
	).run()

	return """Changed Status to Refund.
		Jobs will be picked up by the hourly scheduler in its next iteration !!"""
