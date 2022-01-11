// Copyright (c) 2021, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Razorpay Payment Log', {
	refresh: function(frm) {
		if (frm.doc.status === "Failed") {
			frm.add_custom_button('Refund Payment', () => {
				// the scheduler job will pick this up in the next cycle
				frm.set_value("status", "Refund");
				frm.save();
			})
		}
	}
});
