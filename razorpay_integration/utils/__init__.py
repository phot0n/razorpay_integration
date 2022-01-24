# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

import frappe

import math
import time


def get_epoch_time() -> int:
	# returns the current epoch time
	return math.ceil(time.time())

def add_to_epoch(seconds: int) -> int:
	# adds seconds to the current epoch time
	return get_epoch_time() + seconds

def convert_epoch_to_timestamp(epoch_time: int):
	# converts any given epoch time to human readable datetime
	return time.ctime(epoch_time)

def run_callback(method_string: str, **kwargs):
	"""
	This method follows the concept of hooks
	(infact hooks use the same mechanism in frappe)
	where this will run a function/method from it's string-ed path.
	This method can also pass the params to the method
	though they need to be keyworded.
	"""

	if not method_string:
		return

	try:
		frappe.get_attr(method_string)(**kwargs)
	except Exception as e:
		frappe.log_error(method_string + " : " + e, title=frappe._("Callback Error"))
		frappe.throw(e)
