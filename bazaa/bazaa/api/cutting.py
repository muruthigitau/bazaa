import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def create_cutting_list():
    import json

    try:
        # Parse the incoming JSON data
        data = frappe.local.form_dict or {}
        if isinstance(data, str):
            data = json.loads(data)

        # Validate required fields
        required_fields = ["customer_name", "customer_phone"]
        for field in required_fields:
            if not data.get(field):
                frappe.throw(_(f"Missing required field: {field}"))

        # Create the Cutting List document
        cutting_list = frappe.new_doc("Cutting List")
        cutting_list.customer_name = data.get("customer_name")
        cutting_list.customer_email = data.get("customer_email")
        cutting_list.customer_phone = data.get("customer_phone")
        cutting_list.board_type = data.get("board_type")

        # Add child table entries if present
        items = data.get("items", [])
        for item in items:
            cutting_list.append("items", {
                "length": item.get("length"),
                "width": item.get("width"),
                "qty": item.get("qty"),
                "description": item.get("description"),
                "edging_length": item.get("edging_length") or 0,
                "edging_width": item.get("edging_width") or 0,
                "grooves_length": item.get("grooves_length") or 0,
                "grooves_width": item.get("grooves_width") or 0,
            })

        # Insert the document
        cutting_list.insert(ignore_permissions=True)
        cutting_list.submit()
        frappe.db.commit()

        return {
            "status": "success",
            "name": cutting_list.name,
            "message": _("Cutting List created successfully.")
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Cutting List Error")
        return {
            "status": "error",
            "message": str(e)
        }
