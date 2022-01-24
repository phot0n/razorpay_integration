# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

# frappe imports
from frappe.integrations.utils import create_payment_gateway
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password

# api imports
from razorpay_integration.api import RazorpayPayment


class RazorpaySettings(Document):
	def on_update(self):
		RazorpayPayment.validate_razorpay_creds(
			self.api_key,
			get_decrypted_password("Razorpay Settings", self.name, fieldname="api_secret")
		)

		if self.create_payment_gateway:
			create_payment_gateway(
				self.name,
				settings="Razorpay Settings",
				controller=self.name
			)


	def get_payment_url(self, **kwargs):
		from razorpay_integration import get_payment_url
		return get_payment_url(self.name, **kwargs)
