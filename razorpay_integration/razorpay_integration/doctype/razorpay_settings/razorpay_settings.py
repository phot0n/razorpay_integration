# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

# frappe imports
import frappe
from frappe.integrations.utils import create_payment_gateway
from frappe.model.document import Document
from frappe.utils.data import flt
from frappe.utils.password import get_decrypted_password

# standard imports
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

		if self.create_payment_gateway:
			create_payment_gateway(
				self.name,
				settings="Razorpay Settings",
				controller=self.name
			)


	def get_payment_url(self, **kwargs):
		kwargs["payer_email"] = frappe.session.user if (
			frappe.session.user not in ("Guest", "Administrator")
		) else ""
		kwargs["payer_name"] = frappe.utils.get_fullname(frappe.session.user)

		razorpay_response = RazorpayPayment(
			self.api_key,
			get_decrypted_password("Razorpay Settings", self.name, fieldname="api_secret")
		).get_or_create_payment_link(**kwargs)

		# log details in razorpay log
		frappe.get_doc(
			doctype="Razorpay Payment Log",
			reference_id=razorpay_response.get("reference_id"),
			status="Created",
			razorpay_setting=self.name,
			description=razorpay_response.get("description"),
			currency=razorpay_response.get("currency"),
			amount=flt(razorpay_response.get("amount") / 100), # razorpay returns the amount as it's sent to it
			payment_link_id=razorpay_response.get("id"),
			payment_url=razorpay_response.get("short_url"),
			valid_till=razorpay_response.get("expire_by"),
			customer=json.dumps(razorpay_response.get("customer")),
			payload=json.dumps(
				dict(redirect_to=kwargs.get("redirect_to", "/"))
			)
		).insert(ignore_permissions=True)

		return razorpay_response.get("short_url")
