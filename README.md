## Razorpay Integration

Razorpay Integration for Frappe

#

## Features

1. Payment Links
2. Refunds (Full)

#

## Get/Install App

```
bench get-app phot0n/razorpay_integration
bench --site <sitename> install-app razorpay_integration
```

#

## Usage/Info

This App installs 2 doctypes to any site - Razorpay Settings & Razorpay Payment Log.

You can store your api_key(s) and api_secret(s) in Razorpay Settings Doctype which also has 2 addtional checkboxes for Creating Payment Gateway and Enabling Auto Refunds.

Razorpay Payment Log Doctype stores all the logs of your payments and is non-editable by users.

In Razorpay Settings:
1. Checking Create Payment Gateway will automatically create a gateway in the Payment Gateway Doctype (or you can manually create it as well by unchecking the checkbox and heading to Payment Gateway List) - if you're using previous version of frappe it is advised to check this by default as the Payment Gateway Doctype is *locked* and any change is *non-permissible*.

2. Checking Enable Auto Refund will add any payment *verification* failures from that razorpay setting to the Refund Payments scheduled job and will be refunded automatically in the next execution of the job, else if the option is unchecked, the status in the Payment Log will show up as `Failed` and the user can head over to the Payment Log to refund the payment manually and the execution concept will remain the same as with auto refund checked.

There is also a single payment verification page which verifies if the integrity hash given by razorpay matches the generated hash and updates the Payment Log with the relevant status and payment id of the payment.
This page is the default redirect for any generated payment link.

#

## For Developers:

This app acts as a Library of sorts as well and the API can be imported as
```
from razorpay_integration.api import RazorpayPayment
```
This is a custom wrapper on top of razorpay's api which allows us to create payment links,
issue refunds, fetch payment(s), etc, where you need to provide the `api_key` and `api_secret` to it's constructor.

```
rzp = RazorpayPayment("<api_key>", "<api_secret>")
```

### Generation of payment link

```
rzp.get_or_create_payment_link(amount=1000, payer_name="test")
```
The method `get_or_create_payment_link` accepts only kwargs and the available kwargs can be found at the method definition of [`_create_payment_link`](razorpay_integration/api/__init__.py) where `amount` and `payer_name` are mandatory args.

> ```
> NOTE: Any amount passed on to the api should be an INT and razorpay's api only supports upto 2 places of precision
> 	Example:
> 		1. 20.02 should be passed as 2002,
> 		2. 20.00 should be passed as 2000
> ```

An alternate/better way to create payment link(s) is by using the utility function accessible via
```
from razorpay_integration import get_payment_url
```
This function will create a log for the payment link generated as well and we can pass various keyworded args to the same.
2 kwargs of this function are used for running callbacks i.e `on_success` and `on_failure` which have the same implementation as that of hooks. We can attach our method (path) strings to these kwargs and they'll run on the verification page according to the status of verification.
In this utility, we can pass our amount as float (or how we see it) as it will do the conversion automatically

> NOTE: This function should be used typically for any payment link generation as it does many things which the api wrapper has not been configured to do.

Every Payment Link generated will expire within 15 mins of it's creation which is set as default but can be overidden by passing `expire_by` kwarg to either the api method or the utility function. The value to be passed in this kwarg is the unix epoch time (INT) by the time you want your payment link to expire.

> NOTE: Razorpay doesn't allow less than 15 mins of expiry time for any payment link.

### Issue refund against a payment id

```
rzp.refund_payment("<payment_id>", <refund_amt>)
```
The refund amount is optional and should be an INT - if the refund amount is not specified then the amount is refunded in full.
We get the payment ID when a user *completes* the payment.

### Verification of creds(key-secret)

```
RazorpayPayment.validate_razorpay_creds("<api_key>", "<api_secret>")
```

### To verify if the payment hash is valid:

```
RazorpayPayment.verify_payment_signature(
	"<api_secret>",
	"<razorpay_payment_link_id>",
	"<razorpay_payment_link_reference_id>",
	"<razorpay_payment_link_status>",
	"<razorpay_payment_id>",
	"<razorpay_signature>"
)
```
These params (except `api_secret`) are provided by razorpay when a payment has been done for verifying the integrity of the signature provided.

> NOTE: `validate_razorpay_creds` and `verify_payment_signature` are staticmethods hence there is no need to create an object of RazorpayPayment class for them

### Custom Payment Verification Page

We can also override the default Payment Verification Page by passing a custom url to the `callback_url` kwarg of `get_or_create_payment_link` method (or to the `get_payment_url` utility function). This will redirect users to that custom url instead of the Payment Verification Page thus allowing us to create a custom Payment Verification Page.

#

2 Hourly Scheduled Jobs are present for doing things in the background - Refund Payments and Updation of the Payment Log(s) for Expiry of Links
Currently all (full) Refunds are driven through the refund payments scheduled job.

#### License

MIT