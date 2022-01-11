// Copyright (c) 2021, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on("Razorpay Payment Log", {
	refresh: function(frm) {
		if (["Failed", "Paid"].includes(frm.doc.status)) {
			frm.add_custom_button("Refund Payment", () => {
				frappe.confirm(
					__("Are you sure you want to proceed?"), () => {
						frappe.call({
							method: "razorpay_integration.razorpay_integration.doctype." +
									"razorpay_payment_log.razorpay_payment_log.update_payment_log_status_to_refund",
							args: {
								"docname": frm.doc.name
							},
							callback: function(r){
								frm.reload_doc();
							}
						}).then(() => {
							frappe.show_alert(
								__("The status has been changed and will be picked up by the scheduler for refund!!"),
								5
							);
						});
					});
				});
			}
		}
	}
);
