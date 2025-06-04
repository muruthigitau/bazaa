import frappe
from frappe import _
import json

@frappe.whitelist(allow_guest=True)
def groups():
    """Return all item groups with additional fields"""
    item_groups = frappe.get_all(
        "Item Group",
        fields=[
            "name",
            "parent_item_group",
            "is_group",
            "image",
            "description",
            "summary"
        ]
    )
    return item_groups

@frappe.whitelist(allow_guest=True)
def group_detail(name):
    """Return a single item group by name"""
    item_group = frappe.get_all(
        "Item Group",
        filters={"name": name},
        fields=[
            "name",
            "parent_item_group",
            "is_group",
            "image",
            "description",
            "summary"
        ],
        limit=1
    )
    return item_group[0] if item_group else None



@frappe.whitelist(allow_guest=True)
def items():
    """Return all items with selected fields, optionally filtered"""
    filters = frappe._dict(frappe.request.args)

   
    filters.pop("cmd", None)

   
    for key, value in filters.items():
        if isinstance(value, str):
            try:
                filters[key] = json.loads(value)
            except Exception:
                pass

    items = frappe.get_all(
        "Item",
        filters=filters,
        fields=[
            "name",
            "item_name",
            "item_code",
            "item_group",
            "image",
            "price",
            "old_price",
            "discount",
            "vat_price",
            "additional_cost",
            "description",
            "summary"
        ]
    )
    return items


@frappe.whitelist(allow_guest=True)
def item_detail(name):
    """Return a single item by name or item_code"""
    item = frappe.get_all(
        "Item",
        filters={"name": name}, 
        fields=[
            "name",
            "item_code",
            "item_name",
            "item_group",
            "image",
             "price",
            "old_price",
            "discount",
            "vat_price",
            "additional_cost",
            "description",
            "summary"
        ],
        limit=1
    )
    return item[0] if item else None
