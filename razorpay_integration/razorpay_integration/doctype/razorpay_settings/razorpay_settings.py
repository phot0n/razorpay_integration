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
	def validate(self):
		RazorpayPayment(self.api_key, self.api_secret)

		if self.create_payment_gateway:
			create_payment_gateway(
				self.name,
				settings="Razorpay Settings",
				controller=self.name
			)


	def get_payment_url(self, **kwargs):
		'''
			Required Kwargs:
				- Reference Doctype
				- Reference Docname
				- Amount
		'''

		# NOTE: this is done for local setups otherwise razorpay
		# throws a valdation error for email
		kwargs["payer_email"] = kwargs.get("payer_email", frappe.session.user) if (
				kwargs.get("payer_email", frappe.session.user) not in ("Guest", "Administrator")
			) else ""
		kwargs["payer_name"] = kwargs.get("payer_name", frappe.utils.get_fullname(frappe.session.user))

		log = frappe.get_doc(
			doctype="Razorpay Payment Log",
			status="Created",
			razorpay_setting=self.name,
			reference_doctype=kwargs["reference_doctype"],
			reference_docname=kwargs["reference_docname"],
			description=kwargs.get("description"),
			amount=flt(kwargs["amount"]),
			payload=json.dumps(
				dict(redirect_to=kwargs.get("redirect_to", "/"))
			)
		).insert(ignore_permissions=True)

		# use log name as reference id in payment link
		kwargs["reference_id"] = log.name

		razorpay_response = RazorpayPayment(
			self.api_key,
			get_decrypted_password("Razorpay Settings", self.name, fieldname="api_secret"),
			ignore_validation=True
		).get_or_create_payment_link(**kwargs)

		log.payment_link_id = razorpay_response.get("id")
		log.payment_url = razorpay_response.get("short_url")
		log.valid_till = razorpay_response.get("expire_by")
		log.customer = json.dumps(razorpay_response.get("customer"))
		log.save(ignore_permissions=True)

		return razorpay_response.get("short_url")
