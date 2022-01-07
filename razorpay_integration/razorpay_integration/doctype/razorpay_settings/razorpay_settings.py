# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

# frappe imports
import frappe
from frappe.integrations.utils import create_payment_gateway
from frappe.model.document import Document

# third party imports
import json

# api imports
from razorpay_integration.api.razorpay_payment import RazorpayPayment


class RazorpaySettings(Document):
	'''
	What do we need for every setting when being saved:
		- are the api keys working/correct?
	'''
	def validate(self):
		RazorpayPayment(self.api_key, self.api_secret)
		create_payment_gateway(
			self.name,
			settings="Razorpay Settings",
			controller=self.name
		)


	def get_payment_url(self, **kwargs):
		kwargs["reference_id"] = kwargs.pop("order_id")
		kwargs["callback_url"] = kwargs.pop("redirect_to")

		razorpay_response = RazorpayPayment(
			self.api_key,
			self.api_secret
		).get_or_create_payment_link(**kwargs)

		# log details in razorpay log
		frappe.get_doc(
			doctype="Razorpay Payment Log",
			reference_id=razorpay_response.get("reference_id"),
			status="Created",
			reference_doctype=kwargs.get("reference_doctype"),
			reference_docname=kwargs.get("reference_docname"),
			description=razorpay_response.get("description"),
			currency=razorpay_response.get("currency"),
			amount=razorpay_response.get("amount"),
			payment_link_id=razorpay_response.get("id"),
			payment_url=razorpay_response.get("short_url"),
			valid_till=razorpay_response.get("expire_by"),
			customer=json.dumps(razorpay_response.get("customer"))
		).insert(ignore_permissions=True)

		return razorpay_response.get("short_url")
