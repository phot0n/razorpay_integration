frappe.listview_settings["Razorpay Payment Log"] = {
	onload(listview) {
        listview.page.add_button("Add All Failed Payments To Refund Scheduler", () => {
            frappe.call({
                method: "razorpay_integration.razorpay_integration.doctype." +
				"razorpay_payment_log.razorpay_payment_log.update_failed_payment_log_status_to_refund"
            }).then(r => {
				listview.refresh();
                frappe.msgprint(__(
                    `${r.message}`
                ));
            });
        });
    }
}
