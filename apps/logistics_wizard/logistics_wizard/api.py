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
        "doctype": "Shipment Tracking",
        "label": "3. Theo dõi hành trình (Shipment Tracking)",
        "slug": "shipment-tracking",
    },
    {
        "step": 4,
        "doctype": "Purchase Receipt",
        "label": "4. Nhận hàng (Purchase Receipt)",
        "slug": "purchase-receipt",
    },
    {
        "step": 5,
        "doctype": "Landed Cost Voucher",
        "label": "5. Phân bổ giá vốn (Landed Cost)",
        "slug": "landed-cost-voucher",
    },
    {
        "step": 6,
        "doctype": "Stock Entry",
        "label": "6. Nhập kho (Stock Entry)",
        "slug": "stock-entry",
    },
]


@frappe.whitelist()
def sync_aftership(tracking_number, shipment_name):
    if not tracking_number or not shipment_name:
        frappe.throw("Thiếu mã vận đơn (tracking_number)")

    mock_data = {
        "data": {
            "tracking": {
                "tag": "InTransit",
                "checkpoints": [
                    {
                        "checkpoint_time": "2026-09-15T10:00:00",
                        "location": "US Port",
                        "message": "Export Customs Cleared",
                    },
                    {
                        "checkpoint_time": "2026-09-15T12:00:00",
                        "location": "Ocean",
                        "message": "Departed (Loaded on Vessel/Flight)",
                    },
                    {
                        "checkpoint_time": "2026-09-15T15:00:00",
                        "location": "Pacific Ocean",
                        "message": "Ocean/Air Transit",
                    },
                ],
            }
        }
    }

    shipment = frappe.get_doc("Shipment Tracking", shipment_name)
    shipment.set("transit_route", [])

    for cp in mock_data["data"]["tracking"]["checkpoints"]:
        shipment.append(
            "transit_route",
            {
                "activity": cp.get("message"),
                "location": cp.get("location"),
                "date": cp.get("checkpoint_time").split("T")[0],
            },
        )

    shipment.save(ignore_permissions=True)
    frappe.db.commit()
    return f"Đã đồng bộ thành công {len(mock_data['data']['tracking']['checkpoints'])} trạm hành trình!"


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

    # 6. Fallback direct links between PR and MR
    if chain["Purchase Receipt"] and not chain["Material Request"]:
        chain["Material Request"] = _get_mr_from_pr(chain["Purchase Receipt"])
    elif chain["Material Request"] and not chain["Purchase Receipt"]:
        chain["Purchase Receipt"] = _get_pr_from_mr(chain["Material Request"])

    # 7. Secondary pass: ensure all downstream links from discovered nodes are populated
    # From PO -> PR & MR & ST
    if chain["Purchase Order"]:
        if not chain["Material Request"]:
            chain["Material Request"] = _get_mr_from_po(chain["Purchase Order"])
        if not chain["Purchase Receipt"]:
            chain["Purchase Receipt"] = _get_pr_from_po(chain["Purchase Order"])
        if not chain["Shipment Tracking"]:
            chain["Shipment Tracking"] = _get_shipment_tracking(
                chain["Purchase Order"], chain["Purchase Receipt"]
            )

    # From PR -> LCV & STE & ST
    if chain["Purchase Receipt"]:
        if not chain["Landed Cost Voucher"]:
            chain["Landed Cost Voucher"] = _get_lcv_from_pr(chain["Purchase Receipt"])
        if not chain["Stock Entry"]:
            chain["Stock Entry"] = _get_ste_from_chain(
                chain["Purchase Receipt"],
                chain["Purchase Order"],
                chain["Material Request"],
            )
        if not chain["Shipment Tracking"]:
            chain["Shipment Tracking"] = _get_shipment_tracking(
                chain["Purchase Order"], chain["Purchase Receipt"]
            )

    # From ST -> PO / PR
    if not chain["Shipment Tracking"]:
        chain["Shipment Tracking"] = _get_shipment_tracking(
            chain["Purchase Order"], chain["Purchase Receipt"]
        )

    # Final pass for Stock Entry from any linked node
    if not chain["Stock Entry"]:
        chain["Stock Entry"] = _get_ste_from_chain(
            chain["Purchase Receipt"],
            chain["Purchase Order"],
            chain["Material Request"],
        )

    # Construct response steps
    steps_data = []
    for s in WORKFLOW_STEPS:
        dt = s["doctype"]
        dn = chain.get(dt)
        status_info = _get_doc_status_info(dt, dn)
        is_current = (dt == doctype and dn == docname)

        steps_data.append(
            {
                "step": s["step"],
                "doctype": dt,
                "label": s["label"],
                "docname": dn,
                "docstatus": status_info["docstatus"],
                "status": status_info["status"],
                "completed": status_info["completed"],
                "is_current": is_current,
                "url": f"/app/{s['slug']}/{dn}" if dn else f"/app/{s['slug']}",
            }
        )

    return {
        "success": True,
        "current_doctype": doctype,
        "current_docname": docname,
        "steps": steps_data,
    }


