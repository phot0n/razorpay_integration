# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.integrations.utils import make_get_request
from frappe.model.document import Document

from razorpay_integration.api.razorpay_payment import RazorpayPayment


class RazorpaySettings(Document):
	'''
	What do we need for every setting when being saved:
		- are the api keys working/correct?
	'''
	def validate(self):
		try:
			make_get_request(
				url="https://api.razorpay.com/v1/customers?count=1",
				auth=(
					self.api_key,
					self.api_secret
				)
			)
		except Exception:
			frappe.throw(
				frappe._("API Key and/or API Secret are not correct !")
			)

	def get_payment_link(self, **kwargs):
		razorpay_response = RazorpayPayment(
			self.api_key,
			self.api_secret
		).get_or_create_payment_link(**kwargs)

		# log details in razorpay log
		frappe.get_doc(
			doctype="Razorpay Payment Log",
			reference_id=razorpay_response.get("reference_id"),
			status="Created",
			description=razorpay_response.get("description"),
			currency=razorpay_response.get("currency"),
			amount=razorpay_response.get("amount"),
			payment_link_id=razorpay_response.get("id"),
			payment_url=razorpay_response.get("short_url"),
			valid_till=razorpay_response.get("expire_by"),
			customer=razorpay_response.get("customer")
		).insert(ignore_permissions=True)

		return razorpay_response.get("short_url")
