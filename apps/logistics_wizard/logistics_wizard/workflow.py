import frappe
from frappe import _

WORKFLOW_STEPS = [
    {
        "step": 1,
        "doctype": "Material Request",
        "label": "1. Yêu cầu mua hàng (Material Request)",
        "slug": "material-request",
    },
    {
        "step": 2,
        "doctype": "Purchase Order",
        "label": "2. Đơn đặt hàng (Purchase Order)",
        "slug": "purchase-order",
    },
    {
        "step": 3,
        "doctype": "Payment Entry",
        "label": "3. Đặt cọc / Tạm ứng (Payment Entry)",
        "slug": "payment-entry",
    },
    {
        "step": 4,
        "doctype": "Shipment Tracking",
        "label": "4. Theo dõi hành trình (Shipment Tracking)",
        "slug": "shipment-tracking",
    },
    {
        "step": 5,
        "doctype": "Purchase Receipt",
        "label": "5. Nhận hàng (Purchase Receipt)",
        "slug": "purchase-receipt",
    },
    {
        "step": 6,
        "doctype": "Landed Cost Voucher",
        "label": "6. Phân bổ giá vốn (Landed Cost)",
        "slug": "landed-cost-voucher",
    },
    {
        "step": 7,
        "doctype": "Stock Entry",
        "label": "7. Nhập kho (Stock Entry)",
        "slug": "stock-entry",
    },
]


@frappe.whitelist(allow_guest=True)
def get_workflow_chain_status(doctype=None, docname=None):
    """
    Traverse 6-step logistics document chain bidirectionally:
    Material Request <-> Purchase Order <-> Shipment Tracking <-> Purchase Receipt <-> Landed Cost Voucher <-> Stock Entry
    Returns status, docstatus, completed flag, and direct link for each step.
    """
    # Input sanitization and type enforcement
    if not doctype or not docname or not isinstance(doctype, str) or not isinstance(docname, str):
        return {
            "success": False,
            "error": _("Thiếu thông tin doctype hoặc docname hợp lệ"),
            "steps": [],
        }

    # Ensure string arguments are stripped
    doctype = doctype.strip()
    docname = docname.strip()
    if not doctype or not docname:
        return {
            "success": False,
            "error": _("Thiếu thông tin doctype hoặc docname hợp lệ"),
            "steps": [],
        }

    chain = {s["doctype"]: None for s in WORKFLOW_STEPS}
    if doctype in chain:
        chain[doctype] = docname

    # 0. Traversal from/to Payment Entry
    if chain.get("Payment Entry") and not chain.get("Purchase Order"):
        chain["Purchase Order"] = _get_po_from_pe(chain["Payment Entry"])

    # 1. Traversal from/to Stock Entry
    if chain["Stock Entry"]:
        ste_pr, ste_po, ste_mr = _get_links_from_ste(chain["Stock Entry"])
        if ste_pr and not chain["Purchase Receipt"]:
            chain["Purchase Receipt"] = ste_pr
        if ste_po and not chain["Purchase Order"]:
            chain["Purchase Order"] = ste_po
        if ste_mr and not chain["Material Request"]:
            chain["Material Request"] = ste_mr

    # 2. Traversal from/to Landed Cost Voucher
    if chain["Landed Cost Voucher"] and not chain["Purchase Receipt"]:
        chain["Purchase Receipt"] = _get_pr_from_lcv(chain["Landed Cost Voucher"])

    # 3. Traversal from/to Shipment Tracking
    if chain["Shipment Tracking"]:
        st_po, st_pr = _get_links_from_st(chain["Shipment Tracking"])
        if st_po and not chain["Purchase Order"]:
            chain["Purchase Order"] = st_po
        if st_pr and not chain["Purchase Receipt"]:
            chain["Purchase Receipt"] = st_pr

    # 4. Traversal between Purchase Receipt and Purchase Order
    if chain["Purchase Receipt"] and not chain["Purchase Order"]:
        chain["Purchase Order"] = _get_po_from_pr(chain["Purchase Receipt"])
    elif chain["Purchase Order"] and not chain["Purchase Receipt"]:
        chain["Purchase Receipt"] = _get_pr_from_po(chain["Purchase Order"])

    # 5. Traversal between Purchase Order and Material Request
    if chain["Purchase Order"] and not chain["Material Request"]:
        chain["Material Request"] = _get_mr_from_po(chain["Purchase Order"])
    elif chain["Material Request"] and not chain["Purchase Order"]:
        chain["Purchase Order"] = _get_po_from_mr(chain["Material Request"])

    # 6. Secondary resolution for Material Request via Purchase Receipt if still missing
    if not chain["Material Request"] and chain["Purchase Receipt"]:
        chain["Material Request"] = _get_mr_from_pr(chain["Purchase Receipt"])
    elif not chain["Purchase Receipt"] and chain["Material Request"]:
        chain["Purchase Receipt"] = _get_pr_from_mr(chain["Material Request"])

    # 7. Secondary resolution for Payment Entry via Purchase Order
    if not chain.get("Payment Entry") and chain.get("Purchase Order"):
        chain["Payment Entry"] = _get_pe_from_po(chain["Purchase Order"])

    # 8. Secondary resolution for Landed Cost Voucher via Purchase Receipt
    if not chain["Landed Cost Voucher"] and chain["Purchase Receipt"]:
        chain["Landed Cost Voucher"] = _get_lcv_from_pr(chain["Purchase Receipt"])

    # 9. Secondary resolution for Stock Entry
    if not chain["Stock Entry"]:
        chain["Stock Entry"] = _get_ste_from_chain(
            chain["Purchase Receipt"],
            chain["Purchase Order"],
            chain["Material Request"],
        )

    # 10. Secondary resolution for Shipment Tracking
    if not chain["Shipment Tracking"]:
        chain["Shipment Tracking"] = _get_shipment_tracking(
            chain["Purchase Order"], chain["Purchase Receipt"]
        )

    # Compile result steps
    steps = []
    current_index = -1
    for idx, step_cfg in enumerate(WORKFLOW_STEPS):
        d_type = step_cfg["doctype"]
        d_name = chain.get(d_type)
        status_info = _get_doc_status_info(d_type, d_name) if d_name else None

        is_current = d_type == doctype and d_name == docname
        if is_current:
            current_index = idx

        steps.append(
            {
                "step": step_cfg["step"],
                "doctype": d_type,
                "label": step_cfg["label"],
                "slug": step_cfg["slug"],
                "docname": d_name,
                "docstatus": status_info["docstatus"] if status_info else None,
                "status": status_info["status"] if status_info else "Chưa tạo",
                "completed": status_info["completed"] if status_info else False,
                "url": f"/app/{step_cfg['slug']}/{d_name}" if d_name else f"/app/{step_cfg['slug']}",
                "is_current": is_current,
            }
        )

    # If current doc was found in chain, mark preceding completed steps accordingly
    if current_index != -1:
        for i in range(current_index):
            if steps[i]["docname"] and steps[i]["docstatus"] == 1:
                steps[i]["completed"] = True

    return {"success": True, "steps": steps}