# ==================== QUERY HELPERS (INDEX-OPTIMIZED) ====================

def _get_mr_from_po(po_name):
    if not po_name or not isinstance(po_name, str):
        return None
    items = frappe.db.get_all(
        "Purchase Order Item",
        filters={"parent": po_name, "docstatus": ["<", 2]},
        fields=["material_request"],
        limit=1,
    )
    for it in items:
        if it.material_request:
            return it.material_request
    return None


def _get_po_from_mr(mr_name):
    if not mr_name or not isinstance(mr_name, str):
        return None
    items = frappe.db.get_all(
        "Purchase Order Item",
        filters={"material_request": mr_name, "docstatus": ["<", 2]},
        fields=["parent"],
        order_by="docstatus desc, creation desc",
        limit=1,
    )
    return items[0].parent if items else None


def _get_pr_from_po(po_name):
    if not po_name or not isinstance(po_name, str):
        return None
    items = frappe.db.get_all(
        "Purchase Receipt Item",
        filters={"purchase_order": po_name, "docstatus": ["<", 2]},
        fields=["parent"],
        order_by="docstatus desc, creation desc",
        limit=1,
    )
    return items[0].parent if items else None


def _get_po_from_pr(pr_name):
    if not pr_name or not isinstance(pr_name, str):
        return None
    items = frappe.db.get_all(
        "Purchase Receipt Item",
        filters={"parent": pr_name, "docstatus": ["<", 2]},
        fields=["purchase_order"],
        limit=1,
    )
    for it in items:
        if it.purchase_order:
            return it.purchase_order
    return None


def _get_mr_from_pr(pr_name):
    if not pr_name or not isinstance(pr_name, str):
        return None
    items = frappe.db.get_all(
        "Purchase Receipt Item",
        filters={"parent": pr_name, "docstatus": ["<", 2]},
        fields=["material_request"],
        limit=1,
    )
    for it in items:
        if it.material_request:
            return it.material_request
    return None


def _get_pr_from_mr(mr_name):
    if not mr_name or not isinstance(mr_name, str):
        return None
    items = frappe.db.get_all(
        "Purchase Receipt Item",
        filters={"material_request": mr_name, "docstatus": ["<", 2]},
        fields=["parent"],
        order_by="docstatus desc, creation desc",
        limit=1,
    )
    return items[0].parent if items else None


def _get_lcv_from_pr(pr_name):
    if not pr_name or not isinstance(pr_name, str):
        return None
    records = frappe.db.get_all(
        "Landed Cost Purchase Receipt",
        filters={
            "receipt_document": pr_name,
            "receipt_document_type": "Purchase Receipt",
            "docstatus": ["<", 2],
        },
        fields=["parent"],
        order_by="docstatus desc, creation desc",
        limit=1,
    )
    return records[0].parent if records else None


def _get_pr_from_lcv(lcv_name):
    if not lcv_name or not isinstance(lcv_name, str):
        return None
    records = frappe.db.get_all(
        "Landed Cost Purchase Receipt",
        filters={
            "parent": lcv_name,
            "receipt_document_type": "Purchase Receipt",
            "docstatus": ["<", 2],
        },
        fields=["receipt_document"],
        limit=1,
    )
    return (
        records[0].receipt_document
        if records and records[0].receipt_document
        else None
    )


def _get_ste_from_chain(pr_name, po_name, mr_name):
    pr_name = pr_name if (pr_name and isinstance(pr_name, str)) else None
    po_name = po_name if (po_name and isinstance(po_name, str)) else None
    mr_name = mr_name if (mr_name and isinstance(mr_name, str)) else None

    if pr_name:
        ste = frappe.db.get_value(
            "Stock Entry",
            {"purchase_receipt_no": pr_name, "docstatus": ["<", 2]},
            "name",
        )
        if ste:
            return ste
        ste_det = frappe.db.get_all(
            "Stock Entry Detail",
            filters={
                "reference_purchase_receipt": pr_name,
                "docstatus": ["<", 2],
            },
            fields=["parent"],
            order_by="docstatus desc, creation desc",
            limit=1,
        )
        if ste_det:
            return ste_det[0].parent

    if po_name:
        ste = frappe.db.get_value(
            "Stock Entry",
            {"purchase_order": po_name, "docstatus": ["<", 2]},
            "name",
        )
        if ste:
            return ste

    if mr_name:
        ste_det = frappe.db.get_all(
            "Stock Entry Detail",
            filters={"material_request": mr_name, "docstatus": ["<", 2]},
            fields=["parent"],
            order_by="docstatus desc, creation desc",
            limit=1,
        )
        if ste_det:
            return ste_det[0].parent

    return None


