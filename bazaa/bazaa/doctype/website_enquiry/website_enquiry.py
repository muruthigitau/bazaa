# Copyright (c) 2025, David Gitau and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class WebsiteEnquiry(Document):
    def on_submit(self):
        self.send_enquiry_email()

    def send_enquiry_email(self):
        # Get the default email from Website Settings or your own settings doctype
        default_email = frappe.db.get_single_value("Sales Settings", "default_email")
        if not default_email:
            frappe.msgprint("No default enquiry email configured in Website Settings.")
            return

        # Construct the message
        message = f"""
        <h3>New Website Enquiry Submitted</h3>
        <p><strong>Name:</strong> {self.first_name} {self.last_name or ""}</p>
        <p><strong>Email:</strong> {self.email}</p>
        <p><strong>Phone:</strong> {self.phone or "N/A"}</p>
        <p><strong>Message:</strong><br>{self.message}</p>
        """

        # Send the email
        frappe.sendmail(
            recipients=[default_email],
            subject=f"New Enquiry: {self.name}",
            message=message,
            delayed=False  # Send immediately
        )

        frappe.msgprint(f"Enquiry email sent to {default_email}")
