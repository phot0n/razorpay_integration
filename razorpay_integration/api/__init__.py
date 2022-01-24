# frappe imports
import frappe
from razorpay_integration.utils import add_to_epoch, get_epoch_time

# standard imports
import hmac
import hashlib
import requests
from functools import partial
from typing import Callable, Dict


'''
TODO (Plan):
	- payment links
	- refunds (partial/full)
	- subscriptions

NOTE(s):
1. Any amount passed on to the api should be an int and
	razorpay's api only supports upto 2 places of precision
	Example:
		20.02 should be passed as 2002,
		20.00 should be passed as 2000

2. Razorpay's python wrapper doesn't utilize the full potential (and our usecases) of
	their api hence a custom wrapper
'''

BASE_API_URL = "https://api.razorpay.com/v1/"


class RazorpayPayment:
	def __init__(self, api_key: str, api_secret: str):
		self.auth = (api_key, api_secret)
		self.headers = {
			"content-type": "application/json"
		}


	@staticmethod
	def validate_razorpay_creds(api_key: str, api_secret: str):
		return handle_api_response(
			partial(
				requests.get,
				BASE_API_URL + "customers?count=1",
				auth=(api_key, api_secret),
				headers={
					"content-type": "application/json"
				}
			)
		)


	@staticmethod
	def verify_payment_signature(
		api_secret: str,
		*,
		razorpay_payment_link_id: str,
		razorpay_payment_link_reference_id: str,
		razorpay_payment_link_status: str,
		razorpay_payment_id: str,
		razorpay_signature: str,
		raise_err: bool=False
	):
		message = "|".join(
			(
				razorpay_payment_link_id,
				razorpay_payment_link_reference_id,
				razorpay_payment_link_status,
				razorpay_payment_id
			)
		)

		secret = bytes(api_secret, "utf-8")
		msg = bytes(message, "utf-8")

		if not hmac.compare_digest(
			hmac.new(key=secret, msg=msg, digestmod=hashlib.sha256).hexdigest(),
			razorpay_signature
		):
			# if this fails we can say the payment failed
			if raise_err:
				frappe.throw(
					frappe._("Razorpay Payment Signature Verification Failed")
				)

			return False

		return True


	def _create_payment_link(
		self,
		amount: int,
		payer_name: str,
		api_endpoint: str,
		*,
		callback_url: str="",
		description: str="",
		expire_by: int=0,
		reference_id: str="",
		payer_email: str="",
		payer_phone: str="",
		notes: Dict={},
		**kwargs
	):
		'''
		ref: https://razorpay.com/docs/api/payment-links/#create-payment-link
		'''

		if amount < 1:
			frappe.throw(
				frappe._("Sufficient amount not provided to start a transaction !")
			)

		if not payer_name:
			frappe.throw(
				frappe._("Customer's name is required!")
			)

		if expire_by and expire_by <= get_epoch_time():
			frappe.throw(
				frappe._("Expiry time of Payment link should be atleast 15 mins in the future!!")
			)

		return handle_api_response(
			partial(
				requests.post,
				BASE_API_URL + api_endpoint,
				auth=self.auth,
				json={
					"amount": amount,
					"callback_url": callback_url or frappe.utils.get_url("razorpay_payment_status"),
					"callback_method": "get",
					"currency": "INR",
					"customer": {
						"name": payer_name,
						"email": payer_email,
						"phone": payer_phone
					},
					"description": description,
					# min time allowed for expiry of every payment link is around 15 mins
					"expire_by": expire_by or add_to_epoch(905),
					"notify": {
						"sms": kwargs.get("notify_via_email", False),
						"email": kwargs.get("notify_via_sms", False)
					},
					# used as reference id in razorpay log
					"reference_id": reference_id,
					# anything can be put in this as a key value pair
					"notes": notes
				},
				headers=self.headers
			)
		)


	def get_or_create_payment_link(
		self,
		*,
		payment_link_id: str="",
		**kwargs
	):
		api_endpoint = "payment_links"

		if payment_link_id:
			#ref: https://razorpay.com/docs/api/payment-links/#specific-payment-links-by-id

			return handle_api_response(
				partial(
					requests.get,
					BASE_API_URL + f"{api_endpoint}/{payment_link_id}",
					auth=self.auth,
					headers=self.headers
				)
			)

		return self._create_payment_link(api_endpoint=api_endpoint, **kwargs)


	def fetch_payment_details(self, payment_id: str):
		if not payment_id:
			frappe.throw(
				frappe._(
					"Please Provide Payment ID "
					"for fetching the respective payment !"
				)
			)

		return handle_api_response(
			partial(
				requests.get,
				BASE_API_URL + f"payments/{payment_id}",
				auth=self.auth,
				headers=self.headers
			)
		)


	def refund_payment(self, payment_id: str, refund_amt: int=0):
		# NOTE: Refund amount should be less than/equal to the payment amount
		# if the refund amount is not provided, a full refund is initiated
		if not payment_id:
			frappe.throw(
				frappe._(
					"Please Provide Payment ID " +
					"for which the amount needs to be refunded !"
				)
			)

		json = {"amount": refund_amt, "speed": "optimum"} if (
			refund_amt
		) else {"speed": "optimum"}

		return handle_api_response(
			partial(
				requests.post,
				BASE_API_URL + f"payments/{payment_id}/refund",
				auth=self.auth,
				json=json,
				headers=self.headers
			)
		)


	def fetch_refund_details(self, refund_id: str):
		if not refund_id:
			frappe.throw(
				frappe._(
					"Please Provide Refund ID to fetch the refund details"
				)
			)

		return handle_api_response(
			partial(
				requests.get,
				BASE_API_URL + f"refunds/{refund_id}",
				auth=self.auth,
				headers=self.headers
			)
		)



def handle_api_response(_func: Callable):
	if not callable(_func):
		return

	response = _func().json()

	# to get api's errors
	if response.get("error"):
		frappe.log_error(response["error"], title=frappe._("Razorpay API Error"))
		frappe.throw(
			frappe._(
				response["error"].get("description")
			)
		)

	return response
