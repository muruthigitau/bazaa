import frappe


@frappe.whitelist(allow_guest=True)
def create_sales_order():
    import json
    from frappe import throw, _
    
    try:
       
        data = frappe.local.form_dict or {}
        
        items_data = data.pop("items", [])
        
       
        if not data.get("phone"):
            throw(_("Phone number is required to create a customer"))
        
       
        customer_name = create_or_get_customer_by_phone(data)
        
       
        sales_order = frappe.new_doc("Sales Order")
        sales_order.customer = customer_name
        sales_order.delivery_date = frappe.utils.add_days(frappe.utils.nowdate(), 7)
        
       
        default_warehouse = frappe.db.get_single_value("Sales Settings", "default_warehouse")
        if not default_warehouse:
            warehouses = frappe.get_all("Warehouse", limit=1)
            if warehouses:
                default_warehouse = warehouses[0].name
        
       
        for item_data in items_data:
            item_code = item_data.get("item_code") or item_data.get("name")
            if not item_code:
                continue
                
            sales_order.append("items", {
                "item_code": item_code,
                "qty": item_data.get("quantity", 1),
                "rate": item_data.get("price", 0),
                "delivery_date": frappe.utils.add_days(frappe.utils.nowdate(), 7),
                "warehouse": default_warehouse 
            })
        
        
        
        sales_order.insert(ignore_permissions=True)
        sales_order.submit()
        
        return {
            "id": sales_order.name,
            "status": "success",
            "message": _("Sales Order created successfully")
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Sales Order Creation Error")
        return {
            "status": "error",
            "message": str(e)
        }

def create_or_get_customer_by_phone(customer_data):
    """Create or get existing customer based on phone number"""
    from frappe import throw, _
    
    phone = customer_data.get("phone")
    if not phone:
        throw(_("Phone number is required to create a customer"))
    
   
    clean_phone = ''.join(filter(str.isdigit, phone))
    
   
    customer_name = frappe.db.get_value("Customer", {"mobile_no": clean_phone}, "name")
    
    if not customer_name:
       
        contact_name = frappe.db.get_value("Contact", {"mobile_no": clean_phone}, "name")
        if contact_name:
           
            customer_name = frappe.db.get_value("Dynamic Link", {
                "parenttype": "Contact",
                "parent": contact_name,
                "link_doctype": "Customer"
            }, "link_name")
    
    if customer_name:
        return customer_name
    
   
    customer = frappe.new_doc("Customer")
    customer.customer_name = f"{customer_data.get('firstName', '')} {customer_data.get('lastName', '')}".strip()
    customer.customer_type = "Individual"
    customer.mobile_no = clean_phone
    
   
    if customer_data.get("email"):
        customer.email_id = customer_data.get("email")
    
    customer.insert(ignore_permissions=True)
    
   
    contact = frappe.new_doc("Contact")
    contact.first_name = customer_data.get("firstName", "")
    contact.last_name = customer_data.get("lastName", "")
    contact.mobile_no = clean_phone
    
    if customer_data.get("email"):
        contact.email_id = customer_data.get("email")
        contact.append("email_ids", {
            "email_id": customer_data.get("email"),
            "is_primary": 1
        })
    
    contact.append("links", {
        "link_doctype": "Customer",
        "link_name": customer.name
    })
    contact.insert(ignore_permissions=True)
    
   
    if customer_data.get("address"):
        address = frappe.new_doc("Address")
        address.address_line1 = customer_data.get("address")
        address.city = customer_data.get("city", "Nairobi")
        address.address_type = "Billing"
        address.is_primary_address = 1
        address.is_shipping_address = 1
        address.append("links", {
            "link_doctype": "Customer",
            "link_name": customer.name
        })
        address.insert(ignore_permissions=True)
    
    return customer.name


@frappe.whitelist(allow_guest=True)
def get_sales_order_details(order_name):
    """Returns sales order details in API format"""
    from frappe import throw, _
    
    try:
        if not order_name:
            throw(_("Order name is required"))
        
       
        so = frappe.get_doc("Sales Order", order_name)
        
       
        customer = frappe.get_doc("Customer", so.customer)
        contact = get_customer_primary_contact(so.customer)
        
       
        items = []
        for item in so.items:
            items.append({
                "product_id": item.item_code,
                "quantity": item.qty,
                "price": item.rate,
                "name": item.item_name 
            })
        
        balances = get_sales_order_payments(so.name)
       
        response = {
            "phone": customer.mobile_no or (contact.mobile_no if contact else ""),
            "firstName": contact.first_name if contact else "",
            "lastName": contact.last_name if contact else "",
            "email": contact.email_id if contact else "",
            "items": items,
            "orderDate": so.transaction_date.strftime("%Y-%m-%d") if so.transaction_date else "",
            "deliveryDate": so.delivery_date.strftime("%Y-%m-%d") if so.delivery_date else "",
            "status": so.status,
            "total": so.total,
            "grandTotal": so.grand_total,
            "customer": so.customer,
            "orderName": so.name,
            **balances
        }
        
       
        address = get_customer_primary_address(so.customer)
        if address:
            response.update({
                "address": address.address_line1,
                "city": address.city
            })
        
        return {
            "status": "success",
            "data": response
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Sales Order Fetch Error")
        return {
            "status": "error",
            "message": str(e)
        }

def get_customer_primary_contact(customer_name):
    """Returns primary contact for customer"""
    contact_name = frappe.db.get_value("Dynamic Link", {
        "link_doctype": "Customer",
        "link_name": customer_name,
        "parenttype": "Contact"
    }, "parent")
    
    if contact_name:
        return frappe.get_doc("Contact", contact_name)
    return None

def get_customer_primary_address(customer_name):
    """Returns the most recent address linked to a customer"""
   
    links = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Customer",
            "link_name": customer_name,
            "parenttype": "Address",
        },
        fields=["parent"],
        order_by="creation desc",
        limit=1
    )

    if links:
        return frappe.get_doc("Address", links[0]["parent"])

    return None


def get_sales_order_payments(order_name):
    """Returns all payments connected to a sales order with totals"""
    from frappe import throw, _

    if not order_name:
        throw(_("Order name is required"))
    
    # Get sales order
    so = frappe.get_doc("Sales Order", order_name)
    
    # Get all Payment Entries linked to this sales order
    payment_entries = frappe.get_all(
        "Payment Entry Reference",
        filters={
            "reference_doctype": "Sales Order",
            "reference_name": order_name,
            "docstatus": 1  # Only submitted payments
        },
        fields=["parent", "allocated_amount"],
        order_by="creation"
    )
    
    # Get payment details
    payments = []
    total_paid = 0
    
    for entry in payment_entries:
        payment = frappe.get_doc("Payment Entry", entry.parent)
        payments.append({
            "payment_id": payment.name,
            "amount": entry.allocated_amount,
            "payment_date": payment.posting_date.strftime("%Y-%m-%d") if payment.posting_date else "",
            "payment_mode": payment.mode_of_payment,
            "status": payment.status
        })
        total_paid += entry.allocated_amount
    
    # Calculate balance
    balance = so.grand_total - total_paid
    
    return {
        "order_total": so.grand_total,
        "total_paid": total_paid,
        "balance": balance,
        "payments": payments,
        "currency": so.currency
    }
    
        