def _get_mr_from_po(po_name):
    mr = frappe.db.get_value(
        "Purchase Order Item",
        {"parent": po_name, "material_request": ["is", "set"]},
        "material_request",
    )
    if not mr:
        # Fallback query if material_request is not empty string
        records = frappe.get_all(
            "Purchase Order Item",
            filters={"parent": po_name},
            fields=["material_request"],
            limit=1,
        )
        if records and records[0].material_request:
            mr = records[0].material_request
    return mr


def _get_po_from_mr(mr_name):
    po = frappe.db.get_value(
        "Purchase Order Item",
        {"material_request": mr_name, "docstatus": ["!=", 2]},
        "parent",
    )
    return po


def _get_pr_from_po(po_name):
    pr = frappe.db.get_value(
        "Purchase Receipt Item",
        {"purchase_order": po_name, "docstatus": ["!=", 2]},
        "parent",
    )
    return pr


def _get_po_from_pr(pr_name):
    po = frappe.db.get_value(
        "Purchase Receipt Item",
        {"parent": pr_name, "purchase_order": ["is", "set"]},
        "purchase_order",
    )
    if not po:
        records = frappe.get_all(
            "Purchase Receipt Item",
            filters={"parent": pr_name},
            fields=["purchase_order"],
            limit=1,
        )
        if records and records[0].purchase_order:
            po = records[0].purchase_order
    return po


def _get_mr_from_pr(pr_name):
    mr = frappe.db.get_value(
        "Purchase Receipt Item",
        {"parent": pr_name, "material_request": ["is", "set"]},
        "material_request",
    )
    if not mr:
        records = frappe.get_all(
            "Purchase Receipt Item",
            filters={"parent": pr_name},
            fields=["material_request"],
            limit=1,
        )
        if records and records[0].material_request:
            mr = records[0].material_request
    return mr