def _get_links_from_ste(ste_name):
    if not ste_name or not isinstance(ste_name, str):
        return None, None, None
    ste = frappe.db.get_value(
        "Stock Entry", ste_name, ["purchase_receipt_no", "purchase_order"], as_dict=True
    )
    pr = ste.purchase_receipt_no if ste else None
    po = ste.purchase_order if ste else None
    mr = None
    if not pr:
        det_pr = frappe.db.get_all(
            "Stock Entry Detail",
            filters={"parent": ste_name, "docstatus": ["<", 2]},
            fields=["reference_purchase_receipt"],
            limit=1,
        )
        if det_pr and det_pr[0].reference_purchase_receipt:
            pr = det_pr[0].reference_purchase_receipt
    det_mr = frappe.db.get_all(
        "Stock Entry Detail",
        filters={"parent": ste_name, "docstatus": ["<", 2]},
        fields=["material_request"],
        limit=1,
    )
    if det_mr and det_mr[0].material_request:
        mr = det_mr[0].material_request
    return pr, po, mr


def _get_shipment_tracking(po_name, pr_name):
    po_name = po_name if (po_name and isinstance(po_name, str)) else None
    pr_name = pr_name if (pr_name and isinstance(pr_name, str)) else None
    if not po_name and not pr_name:
        return None
    if not frappe.db.exists("DocType", "Shipment Tracking"):
        return None
    meta = frappe.get_meta("Shipment Tracking")
    if po_name:
        if meta.has_field("purchase_order"):
            res = frappe.db.get_all(
                "Shipment Tracking",
                filters={"purchase_order": po_name, "docstatus": ["<", 2]},
                fields=["name"],
                order_by="docstatus desc, creation desc",
                limit=1,
            )
            if res:
                return res[0].name
        if meta.has_field("po_no"):
            res = frappe.db.get_all(
                "Shipment Tracking",
                filters={"po_no": po_name, "docstatus": ["<", 2]},
                fields=["name"],
                order_by="docstatus desc, creation desc",
                limit=1,
            )
            if res:
                return res[0].name
    if pr_name and meta.has_field("purchase_receipt"):
        res = frappe.db.get_all(
            "Shipment Tracking",
            filters={"purchase_receipt": pr_name, "docstatus": ["<", 2]},
            fields=["name"],
            order_by="docstatus desc, creation desc",
            limit=1,
        )
        if res:
            return res[0].name
    return None


def _get_links_from_st(st_name):
    if not st_name or not isinstance(st_name, str) or not frappe.db.exists("DocType", "Shipment Tracking"):
        return None, None
    meta = frappe.get_meta("Shipment Tracking")
    po, pr = None, None
    if meta.has_field("purchase_order"):
        po = frappe.db.get_value("Shipment Tracking", st_name, "purchase_order")
    elif meta.has_field("po_no"):
        po = frappe.db.get_value("Shipment Tracking", st_name, "po_no")
    if meta.has_field("purchase_receipt"):
        pr = frappe.db.get_value("Shipment Tracking", st_name, "purchase_receipt")
    return po, pr


def _get_doc_status_info(doctype, docname):
    if (
        not doctype
        or not docname
        or not isinstance(doctype, str)
        or not isinstance(docname, str)
    ):
        return {"docstatus": None, "status": None, "completed": False}

    if not frappe.db.exists("DocType", doctype) or not frappe.db.exists(doctype, docname):
        return {"docstatus": None, "status": None, "completed": False}

    meta = frappe.get_meta(doctype)
    fields = ["name", "docstatus"]
    if meta.has_field("status"):
        fields.append("status")

    doc_vals = frappe.db.get_value(doctype, docname, fields, as_dict=True)
    if not doc_vals:
        return {"docstatus": None, "status": None, "completed": False}

    docstatus = doc_vals.get("docstatus", 0)
    status = doc_vals.get("status", "")

    if doctype == "Shipment Tracking":
        completed = bool(docname) and (docstatus != 2 and status != "Cancelled")
    elif meta.is_submittable:
        completed = (docstatus == 1)
    else:
        completed = (docstatus != 2 and status != "Cancelled")

    return {
        "docstatus": docstatus,
        "status": status,
        "completed": completed,
    }
