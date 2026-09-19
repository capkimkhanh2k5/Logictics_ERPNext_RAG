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
import frappe
import requests
import random
import urllib.parse

OFFLINE_LOCATION_COORDINATES = {
    # Apple / California / US West Coast
    "apple park, cupertino": [37.3346, -122.0090],
    "apple park": [37.3346, -122.0090],
    "apple inc.": [37.3346, -122.0090],
    "apple warehouse, cupertino": [37.3346, -122.0090],
    "cupertino": [37.3318, -122.0312],
    "cupertino, california": [37.3318, -122.0312],
    "san francisco": [37.7749, -122.4194],
    "san francisco airport": [37.6213, -122.3790],
    "sfo airport": [37.6213, -122.3790],
    "sfo": [37.6213, -122.3790],
    "port of long beach": [33.7701, -118.1937],
    "long beach port": [33.7701, -118.1937],
    "long beach": [33.7701, -118.1937],
    "port of los angeles": [33.7432, -118.2673],
    "la port": [33.7432, -118.2673],
    "port of oakland": [37.7952, -122.2792],
    "oakland": [37.7952, -122.2792],
    "california": [36.7783, -119.4179],
    "united states": [37.0902, -95.7129],
    "usa": [37.0902, -95.7129],

    # Texas / US Inland
    "dell factory, texas": [30.4515, -97.6664],
    "dell factory": [30.4515, -97.6664],
    "highway 45 to new york": [36.1627, -86.7816],
    "highway 45": [32.7767, -96.7970],
    "texas": [31.9686, -99.9018],
    "port of new york": [40.6840, -74.0400],
    "new york": [40.7128, -74.0060],
    "american": [37.0902, -95.7129],
    "american port": [40.7128, -74.0060],
    "us port": [40.7128, -74.0060],

    # Ocean / Maritime & Air Corridors
    "pacific ocean": [20.0, -160.0],
    "ocean": [20.0, -160.0],
    "hawaii transit hub": [21.3069, -157.8583],
    "mid-pacific ocean": [20.0, -165.0],
    "guam maritime corridor": [13.4443, 144.7937],
    "luzon strait": [20.0, 121.0],
    "east sea": [12.0, 114.0],
    "south china sea": [12.0, 114.0],
    "pacific flight corridor": [28.0, -165.0],
    "tokyo narita airspace": [35.7720, 140.3929],

    # Vietnam Ports & Gateways
    "cat lai port, ho chi minh": [10.7600, 106.7900],
    "cat lai port": [10.7600, 106.7900],
    "vn port": [10.7600, 106.7900],
    "cap khanhs warehouse": [10.8231, 106.6297],
    "cap khanh logistics warehouse": [10.8231, 106.6297],
    "cap khanh logistics": [10.8231, 106.6297],
    "stores - ck": [10.8231, 106.6297],
    "ck store": [10.8231, 106.6297],
    "tan son nhat airport": [10.8188, 106.6520],
    "tan son nhat": [10.8188, 106.6520],
    "sgn airport": [10.8188, 106.6520],
    "sgn": [10.8188, 106.6520],
    "noi bai airport": [21.2212, 105.8072],
    "noi bai": [21.2212, 105.8072],
    "han airport": [21.2212, 105.8072],
    "ho chi minh city": [10.8231, 106.6297],
    "tp. hồ chí minh": [10.8231, 106.6297],
    "ho chi minh": [10.8231, 106.6297],
    "hanoi": [21.0285, 105.8542],
    "hà nội": [21.0285, 105.8542],
    "da nang": [16.0544, 108.2022],
    "đà nẵng": [16.0544, 108.2022],
    "hai phong port": [20.8651, 106.7093],
    "hai phong": [20.8449, 106.6881],
    "hải phòng": [20.8449, 106.6881],
    "vietnam": [14.0583, 108.2772],

    # International Hubs
    "singapore": [1.3521, 103.8198],
    "tokyo": [35.6762, 139.6503],
    "shanghai": [31.2304, 121.4737],
}