def _get_pr_from_mr(mr_name):
    pr = frappe.db.get_value(
        "Purchase Receipt Item",
        {"material_request": mr_name, "docstatus": ["!=", 2]},
        "parent",
    )
    return pr


def _get_lcv_from_pr(pr_name):
    lcv = frappe.db.get_value(
        "Landed Cost Purchase Receipt",
        {"receipt_document": pr_name, "docstatus": ["!=", 2]},
        "parent",
    )
    return lcv


def _get_pr_from_lcv(lcv_name):
    pr = frappe.db.get_value(
        "Landed Cost Purchase Receipt",
        {
            "parent": lcv_name,
            "receipt_document_type": "Purchase Receipt",
            "docstatus": ["!=", 2],
        },
        "receipt_document",
    )
    return pr


def _get_ste_from_chain(pr_name, po_name, mr_name):
    # Check if Stock Entry references Purchase Receipt
    if pr_name and frappe.db.has_column("Stock Entry", "purchase_receipt_no"):
        ste = frappe.db.get_value(
            "Stock Entry",
            {"purchase_receipt_no": pr_name, "docstatus": ["!=", 2]},
            "name",
        )
        if ste:
            return ste

    if pr_name and frappe.db.has_column("Stock Entry", "reference_no"):
        ste = frappe.db.get_value(
            "Stock Entry",
            {"reference_no": pr_name, "docstatus": ["!=", 2]},
            "name",
        )
        if ste:
            return ste

    # Check via Stock Entry Detail
    if pr_name and frappe.db.has_column("Stock Entry Detail", "reference_purchase_receipt"):
        ste = frappe.db.get_value(
            "Stock Entry Detail",
            {"reference_purchase_receipt": pr_name, "docstatus": ["!=", 2]},
            "parent",
        )
        if ste:
            return ste

    # Check via Material Request
    if mr_name:
        ste = frappe.db.get_value(
            "Stock Entry Detail",
            {"material_request": mr_name, "docstatus": ["!=", 2]},
            "parent",
        )
        if ste:
            return ste

    # Check via Purchase Order
    if po_name and frappe.db.has_column("Stock Entry", "purchase_order"):
        ste = frappe.db.get_value(
            "Stock Entry",
            {"purchase_order": po_name, "docstatus": ["!=", 2]},
            "name",
        )
        if ste:
            return ste

    return None


def _get_links_from_ste(ste_name):
    ste_pr, ste_po, ste_mr = None, None, None

    # Check parent fields
    if frappe.db.has_column("Stock Entry", "purchase_receipt_no"):
        ste_pr = frappe.db.get_value("Stock Entry", ste_name, "purchase_receipt_no")
    if not ste_pr and frappe.db.has_column("Stock Entry", "reference_no"):
        ref = frappe.db.get_value("Stock Entry", ste_name, "reference_no")
        if ref and frappe.db.exists("Purchase Receipt", ref):
            ste_pr = ref

    if frappe.db.has_column("Stock Entry", "purchase_order"):
        ste_po = frappe.db.get_value("Stock Entry", ste_name, "purchase_order")

    # Check item details
    items = frappe.get_all(
        "Stock Entry Detail",
        filters={"parent": ste_name},
        fields=["material_request", "name"],
        limit=10,
    )
    for item in items:
        if item.material_request and not ste_mr:
            ste_mr = item.material_request

    return ste_pr, ste_po, ste_mr


def _get_shipment_tracking(po_name, pr_name):
    if not frappe.db.exists("DocType", "Shipment Tracking"):
        return None

    st = None
    if po_name and frappe.db.has_column("Shipment Tracking", "purchase_order"):
        st = frappe.db.get_value(
            "Shipment Tracking",
            {"purchase_order": po_name, "docstatus": ["!=", 2]},
            "name",
        )
    if not st and pr_name and frappe.db.has_column("Shipment Tracking", "purchase_receipt"):
        st = frappe.db.get_value(
            "Shipment Tracking",
            {"purchase_receipt": pr_name, "docstatus": ["!=", 2]},
            "name",
        )
    if not st and po_name and frappe.db.has_column("Shipment Tracking", "tracking_number"):
        st = frappe.db.get_value(
            "Shipment Tracking",
            {"tracking_number": po_name, "docstatus": ["!=", 2]},
            "name",
        )
    if not st and po_name and frappe.db.has_column("Purchase Order", "shipment_tracking"):
        st = frappe.db.get_value("Purchase Order", po_name, "shipment_tracking")
    if not st and pr_name and frappe.db.has_column("Purchase Receipt", "shipment_tracking"):
        st = frappe.db.get_value("Purchase Receipt", pr_name, "shipment_tracking")

    # Final fallback: look up by naming convention (e.g. SHIP-TRACK-{po_name})
    if not st and po_name:
        candidate = f"SHIP-TRACK-{po_name}"
        if frappe.db.exists("Shipment Tracking", candidate):
            st = candidate

    return st


