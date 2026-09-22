"""
Logistics Wizard - Central API Facade / Dispatcher
===================================================
Module này đóng vai trò tập hợp, điều phối và export các API cho ERPNext / Frappe RPC.
Các logic nghiệp vụ chuyên biệt đã được phân tách thành các module độc lập:
1. workflow.py: Quản lý 6 bước tiến trình chuỗi cung ứng (Workflow Chain Traversal & Status)
2. routing.py: Động cơ định tuyến hàng hải searoute, hàng không Great-Circle 3D & bộ nhớ đệm Redis
3. GEO_shipTracking.py: Quản lý toạ độ địa lý, geocoding và danh sách vận chuyển
4. aftership.py: Tích hợp và đồng bộ hành trình vận đơn từ dịch vụ AfterShip
"""

import frappe
from typing import Optional, Dict, Any

# 1. Module Workflow: Quản lý chuỗi tiến trình 6 bước
from .workflow import (
    WORKFLOW_STEPS,
    get_workflow_chain_status,
)

# 2. Module Routing Engine (Layer 2 - High Performance & Caching)
from .routing import (
    get_route_coordinates,
    get_location_coords,
    get_location_details,
    load_locations_data,
    calculate_ocean_route,
    calculate_air_route,
    calculate_road_route,
    calculate_multimodal_route,
    great_circle_distance,
    find_nearest_hub,
)

# 3. Module GEO & Legacy Tracking functions
from .GEO_shipTracking import (
    get_active_shipments,
    geocode_location,
    get_maritime_waypoints,
    get_air_waypoints,
    build_route,
)

# 4. Module AfterShip: Đồng bộ vận đơn
from .aftership import (
    sync_aftership,
)


