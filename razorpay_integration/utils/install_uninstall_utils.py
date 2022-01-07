import frappe

def add_razorpay_section_in_web_form() -> None:
	# Installs a section for Razorpay in Web Form DocType

	web_form_doctype = frappe.get_doc("DocType","Web Form")
	web_form_doctype.extend("fields", [
		{
			"label": "Razorpay",
			"fieldtype": "Section Break",
			"fieldname": "sb_razorpay",
			"collapsible": 1
		},
		{
			"label": "Accept Razorpay",
			"fieldtype": "Check",
			"fieldname": "accept_razorpay",
			"default": 1
		},
		{
			"label": "Razorpay Setting",
			"fieldtype": "Link",
			"fieldname": "razorpay_setting",
			"options": "Razorpay Settings",
			"depends_on": "accept_razorpay"
		},
		{
			"label": "Amount",
			"fieldtype": "Currency",
			"fieldname": "razorpay_amount",
			"depends_on": "eval:doc.accept_razorpay && !doc.accept_razorpay_amount_field",
		},
		{
			"label": "Amount Field",
			"fieldtype": "Select",
			"fieldname": "razorpay_amount_field",
			"depends_on": "eval:doc.accept_razorpay && doc.accept_razorpay_amount_field"
		},
		{
			"label": "",
			"fieldtype": "Column Break",
			"fieldname": "cb_razorpay"
		},
		{
			"label": "Razorpay Amount Based on Field",
			"fieldtype": "Check",
			"fieldname": "accept_razorpay_amount_field",
			"default": 0,
			"depends_on": "accept_razorpay"
		},
		{
			"label": "Currency",
			"fieldtype": "Data",
			"default": "INR",
			"read_only": 1,
			"fieldname": "razorpay_currency",
			"depends_on": "accept_razorpay"
		},
		# TODO: not very sure about this
		{
			"label": "Callback Redirect (On Success)",
			"fieldtype": "Data",
			"fieldname": "razorpay_callback_redirect",
			"depends_on": "accept_razorpay",
			"options": "URL"
		}
	])

	web_form_doctype.save()


def remove_razorpay_section_from_web_form() -> None:
	# Removes Razorpay section from Web Form DocType

	web_form_doctype = frappe.get_doc("DocType","Web Form")
	razorpay_fieldnames = (
		"sb_razorpay",
		"accept_razorpay",
		"accept_razorpay_amount_field",
		"razorpay_setting",
		"razorpay_amount",
		"razorpay_amount_field",
		"cb_razorpay",
		"razorpay_currency",
		"razorpay_callback_redirect"
	)

	for fieldname in razorpay_fieldnames:
		for field in web_form_doctype.fields:
			if field.fieldname == fieldname:
				web_form_doctype.fields.remove(field)
				break

	web_form_doctype.save()
