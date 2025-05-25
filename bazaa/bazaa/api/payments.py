import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def initiate_payment_request():
    frappe.set_user("Guest")
    frappe.flags.ignore_permissions = True

    import json
    data = frappe.local.form_dict
    if not data:
        try:
            data = json.loads(frappe.request.data or '{}')
        except Exception:
            data = {}

    id = data.get("id")
    amount = data.get("amount")
    phone = data.get("phone")

    if not id or not amount or not phone:
        frappe.throw(_("Missing required fields: id, amount, or phone."))

    # Get Sales Order and Customer
    sales_order = frappe.get_doc("Sales Order", id)
    customer = sales_order.customer

    # Cancel existing unpaid submitted requests for same Sales Order
    existing_requests = frappe.get_all(
        "Payment Request",
        filters={
            "reference_doctype": "Sales Order",
            "reference_name": id,
            "docstatus": 1  # Submitted
        },
        fields=["name", "grand_total", "status"]
    )

    for req in existing_requests:
        if req.status != "Paid":
            try:
                pr_doc = frappe.get_doc("Payment Request", req.name)
                mpesa_requests = frappe.get_all(
                    "Mpesa Express Request",
                    filters={"reference_name": req.name, "docstatus": 1, "reference_doctype": "Payment Request"},
                    fields=["name"]
                )
                for mpesa in mpesa_requests:
                    try:
                        mpesa_doc = frappe.get_doc("Mpesa Express Request", mpesa.name)
                        mpesa_doc.flags.ignore_permissions = True
                        mpesa_doc.cancel()
                    except Exception as e:
                        frappe.log_error(f"Failed to cancel Mpesa Express Request {mpesa.name}: {str(e)}", "MPESA Cancel Error")

                
                pr_doc.flags.ignore_permissions = True
                pr_doc.cancel()
            except Exception as e:
                frappe.log_error(f"Failed to cancel Payment Request {req.name}: {str(e)}", "Cancel Payment Request Error")

    # Get settings
    sales_settings = frappe.get_single("Sales Settings")
    mode_of_payment = sales_settings.default_mode_of_payment
    gateway_account = sales_settings.default_gateway_account
    gateway = sales_settings.default_payment_gateway

    # Create new Payment Request
    pr = frappe.get_doc({
        "doctype": "Payment Request",
        "payment_gateway": gateway,
        "payment_gateway_account": gateway_account,
        "payment_request_type": "Inward",
        "party_type": "Customer",
        "party": customer,
        "reference_doctype": "Sales Order",
        "reference_name": id,
        "grand_total": amount,
        "currency": sales_order.currency,
        "mode_of_payment": mode_of_payment or "Cash",
        "email_to": sales_order.get("contact_email") or "test@example.com",
        "phone_number": phone,
    })

    pr.flags.ignore_permissions = True
    pr.insert(ignore_permissions=True)
    pr.submit()

    return {
        "payment_request": pr.name,
        "status": pr.status,
        "amount": pr.grand_total,
        "payment_url": pr.payment_url if hasattr(pr, "payment_url") else None
    }


@frappe.whitelist(allow_guest=True)
def check_status(id):
    frappe.set_user("Guest")
    frappe.flags.ignore_permissions = True

    if not id:
        frappe.throw(_("Payment Request ID is required."))

    # Get Payment Request
    pr = frappe.get_doc("Payment Request", id)

    if not pr:
        frappe.throw(_("Payment Request not found."))

    # Check status
    status = pr.status
    if status == "Paid":
        return {
            "status": "success",
            "message": _("Payment has been completed successfully."),
            "payment_request": pr.name
        }
    else:
        return {
            "status": "pending",
            "message": _("Payment is still pending."),
            "payment_request": pr.name
        }
        
@frappe.whitelist(allow_guest=True)
def reinitiate_stkpush(id):
    frappe.set_user("Guest")
    frappe.flags.ignore_permissions = True

    if not id:
        frappe.throw(_("Payment Request ID is required."))

    # Get Payment Request
    payment_request = frappe.get_doc("Payment Request", id)
    
    if not payment_request:
        frappe.throw(_("Payment Request not found."))

    # Check if payment request is already paid
    if payment_request.status == "Paid":
        return {
            "status": "error",
            "message": _("Payment has already been completed."),
            "payment_request": payment_request.name
        }

    # Get associated Mpesa Express Request
    mpesa_requests = frappe.get_all(
        "Mpesa Express Request",
        filters={
            "reference_doctype": "Payment Request",
            "reference_name": payment_request.name,
            "docstatus": 1  # Submitted
        },
        order_by="creation desc",
        limit_page_length=1
    )

    if not mpesa_requests:
        return {
            "status": "error",
            "message": _("No Mpesa Express Request found for this payment."),
            "payment_request": payment_request.name
        }

    mpesa_request = frappe.get_doc("Mpesa Express Request", mpesa_requests[0].name)

    try:
        # Reinitiate STK push
        result = mpesa_request.send_stk_push()
        
        return {
            "status": "success",
            "message": _("STK Push reinitiated successfully."),
            "payment_request": payment_request.name,
            "mpesa_request": mpesa_request.name,
            "result": result
        }
    except Exception as e:
        frappe.log_error(f"Failed to reinitiate STK Push: {str(e)}", "STK Push Reinitiation Error")
        return {
            "status": "error",
            "message": _("Failed to reinitiate STK Push. Please try again."),
            "payment_request": payment_request.name,
            "error": str(e)
        }