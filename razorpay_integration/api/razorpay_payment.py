# frappe imports
import frappe

# third party imports
import hmac
import razorpay
import requests
import hashlib
from functools import partial
from typing import Callable
from uuid import uuid4


'''
TODO:
	- payment links
	- subscriptions
	- refunds

Flow:
	- Everthing starts with a payment link
	- Then payment is initiated on that link

For every payment link created we get an order id and payment link id
When the payment is made successfully on the payment link, we get the payment id

NOTE: Razorpay's wrapper library doesn't have the implementation for:
	- payment link (in v1.2.0)
	- fetching all customers (not even in master)
'''


class RazorpayPayment:
	def __init__(self, api_key: str, api_secret: str):
		self.api_key = api_key
		self.api_secret = api_secret
		self.base_api_url = "https://api.razorpay.com/v1/"
		self.validate_razorpay_creds()

		# only initialize razorpay's client if the validation succeeds
		self.rzp_client = razorpay.Client(auth=(api_key, api_secret))


	def validate_razorpay_creds(self):
		return handle_api_response(
			partial(
				requests.get,
				self.base_api_url + "customers?count=1",
				auth=(self.api_key, self.api_secret),
				headers={
					"content-type": "application/json"
				}
			)
		)


	def _create_payment_link(self, **kwargs):
		# ref: https://razorpay.com/docs/api/payment-links/#create-payment-link
		'''
		Request params for creating payment link:
			- amount (required) INT
			- currency STRING
			- description STRING : A brief description of the Payment Link. (max 2048 characters)
			- reference_id STRING : Reference number tagged to a Payment Link. Must be a unique number for each Payment Link. (max 40 characters)
			- reminder_enable BOOLEAN : Used to send reminders for the Payment Link.
			- customer JSON_OBJ
				- name STRING
				- email STRING
				- phone STRING
			- expire_by INT : Timestamp, in Unix, at which the Payment Link will expire (default is 6 months from creation)
			- notify JSON_OBJ
				- sms BOOLEAN : Razorpay will handle the notification
				- email BOOLEAN : Razorpay will handle the notification
			- callback_url STRING : Adds a redirect URL to the Payment Link. Once customers completes the payment, they are redirected to the specified URL.
				- ref: https://razorpay.com/docs/api/payment-links/#using-callback_url-parameter
			- callback_method (required if `callback_url` is provided) STRING
			- upi_link BOOLEAN : For creating UPI Payment Link

		Further customizations:
			- ref: https://razorpay.com/docs/api/payment-links/customise/
		'''

		if not kwargs.get("amount"):
			frappe.throw(
				frappe._("Amount (INT) is required for creating a payment link !")
			)

		# convert rupee to paise
		# razorpay takes amount precision upto 2 places
		kwargs["amount"] *= 100

		return handle_api_response(
			partial(
				requests.post,
				self.base_api_url + f"{kwargs.get('api_endpoint')}",
				auth=(self.api_key, self.api_secret),
				json={
					"amount": kwargs["amount"],
					"callback_url": kwargs.get("callback_url", ""),
					"callback_method": "get" if kwargs.get("callback_url") else "",
					"currency": "INR",
					"customer": {
						"name": kwargs.get("payer_name", ""),
						"email": kwargs.get("payer_email", ""),
						"phone": kwargs.get("payer_phone", "")
					},
					"description": kwargs.get("description", ""),
					"expire_by": kwargs.get("expire_by", 0),
					"notify": {
						"sms": kwargs.get("notify_via_sms", False),
						"email": kwargs.get("notify_via_email", False)
					},
					"reference_id": kwargs.get("reference_id", str(uuid4())), # use this ref id in razorpay log
					"reminder_enable": kwargs.get("reminder_enable", False)
				},
				headers={
					"Content-type": "application/json"
				}
			)
		)


	def get_or_create_payment_link(
		self,
		payment_link_id: str="",
		api_endpoint: str="payment_links",
		**kwargs
	):

		if payment_link_id:
			#ref: https://razorpay.com/docs/api/payment-links/#specific-payment-links-by-id
			return handle_api_response(
				partial(
					requests.get,
					self.base_api_url + f"{api_endpoint}/{payment_link_id}",
					auth=(self.api_key, self.api_secret),
					headers={
						"content-type": "application/json"
					}
				)
			)

		kwargs.update(dict(api_endpoint=api_endpoint))
		return self._create_payment_link(**kwargs)


	def get_payment(self, payment_id: str):
		if not payment_id:
			frappe.throw(
				frappe._(
					"Please Provide Payment ID "
					"for fetching the respective payment !"
				)
			)

		return handle_api_response(
			partial(self.rzp_client.payment.fetch, payment_id)
		)


	def refund_payment(self, payment_id: str, refund_amt: int):
		# NOTE: Refund amount should be less than/equal to the payment amount
		if not payment_id:
			frappe.throw(
				frappe._(
					"Please Provide Payment ID for which the amount needs to be refunded !"
				)
			)

		if not refund_amt:
			# refund is done in full by default
			_func = partial(self.rzp_client.payment.refund, payment_id)
		else:
			_func = partial(self.rzp_client.payment.refund, payment_id, refund_amt)

		return handle_api_response(_func)


	def verify_payment_signature(
		self,
		razorpay_payment_link_id: str,
		razorpay_payment_link_reference_id: str,
		razorpay_payment_link_status: str,
		razorpay_payment_id: str,
		razorpay_signature: str,
		raise_err: bool=False
	):
		message = razorpay_payment_link_id + "|" + \
			razorpay_payment_link_reference_id + "|" + \
			razorpay_payment_link_status + "|" + razorpay_payment_id
		secret = bytes(self.api_secret, "utf-8")
		msg = bytes(message, "utf-8")

		if not hmac.compare_digest(
			hmac.new(key=secret, msg=msg, digestmod=hashlib.sha256).hexdigest(),
			razorpay_signature
		):
			if raise_err:
				frappe.throw(
					frappe._("Razorpay Signature Verification Failed")
				)

			return False

		return True



def handle_api_response(_func: Callable):
	if not callable(_func):
		return

	# putting try except here to log razorpay's wrapper errors
	try:
		response = _func()
	except Exception as e:
		frappe.log_error(e)
		frappe.throw(
			frappe._("Something Bad Happened !")
		)

	if isinstance(response, requests.Response):
		response = response.json()

		# to get api's errors
		if response.get("error"):
			frappe.log_error(response["error"])
			frappe.throw(
				frappe._(
					response["error"].get("code") +
					": " +
					response["error"].get("description")
				)
			)

	return response