def _get_links_from_st(st_name):
    st_po, st_pr = None, None
    if frappe.db.has_column("Shipment Tracking", "purchase_order"):
        st_po = frappe.db.get_value("Shipment Tracking", st_name, "purchase_order")
    if frappe.db.has_column("Shipment Tracking", "purchase_receipt"):
        st_pr = frappe.db.get_value("Shipment Tracking", st_name, "purchase_receipt")

    if not st_po and st_name.startswith("SHIP-TRACK-"):
        possible_po = st_name.replace("SHIP-TRACK-", "")
        if frappe.db.exists("Purchase Order", possible_po):
            st_po = possible_po

    return st_po, st_pr


def _get_pe_from_po(po_name):
    if not po_name:
        return None
    pe = frappe.db.sql("""
        SELECT parent FROM `tabPayment Entry Reference`
        WHERE reference_doctype = 'Purchase Order' AND reference_name = %s AND docstatus != 2
        ORDER BY creation DESC LIMIT 1
    """, (po_name,))
    if pe:
        return pe[0][0]

    # Fallback: check if PO was billed via Purchase Invoice and paid
    try:
        pi_names = frappe.db.get_all(
            "Purchase Invoice Item",
            filters={"purchase_order": po_name, "docstatus": ["!=", 2]},
            pluck="parent",
            distinct=True
        )
        if pi_names:
            pe_row = frappe.db.sql("""
                SELECT parent FROM `tabPayment Entry Reference`
                WHERE reference_doctype = 'Purchase Invoice' AND reference_name IN %s AND docstatus != 2
                ORDER BY creation DESC LIMIT 1
            """, (tuple(pi_names),))
            if pe_row:
                return pe_row[0][0]
    except Exception:
        pass

    return None


def _get_po_from_pe(pe_name):
    if not pe_name:
        return None
    po = frappe.db.sql("""
        SELECT reference_name FROM `tabPayment Entry Reference`
        WHERE parent = %s AND reference_doctype = 'Purchase Order' AND docstatus != 2
        LIMIT 1
    """, (pe_name,))
    if po:
        return po[0][0]

    # Fallback: check via referenced Purchase Invoice
    try:
        pi = frappe.db.sql("""
            SELECT reference_name FROM `tabPayment Entry Reference`
            WHERE parent = %s AND reference_doctype = 'Purchase Invoice' AND docstatus != 2
            LIMIT 1
        """, (pe_name,))
        if pi:
            po_name = frappe.db.get_value(
                "Purchase Invoice Item",
                {"parent": pi[0][0], "docstatus": ["!=", 2]},
                "purchase_order"
            )
            if po_name:
                return po_name
    except Exception:
        pass

    return None


def _get_doc_status_info(doctype, docname):
    if not frappe.db.exists(doctype, docname):
        return None

    # Get docstatus and status if available
    fields = ["docstatus"]
    if frappe.db.has_column(doctype, "status"):
        fields.append("status")

    data = frappe.db.get_value(doctype, docname, fields, as_dict=True)
    if not data:
        return None

    docstatus = data.get("docstatus", 0)
    status = data.get("status", "")

    # Determine standard status label if empty
    if not status:
        if docstatus == 0:
            status = "Draft"
        elif docstatus == 1:
            status = "Submitted"
        elif docstatus == 2:
            status = "Cancelled"

    # Business rule for completed state across standard procurement DocTypes
    completed = False
    if docstatus == 1:
        if doctype == "Material Request":
            completed = status in ["Ordered", "Issued", "Transferred", "Received"]
        elif doctype == "Purchase Order":
            completed = status in ["To Receive and Bill", "To Bill", "To Receive", "Completed", "Closed"]
        elif doctype == "Payment Entry":
            completed = True
        elif doctype == "Shipment Tracking":
            completed = status in ["Delivered", "Completed", "Giao hàng thành công", "Received", "Closed"]
        elif doctype in ["Purchase Receipt", "Landed Cost Voucher", "Stock Entry"]:
            completed = True

    return {
        "docstatus": docstatus,
        "status": status,
        "completed": completed,
    }