@frappe.whitelist(allow_guest=True)
def get_shipment_tracking(docname: Optional[str] = None,
                          doctype: Optional[str] = None,
                          tracking_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Whitelisted API endpoint for ERPNext / Leaflet Map tracking.
    Dynamically extracts origin and destination from document / linked Shipment Tracking,
    invokes routing.py (searoute ocean routing / 3D Great-Circle air routing + Redis cache),
    and returns rich tracking data, real polylines, and GeoJSON.
    """
    # Support tracking_id argument interchangeably with docname
    if tracking_id and not docname:
        docname = tracking_id
        if not doctype:
            doctype = "Purchase Order" if str(docname).startswith("PUR") else "Shipment Tracking"

    if not docname or not doctype:
        return {"status": "error", "message": "Vui lòng chọn một đơn hàng hoặc mã vận đơn."}

    if not frappe.db.exists(doctype, docname):
        return {"status": "error", "message": f"Không tìm thấy chứng từ {doctype} {docname}."}

    doc = frappe.get_doc(doctype, docname)
    docstatus = doc.docstatus
    status = getattr(doc, "status", "Draft")

    shipment_doc = None
    po_doc = None

    if doctype == "Purchase Order":
        po_doc = doc
        shipment_name = frappe.db.get_value("Shipment Tracking", {"purchase_order": docname}, "name")
        if shipment_name:
            shipment_doc = frappe.get_doc("Shipment Tracking", shipment_name)
    elif doctype == "Shipment Tracking":
        shipment_doc = doc
        po_name = getattr(doc, "purchase_order", None)
        if po_name and frappe.db.exists("Purchase Order", po_name):
            po_doc = frappe.get_doc("Purchase Order", po_name)

    # 1. Resolve Shipping Method
    method = "Ocean"
    if shipment_doc and getattr(shipment_doc, "shipping_method", None):
        method = shipment_doc.shipping_method
    elif getattr(doc, "shipping_method", None):
        method = doc.shipping_method
    elif getattr(doc, "ship_via", None):
        method = doc.ship_via

    method_norm = str(method).strip().capitalize()
    if method_norm in ["Sea", "Maritime"]:
        method_norm = "Ocean"
    elif method_norm in ["Flight", "Plane"]:
        method_norm = "Air"
    elif method_norm in ["Truck", "Inland"]:
        method_norm = "Road"

    # 2. Extract Multimodal 4 Stations: Origin (O), Departure Hub, Arrival Hub, Destination (D)
    origin_facility = None
    departure_hub = None
    arrival_hub = None
    dest_facility = None

    if shipment_doc:
        departure_hub = getattr(shipment_doc, "origin_port", None)
        arrival_hub = getattr(shipment_doc, "destination_port", None)
        dest_facility = getattr(shipment_doc, "warehouse", None) or getattr(shipment_doc, "dest_warehouse", None)

    source_doc = po_doc or doc
    if source_doc:
        # Origin Facility: supplier address or supplier dynamic link
        if not origin_facility and getattr(source_doc, "supplier_address", None):
            try:
                s_addr = frappe.get_doc("Address", source_doc.supplier_address)
                parts = [p for p in [s_addr.city, s_addr.country] if p]
                if parts:
                    origin_facility = ", ".join(parts)
                elif getattr(s_addr, "address_title", None):
                    origin_facility = s_addr.address_title
            except Exception:
                origin_facility = source_doc.supplier_address

        if not origin_facility and getattr(source_doc, "supplier", None):
            try:
                links = frappe.get_all(
                    "Dynamic Link",
                    filters={"link_doctype": "Supplier", "link_name": source_doc.supplier, "parenttype": "Address"},
                    fields=["parent"]
                )
                if links:
                    s_addr = frappe.get_doc("Address", links[0].parent)
                    parts = [p for p in [s_addr.city, s_addr.country] if p]
                    if parts:
                        origin_facility = ", ".join(parts)
                    elif getattr(s_addr, "address_title", None):
                        origin_facility = s_addr.address_title
            except Exception:
                pass

        if not origin_facility:
            origin_facility = getattr(source_doc, "supplier", None)

        # Destination Facility: warehouse or shipping address
        if not dest_facility:
            wh_name = getattr(source_doc, "set_warehouse", None) or (shipment_doc and getattr(shipment_doc, "warehouse", None))
            if wh_name and frappe.db.exists("Warehouse", wh_name):
                try:
                    wh_doc = frappe.get_doc("Warehouse", wh_name)
                    if getattr(wh_doc, "address", None) and frappe.db.exists("Address", wh_doc.address):
                        d_addr = frappe.get_doc("Address", wh_doc.address)
                        parts = [p for p in [d_addr.city, d_addr.country] if p]
                        if parts:
                            dest_facility = ", ".join(parts)
                        elif getattr(d_addr, "address_title", None):
                            dest_facility = d_addr.address_title
                    if not dest_facility:
                        dest_facility = getattr(wh_doc, "warehouse_name", None) or wh_name
                except Exception:
                    dest_facility = wh_name

            if not dest_facility and getattr(source_doc, "shipping_address", None):
                if frappe.db.exists("Address", source_doc.shipping_address):
                    try:
                        d_addr = frappe.get_doc("Address", source_doc.shipping_address)
                        parts = [p for p in [d_addr.city, d_addr.country] if p]
                        if parts:
                            dest_facility = ", ".join(parts)
                        elif getattr(d_addr, "address_title", None):
                            dest_facility = d_addr.address_title
                    except Exception:
                        pass

            if not dest_facility and getattr(source_doc, "company", None):
                try:
                    c_links = frappe.get_all(
                        "Dynamic Link",
                        filters={"link_doctype": "Company", "link_name": source_doc.company, "parenttype": "Address"},
                        fields=["parent"]
                    )
                    if c_links:
                        c_addr = frappe.get_doc("Address", c_links[0].parent)
                        parts = [p for p in [c_addr.city, c_addr.country] if p]
                        if parts:
                            dest_facility = ", ".join(parts)
                except Exception:
                    pass
                if not dest_facility:
                    dest_facility = getattr(source_doc, "company", None)

    # Dynamic default fallbacks
    if not origin_facility:
        origin_facility = "Kho nhà máy xuất phát"
    if not dest_facility:
        dest_facility = "Kho đích nhận hàng"

    target_hub_type = "seaport" if method_norm == "Ocean" else "airport"

    # Resolve coordinates
    o_coords = get_location_coords(origin_facility)
    d_coords = get_location_coords(dest_facility)

    # Dynamic nearest hub selection if not explicitly specified
    if not departure_hub and o_coords:
        departure_hub = find_nearest_hub(o_coords, target_hub_type)

    if not arrival_hub and d_coords:
        arrival_hub = find_nearest_hub(d_coords, target_hub_type)

    # 3. Dynamic Route Generation via Multimodal Routing Engine
    try:
        route_data = calculate_multimodal_route(
            origin_facility=origin_facility,
            departure_hub=departure_hub,
            arrival_hub=arrival_hub,
            dest_facility=dest_facility,
            shipping_method=method_norm,
            use_cache=True
        )
        legs = route_data.get("legs", [])
        full_route = route_data.get("full_route", [])
        distance_km = route_data.get("distance_km", 0.0)
        is_cached = route_data.get("cached", False)
        progress_thresholds = route_data.get("progress_thresholds", [0.0, 0.05, 0.95, 1.0])
        origin_info = route_data.get("origin", {})
        dhub_info = route_data.get("departure_hub", {})
        ahub_info = route_data.get("arrival_hub", {})
        dest_info = route_data.get("destination", {})
    except Exception as e:
        frappe.log_error(f"Multimodal calculation failed ({e}), falling back to standard route", "Logistics Wizard Routing")
        route_legacy = get_route_coordinates(departure_hub or origin_facility, arrival_hub or dest_facility, shipping_method=method_norm, use_cache=True)
        legs = []
        full_route = route_legacy.get("coordinates_latlon", [])
        distance_km = route_legacy.get("distance_km", 0.0)
        is_cached = route_legacy.get("cached", False)
        progress_thresholds = [0.0, 0.05, 0.95, 1.0]

        orig_meta = get_location_details(origin_facility) or {}
        dhub_meta = get_location_details(departure_hub) or {}
        ahub_meta = get_location_details(arrival_hub) or {}
        dest_meta = get_location_details(dest_facility) or {}

        hub_type_str = "Cảng biển" if method_norm == "Ocean" else ("Sân bay" if method_norm == "Air" else "Trạm trung chuyển")

        origin_info = {
            "query": str(origin_facility),
            "name": orig_meta.get("name_vi") or orig_meta.get("name") or str(origin_facility),
            "coordinates": list(get_location_coords(origin_facility) or [0.0, 0.0])
        }
        dhub_info = {
            "query": str(departure_hub),
            "name": dhub_meta.get("name_vi") or dhub_meta.get("name") or (f"{hub_type_str} xuất phát ({departure_hub})" if departure_hub else "Điểm xuất phát"),
            "coordinates": list(get_location_coords(departure_hub)) if departure_hub and get_location_coords(departure_hub) else None
        }
        ahub_info = {
            "query": str(arrival_hub),
            "name": ahub_meta.get("name_vi") or ahub_meta.get("name") or (f"{hub_type_str} đến ({arrival_hub})" if arrival_hub else "Điểm đến"),
            "coordinates": list(get_location_coords(arrival_hub)) if arrival_hub and get_location_coords(arrival_hub) else None
        }
        dest_info = {
            "query": str(dest_facility),
            "name": dest_meta.get("name_vi") or dest_meta.get("name") or str(dest_facility),
            "coordinates": list(get_location_coords(dest_facility) or [0.0, 0.0])
        }

    # 4. Determine Progress, Current Leg & Vehicle State
    check_status = (shipment_doc.status if shipment_doc else status) or "Draft"

    hub_type_vi = "Cảng biển" if method_norm == "Ocean" else ("Sân bay" if method_norm == "Air" else "Trạm trung chuyển")
    origin_name = origin_info.get("name") or str(origin_facility) or "Kho nhà máy xuất phát"
    dhub_name = dhub_info.get("name") or (f"{hub_type_vi} xuất phát" if departure_hub else "Điểm xuất phát")
    ahub_name = ahub_info.get("name") or (f"{hub_type_vi} đến" if arrival_hub else "Điểm trung chuyển đến")
    dest_name = dest_info.get("name") or str(dest_facility) or "Kho đích nhận hàng"

    if shipment_doc:
        changed = sync_transit_route_with_status(shipment_doc, ahub_name, dest_name)
        if changed:
            try:
                shipment_doc.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception as e:
                frappe.log_error(f"Error saving synced transit route: {e}", "Logistics Wizard")

    if check_status in ["Completed", "Received", "Closed", "Giao hàng thành công", "Delivered"]:
        progress = 1.0
        status_text = f"Đã giao hàng thành công tại {dest_name}"
        current_location = dest_name
        current_leg_id = "last_mile"
        current_vehicle = "Truck"
    elif check_status == "Customs Clearance":
        progress = max(0.85, progress_thresholds[2] if len(progress_thresholds) > 2 else 0.85)
        status_text = f"Đang làm thủ tục thông quan hải quan tại {ahub_name}"
        current_location = ahub_name
        current_leg_id = "customs"
        current_vehicle = "Ship" if method_norm == "Ocean" else ("Plane" if method_norm == "Air" else "Truck")
    elif check_status == "In Transit" or (doctype == "Purchase Order" and docstatus == 1 and check_status not in ["Draft", "Cancelled"]):
        progress = 0.55
        current_leg_id = "main_haul"
        current_vehicle = "Ship" if method_norm == "Ocean" else "Plane"
        if method_norm == "Air":
            status_text = "Đang bay qua không phận Quốc tế (Air Transit)"
            current_location = "Không phận Quốc tế (Central Pacific Flight Corridor)"
        elif method_norm == "Ocean":
            status_text = "Đang trên biển Thái Bình Dương (Maritime Transit)"
            current_location = "Hải phận Quốc tế Thái Bình Dương (South of Aleutians)"
        else:
            status_text = "Đang trên tuyến đường bộ nội địa"
            current_location = "Tuyến đường bộ"
            current_vehicle = "Truck"

        if shipment_doc and getattr(shipment_doc, "transit_route", None) and len(shipment_doc.transit_route) > 1:
            current_location = shipment_doc.transit_route[-1].location
    elif check_status == "Draft" or (doctype == "Purchase Order" and docstatus in [0, 2]):
        progress = 0.0
        status_text = f"Chờ xuất kho tại nguồn ({origin_name})"
        current_location = origin_name
        current_leg_id = "first_mile"
        current_vehicle = "Truck"
        if shipment_doc and getattr(shipment_doc, "transit_route", None) and len(shipment_doc.transit_route) > 0:
            current_location = shipment_doc.transit_route[0].location
    else:
        progress = 0.5
        current_leg_id = "main_haul"
        current_vehicle = "Ship" if method_norm == "Ocean" else "Plane"
        status_text = "Đang trên hành trình vận chuyển đa phương thức"
        current_location = "Đang vận chuyển quốc tế"

    # 5. Calculate Current Traversed Route based on Progress
    if not full_route:
        current_route = []
    elif progress <= 0.0:
        current_route = [full_route[0]]
    elif progress >= 1.0:
        current_route = full_route
    else:
        cut_index = max(1, int(len(full_route) * progress))
        current_route = full_route[: cut_index + 1]

    # 6. Extract Transit Checkpoints (Milestones) from Child Table
    checkpoints = []
    if shipment_doc and getattr(shipment_doc, "transit_route", None) and len(shipment_doc.transit_route) > 0:
        has_any_curr = any("(Current Position)" in (r.activity or "") for r in shipment_doc.transit_route)
        for idx, r in enumerate(shipment_doc.transit_route):
            c_coords = get_location_coords(r.location)
            is_curr = "(Current Position)" in (r.activity or "")
            if not has_any_curr and idx == len(shipment_doc.transit_route) - 1 and check_status not in ["Draft", "Cancelled"]:
                is_curr = True
            clean_act = (r.activity or "").replace(" (Current Position)", "").replace("(Current Position)", "").strip()
            checkpoints.append({
                "location": r.location,
                "activity": clean_act,
                "is_current": is_curr,
                "date": str(r.date) if r.date else "",
                "coordinates": [c_coords[0], c_coords[1]] if c_coords else None,
                "notes": getattr(r, "notes", "") or ""
            })
    else:
        checkpoints = generate_fallback_checkpoints(origin_name, dhub_name, ahub_name, dest_name, check_status, method_norm)

    return {
        "status": "success",
        "success": True,
        "data": {
            "method": method_norm,
            "route": current_route,
            "full_route": full_route,
            "legs": legs,
            "distance_km": distance_km,
            "progress": progress,
            "progress_thresholds": progress_thresholds,
            "status_text": status_text,
            "current_location": current_location,
            "current_leg_id": current_leg_id,
            "current_vehicle": current_vehicle,
            "docname": docname,
            "doctype": doctype,
            "origin": origin_info,
            "departure_hub": dhub_info,
            "arrival_hub": ahub_info,
            "destination": dest_info,
            "checkpoints": checkpoints,
            "cached": is_cached,
            "waypoints_count": len(full_route),
        },
        "route": {
            "type": "Multimodal",
            "coordinates": full_route,
            "legs": legs,
            "method": method_norm,
            "distance_km": distance_km,
            "cached": is_cached,
        },
        "tracking": {
            "method": method_norm,
            "progress": progress,
            "status_text": status_text,
            "current_location": current_location,
            "current_vehicle": current_vehicle,
            "docname": docname,
        },
        "progress": progress,
    }


def sync_transit_route_with_status(shipment_doc, ahub_name=None, dest_name=None):
    """
    Synchronizes Shipment Tracking transit_route child table with current status.
    Ensures milestones accurately reflect Customs Clearance and Delivery states.
    """
    if not shipment_doc:
        return False
    status = getattr(shipment_doc, "status", None) or "Draft"
    ahub = ahub_name or getattr(shipment_doc, "destination_port", None) or "Cảng / Sân bay nhập khẩu"
    dest = dest_name or getattr(shipment_doc, "warehouse", None) or "Kho đích nhận hàng"

    routes = shipment_doc.get("transit_route") or []
    modified = False

    def clean_activity(text):
        if not text:
            return ""
        return text.replace(" (Current Position)", "").replace("(Current Position)", "").strip()

    def is_customs(text):
        t = (text or "").lower()
        if "export" in t or "xuất khẩu" in t:
            return False
        return "customs" in t or "thông quan" in t or "hải quan" in t

    def is_delivered(text):
        t = (text or "").lower()
        return "delivered" in t or "giao hàng thành công" in t or "nhập kho" in t

    has_customs = any(is_customs(r.activity) for r in routes)
    has_delivered = any(is_delivered(r.activity) for r in routes)

    today_date = str(frappe.utils.today())

    if status == "Customs Clearance":
        for r in routes:
            cleaned = clean_activity(r.activity)
            if cleaned != r.activity:
                r.activity = cleaned
                modified = True

        if not has_customs:
            shipment_doc.append("transit_route", {
                "date": today_date,
                "activity": "Làm thủ tục thông quan Hải quan (Customs Clearance) (Current Position)",
                "location": ahub,
                "notes": f"Lô hàng cập cảng/sân bay đích thực tế ngày {frappe.utils.format_date(today_date, 'dd/MM/yyyy')}, đang tiến hành mở tờ khai hải quan thông quan."
            })
            modified = True
        else:
            for r in routes:
                if is_customs(r.activity):
                    if "(Current Position)" not in (r.activity or ""):
                        r.activity = clean_activity(r.activity) + " (Current Position)"
                        modified = True
                    if str(r.date) != today_date:
                        r.date = today_date
                        modified = True

    elif status in ["Completed", "Received", "Closed", "Giao hàng thành công", "Delivered"]:
        for r in routes:
            cleaned = clean_activity(r.activity)
            if cleaned != r.activity:
                r.activity = cleaned
                modified = True

        if not has_customs:
            shipment_doc.append("transit_route", {
                "date": today_date,
                "activity": "Làm thủ tục thông quan Hải quan (Customs Clearance)",
                "location": ahub,
                "notes": "Hoàn tất thủ tục thông quan hải quan."
            })
            modified = True

        if not has_delivered:
            shipment_doc.append("transit_route", {
                "date": today_date,
                "activity": "Đã giao hàng thành công tại Kho đích (Delivered) (Current Position)",
                "location": dest,
                "notes": f"Đã vận chuyển chặng cuối an toàn và nhập kho hoàn tất ngày {frappe.utils.format_date(today_date, 'dd/MM/yyyy')}."
            })
            modified = True
        else:
            for r in routes:
                if is_delivered(r.activity):
                    if "(Current Position)" not in (r.activity or ""):
                        r.activity = clean_activity(r.activity) + " (Current Position)"
                        modified = True
                    if str(r.date) != today_date:
                        r.date = today_date
                        modified = True

    elif status == "In Transit":
        to_remove = [i for i, r in enumerate(routes) if is_customs(r.activity) or is_delivered(r.activity)]
        if to_remove:
            for idx in reversed(to_remove):
                routes.pop(idx)
            modified = True

        for r in routes:
            cleaned = clean_activity(r.activity)
            if cleaned != r.activity:
                r.activity = cleaned
                modified = True

        if routes:
            last_r = routes[-1]
            if "(Current Position)" not in (last_r.activity or ""):
                last_r.activity = clean_activity(last_r.activity) + " (Current Position)"
                modified = True

    return modified


def generate_fallback_checkpoints(origin_name, dhub_name, ahub_name, dest_name, check_status, method_norm):
    """
    Generates dynamic checkpoints when transit_route is empty or unavailable.
    """
    today_str = str(frappe.utils.today())
    past_date_1 = str(frappe.utils.add_days(today_str, -12))
    past_date_2 = str(frappe.utils.add_days(today_str, -10))
    past_date_3 = str(frappe.utils.add_days(today_str, -4))
    
    hub_type_str = "Cảng biển" if method_norm == "Ocean" else ("Sân bay" if method_norm == "Air" else "Trạm trung chuyển")

    cps = [
        {
            "date": past_date_1,
            "activity": "Đóng gói & Niêm phong Container tại Kho nguồn",
            "location": origin_name,
            "is_current": (check_status == "Draft"),
            "notes": "Hoàn tất đóng seal kiểm tra chất lượng tại nhà máy."
        },
        {
            "date": past_date_2,
            "activity": f"Xuất phát từ {hub_type_str} xuất khẩu",
            "location": dhub_name,
            "is_current": False,
            "notes": "Phương tiện vận tải rời trạm trung chuyển xuất phát."
        }
    ]

    if check_status in ["In Transit", "Customs Clearance", "Completed", "Received", "Closed", "Delivered"]:
        cps.append({
            "date": past_date_3,
            "activity": f"Hành trình vận chuyển {'trên biển' if method_norm == 'Ocean' else ('đường hàng không' if method_norm == 'Air' else 'đường bộ')} quốc tế",
            "location": "Hải phận Quốc tế Thái Bình Dương" if method_norm in ["Ocean", "Air"] else "Tuyến đường bộ nội địa",
            "is_current": (check_status == "In Transit"),
            "notes": "Hành trình ổn định, hệ thống AIS / ADS-B định vị liên tục."
        })

    if check_status in ["Customs Clearance", "Completed", "Received", "Closed", "Delivered"]:
        cps.append({
            "date": today_str,
            "activity": "Làm thủ tục thông quan Hải quan (Customs Clearance)",
            "location": ahub_name,
            "is_current": (check_status == "Customs Clearance"),
            "notes": "Lô hàng cập cảng đến, đang giải phóng tờ khai hải quan nhập khẩu."
        })

    if check_status in ["Completed", "Received", "Closed", "Delivered"]:
        cps.append({
            "date": today_str,
            "activity": "Đã giao hàng thành công tại Kho đích (Delivered)",
            "location": dest_name,
            "is_current": True,
            "notes": "Hàng đã nhập kho đầy đủ và hoàn tất kiểm đếm."
        })

    for cp in cps:
        if not cp.get("coordinates"):
            c_coords = get_location_coords(cp["location"])
            cp["coordinates"] = [c_coords[0], c_coords[1]] if c_coords else None

    return cps


def on_shipment_tracking_validate(doc, method=None):
    """
    Hook called when Shipment Tracking is validated/saved in Frappe desk.
    Automatically keeps transit_route child table synchronized with the selected status.
    """
    try:
        sync_transit_route_with_status(doc)
    except Exception as e:
        frappe.log_error(f"Error in on_shipment_tracking_validate: {e}", "Logistics Wizard")


__all__ = [
    "WORKFLOW_STEPS",
    "get_workflow_chain_status",
    "get_active_shipments",
    "get_shipment_tracking",
    "get_route_coordinates",
    "get_location_coords",
    "get_location_details",
    "load_locations_data",
    "calculate_ocean_route",
    "calculate_air_route",
    "calculate_road_route",
    "calculate_multimodal_route",
    "great_circle_distance",
    "geocode_location",
    "get_maritime_waypoints",
    "get_air_waypoints",
    "build_route",
    "sync_aftership",
    "sync_transit_route_with_status",
    "on_shipment_tracking_validate",
]
