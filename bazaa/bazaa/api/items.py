import frappe
from frappe import _
import json
from math import ceil


def paginate(doctype, filters=None, page=1, limit=20, order_by="creation desc"):
    """
    Helper function for paginating any Frappe doctype list.
    Returns full documents (as_dict) for each entry.
    """
    filters = filters or {}

    # Ensure numeric values
    try:
        page = int(page)
        limit = int(limit)
    except Exception:
        page, limit = 1, 20

    offset = (page - 1) * limit

    # Total records
    total = frappe.db.count(doctype, filters=filters)

    # Fetch paginated names only
    records = frappe.get_all(
        doctype,
        filters=filters,
        fields=["name"],
        order_by=order_by,
        start=offset,
        page_length=limit,
    )

    # Load full docs via get_doc()
    data = []
    for rec in records:
        try:
            doc = frappe.get_doc(doctype, rec.name).as_dict()
            data.append(doc)
        except frappe.DoesNotExistError:
            continue  # skip missing entries

    total_pages = ceil(total / limit) if total > 0 else 1

    return {
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


@frappe.whitelist(allow_guest=True)
def groups():
    """Return paginated item groups (full docs)."""
    args = frappe._dict(frappe.request.args)

    args.pop("cmd", None)
    page = int(args.pop("page", 1))
    limit = int(args.pop("limit", 20))

    return paginate("Item Group", filters=args, page=page, limit=limit)


@frappe.whitelist(allow_guest=True)
def group_detail(name):
    """Return a single item group by name."""
    try:
        return frappe.get_doc("Item Group", name).as_dict()
    except frappe.DoesNotExistError:
        frappe.throw(_("Item Group not found"))


@frappe.whitelist(allow_guest=True)
def items(filters=None, page=1, limit=20):
    """Return paginated items with optional filters (full docs)."""
    filters = filters or {}

    # Parse JSON values
    for key, value in filters.items():
        if isinstance(value, str):
            try:
                filters[key] = json.loads(value)
            except Exception:
                pass

    return paginate("Item", filters=filters, page=page, limit=limit)


@frappe.whitelist(allow_guest=True)
def item_detail(name):
    """Return a single item by name or item_code."""
    item_name = frappe.db.get_value(
        "Item", {"name": name}, "name"
    ) or frappe.db.get_value("Item", {"item_code": name}, "name")

    if not item_name:
        frappe.throw(_("Item not found"))

    return frappe.get_doc("Item", item_name).as_dict()
