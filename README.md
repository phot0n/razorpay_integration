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

This App installs 2 doctypes - Razorpay Settings & Razorpay Payment Log.

You can store your api_key(s) and api_secret(s) in Razorpay Setting Doctype which also has 2 addtional checkboxes for Creating Payment Gateway and Enabling Auto Refunds.
Razorpay Payment Log Doctype stores all the logs of your payments and is non-editable by users.

For Razorpay Setting:
1. Checking Create Payment Gateway will automatically create a gateway in the Payment Gateway Doctype (or you can manually create it as well by unchecking the checkbox and heading to Payment Gateway List).

2. Checking Enable Auto Refund will add any payment *verification* failure from that razorpay setting to the `refund_payments` scheduled job and will be refunded automatically in the next execution of the job, else if the option is unchecked, the status in the Payment Log will show up as `Failed` and the user can head over to the Payment Log to refund the payment manually and the execution concept will remain the same as with auto refund checked.


There is a single payment verification page which verifies if the hash given by razorpay matches the generated hash and updated the Payment Log.
This page is the default redirect for any generated payment link.

#

## For Developers:

This app acts as a Library of sorts as well and the API class can be imported as
```
from razorpay_integration.api import RazorpayPayment
```
This is a custom wrapper on top of razorpay's api which allows us to create payment links,
issue refunds, fetch payment(s), etc, where you need to provide the `api_key` and `api_secret` to the constructor.

```
rzp = RazorpayPayment("<api_key>", "<api_secret>")
```

### To generate a payment link:
```
rzp.get_or_create_payment_link(amount=1000, payer_name="test")
```
The method `get_or_create_payment_link` accepts only kwargs and the available kwargs can be found at the method definition of [`_create_payment_link`](razorpay_integration/api/__init__.py) where `amount` and `payer_name` are mandatory args

> ```
> NOTE: Any amount passed on to the api should be an INT and razorpay's api only supports upto 2 places of precision
> 	Example:
> 		1. 20.02 should be passed as 2002,
> 		2. 20.00 should be passed as 2000
> ```

You can also create payment link using the utility function directly accessible via
```
from razorpay_integration import get_payment_url
```
This function will create a log for the payment link generated as well and you can pass various keyworded args to the same.
2 kwargs of this function are used for running callbacks i.e `on_success` and `on_failure` which have the same implementation as of hooks. You can attach your method (path) strings to these kwargs and they'll be run on the verification page according to the status of verification.
In this method you can pass your amount as float as it will do the conversion automatically

> NOTE: This function should be used typically for any payment link as it does many things which barebones api wrapper has not been configured to do.

### To issue refund against a payment id:
```
rzp.refund_payment("<payment_id>", <refund_amt>)
```
The refund amount is optional and should be an INT - if the refund amount is not specified then the amount is refunded in full

### To verify if the creds(key-secret) provided are correct:
```
RazorpayPayment.validate_razorpay_creds("<api_key>", "<api_secret>")
```
`validate_razorpay_creds` is a staticmethod hence there is no need to create an object for the RazorpayPayment class

### Cusom Payment Verification Page:

You can also override the default Payment Verification Page by passing a custom url to the `callback_url` kwarg of `get_or_create_payment_link` method. This will redirect users to that custom url instead of the Payment Verification Page thus allowing us to create a custom Payment Verification Page.


#### License

MIT