def geocode_location(city, country):
    if not city and not country:
        return None
    query = f"{city or ''}, {country or ''}".strip(", ")
    
    cache_key = f"geocache_{query.lower()}"
    try:
        cached = frappe.cache().get_value(cache_key)
        if cached:
            return cached
    except Exception:
        pass

    # Check offline coordinate database first for container / network isolation resilience
    q_lower = query.lower().strip()
    if q_lower in OFFLINE_LOCATION_COORDINATES:
        coords = OFFLINE_LOCATION_COORDINATES[q_lower]
        try:
            frappe.cache().set_value(cache_key, coords, expires_in_sec=86400)
        except Exception:
            pass
        return coords

    for key, coords in OFFLINE_LOCATION_COORDINATES.items():
        if key in q_lower or q_lower in key:
            try:
                frappe.cache().set_value(cache_key, coords, expires_in_sec=86400)
            except Exception:
                pass
            return coords

    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
    headers = {"User-Agent": "ERPNext-LogisticsWizard-App"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200 and r.json():
            data = r.json()[0]
            result = [float(data['lat']), float(data['lon'])]
            try:
                frappe.cache().set_value(cache_key, result, expires_in_sec=86400)
            except Exception:
                pass
            return result
    except Exception as e:
        frappe.log_error(title="Geocoding Error", message=f"Query: {query}, Error: {str(e)}")
    return None

def get_maritime_waypoints(origin, dest):
    o_lat, o_lng = origin
    d_lat, d_lng = dest
    waypoints = [origin]
    
    # Trans-Pacific route (US West Coast <-> Vietnam / SE Asia)
    if (o_lng < -70 and d_lng > 100) or (o_lng > 100 and d_lng < -70):
        # US -> Hawaii -> Guam -> Luzon Strait / East Sea -> Vietnam
        if o_lng < 0: # Origin in US, Dest in Asia
            waypoints.append([21.3069, -157.8583])  # Hawaii Transit Hub
            waypoints.append([13.4443, 144.7937])   # Guam Maritime Corridor
            waypoints.append([16.0, 118.0])         # East Sea / South China Sea
        else: # Origin in Asia, Dest in US
            waypoints.append([16.0, 118.0])
            waypoints.append([13.4443, 144.7937])
            waypoints.append([21.3069, -157.8583])
    elif o_lng > 70 and d_lng < 50:
        waypoints.append([5.0, 80.0])
        if d_lat > 20:
            waypoints.append([12.0, 43.0])
            waypoints.append([27.0, 34.0])
    
    waypoints.append(dest)
    return waypoints

def get_air_waypoints(origin, dest):
    o_lat, o_lng = origin
    d_lat, d_lng = dest
    waypoints = [origin]
    
    # Trans-Pacific Air corridor (US <-> Vietnam)
    if (o_lng < -70 and d_lng > 100) or (o_lng > 100 and d_lng < -70):
        if o_lng < 0:
            waypoints.append([35.0, -165.0])       # Pacific Flight Corridor
            waypoints.append([35.7720, 140.3929])  # Tokyo Narita Airspace
        else:
            waypoints.append([35.7720, 140.3929])
            waypoints.append([35.0, -165.0])
    
    waypoints.append(dest)
    return waypoints

@frappe.whitelist(allow_guest=True)
def get_active_shipments():
    """Returns a list of Purchase Orders that are currently in transit."""
    pos = frappe.get_all(
        "Purchase Order",
        filters={
            "docstatus": 1,
            "status": ["not in", ["Draft", "Completed", "Closed", "Received", "Cancelled", "Giao hàng thành công"]]
        },
        fields=["name", "status", "transaction_date", "supplier_name"]
    )
    return {"status": "success", "data": pos}

@frappe.whitelist(allow_guest=True)
def get_shipment_tracking(docname=None, doctype=None):
    if not docname or not doctype:
        return {"status": "error", "message": "Vui lòng chọn một đơn hàng."}

    if not frappe.db.exists(doctype, docname):
        return {"status": "error", "message": "Không tìm thấy chứng từ."}
        
    doc = frappe.get_doc(doctype, docname)
    docstatus = doc.docstatus
    status = getattr(doc, 'status', 'Draft')
    
    # Check if there is a Shipment Tracking document for this Purchase Order
    shipment_doc = None
    if doctype == "Purchase Order":
        shipment_name = frappe.db.get_value("Shipment Tracking", {"purchase_order": docname}, "name")
        if shipment_name:
            shipment_doc = frappe.get_doc("Shipment Tracking", shipment_name)
    elif doctype == "Shipment Tracking":
        shipment_doc = doc
        
    method = 'Road'
    if shipment_doc and hasattr(shipment_doc, 'shipping_method') and shipment_doc.shipping_method:
        method = shipment_doc.shipping_method
    elif hasattr(doc, 'shipping_method') and doc.shipping_method:
        method = doc.shipping_method
    elif hasattr(doc, 'ship_via') and doc.ship_via:
        method = doc.ship_via
    else:
        method = random.choice(['Air', 'Ocean', 'Road'])

    origin_city, origin_country = "Hanoi", "Vietnam"
    dest_city, dest_country = "Ho Chi Minh City", "Vietnam"
    origin_str, dest_str = "Hà Nội", "TP. Hồ Chí Minh"

    if doctype == "Purchase Order":
        if doc.supplier_address:
            addr = frappe.get_doc("Address", doc.supplier_address)
            if addr.city: origin_city = addr.city
            if addr.country: origin_country = addr.country
            origin_str = f"{origin_city}, {origin_country}"
            
        if doc.shipping_address:
            addr = frappe.get_doc("Address", doc.shipping_address)
            if addr.city: dest_city = addr.city
            if addr.country: dest_country = addr.country
            dest_str = f"{dest_city}, {dest_country}"
        elif doc.billing_address:
            addr = frappe.get_doc("Address", doc.billing_address)
            if addr.city: dest_city = addr.city
            if addr.country: dest_country = addr.country
            dest_str = f"{dest_city}, {dest_country}"

    route_coords = []
    
    # If we have a Shipment Tracking doc with transit_route, use those locations!
    if shipment_doc and shipment_doc.transit_route:
        for row in shipment_doc.transit_route:
            if row.location:
                # Some naive geocoding lookup
                loc_coords = geocode_location(row.location, "")
                if loc_coords:
                    route_coords.append(loc_coords)

    if not route_coords:
        origin_coords = geocode_location(origin_city, origin_country) or [21.0285, 105.8542]
        dest_coords = geocode_location(dest_city, dest_country) or [10.8231, 106.6297]

        if method == 'Ocean':
            route_coords = get_maritime_waypoints(origin_coords, dest_coords)
        elif method == 'Air':
            route_coords = get_air_waypoints(origin_coords, dest_coords)
        else:
            route_coords = [origin_coords, dest_coords]

    progress = 0.5
    status_text = "Đang vận chuyển (In Transit)"
    
    if method == 'Air':
        current_location = "Đang bay qua không phận Quốc tế"
    elif method == 'Ocean':
        current_location = "Đang trên biển (Maritime Transit)"
    else:
        current_location = "Đang trên tuyến đường bộ"

    if docstatus == 1 and status in ['Completed', 'Received', 'Closed', 'Giao hàng thành công', 'Delivered']:
        progress = 1.0
        status_text = "Đã giao hàng thành công"
        current_location = dest_str
        if shipment_doc and shipment_doc.transit_route:
            current_location = shipment_doc.transit_route[-1].location
    elif docstatus == 2 or (docstatus == 0):
        progress = 0.0
        status_text = "Chờ xử lý"
        current_location = origin_str
        if shipment_doc and shipment_doc.transit_route:
            current_location = shipment_doc.transit_route[0].location

    current_route = []
    if progress == 0.0:
        current_route = [route_coords[0]]
    elif progress == 1.0:
        current_route = route_coords
    else:
        # If we have custom waypoints, include all route coordinates in sequence
        # and set the current location
        if len(route_coords) > 2:
            current_route = route_coords
            if shipment_doc and shipment_doc.transit_route:
                current_location = shipment_doc.transit_route[-2].location if len(shipment_doc.transit_route) > 1 else current_location
        else:
            mid = [
                (route_coords[0][0] + route_coords[-1][0]) / 2,
                (route_coords[0][1] + route_coords[-1][1]) / 2
            ]
            current_route = [route_coords[0], mid]

    return {
        "status": "success",
        "data": {
            "method": method,
            "route": current_route,
            "full_route": route_coords,
            "progress": progress,
            "status_text": status_text,
            "current_location": current_location,
            "docname": docname
        }
    }
