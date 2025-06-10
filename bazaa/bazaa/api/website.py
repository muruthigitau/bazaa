import frappe
from frappe import _
import json

@frappe.whitelist(allow_guest=True)
def equiry():
    try:
        # Parse incoming data
        data = frappe.local.form_dict or {}
        if isinstance(data, str):
            data = json.loads(data)

        # Required fields
        first_name = data.get("first_name")
        message = data.get("message")

        if not first_name or not message:
            return {"status": "error", "message": "First name and message are required."}

        # Create new Website Enquiry document
        enquiry = frappe.get_doc({
            "doctype": "Website Enquiry",
            "first_name": first_name,
            "last_name": data.get("last_name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "message": message,
        })

        # Insert and submit the document
        enquiry.insert(ignore_permissions=True)
        enquiry.submit()

        return {"status": "success", "message": "Enquiry submitted successfully.", "enquiry_id": enquiry.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Website Enquiry API Error")
        return {"status": "error", "message": "Failed to submit enquiry.", "details": str(e)}
