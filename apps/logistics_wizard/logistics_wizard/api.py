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
        # Origin Facility: supplier address or company
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

        # Destination Facility: warehouse or shipping address
        if not dest_facility:
            dest_facility = getattr(source_doc, "set_warehouse", None) or getattr(source_doc, "shipping_address", None)
            if dest_facility and frappe.db.exists("Address", dest_facility):
                try:
                    d_addr = frappe.get_doc("Address", dest_facility)
                    parts = [p for p in [d_addr.city, d_addr.country] if p]
                    if parts:
                        dest_facility = ", ".join(parts)
                    elif getattr(d_addr, "address_title", None):
                        dest_facility = d_addr.address_title
                except Exception:
                    pass

    # Intelligent Fallbacks for US (Apple) -> VN (Da Nang) Corridor
    if not origin_facility:
        origin_facility = "apple_park_cupertino"
    if not departure_hub:
        departure_hub = "port_of_long_beach" if method_norm == "Ocean" else "san_francisco_airport"
    if not arrival_hub:
        arrival_hub = "da_nang_port" if method_norm == "Ocean" else "da_nang_airport"
    if not dest_facility:
        dest_facility = "cap_khanh_warehouse"

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
        origin_info = {"query": str(origin_facility), "name": "Apple Park (Cupertino)", "coordinates": [37.3346, -122.009]}
        dhub_info = {"query": str(departure_hub), "name": "Port of Long Beach", "coordinates": [33.7542, -118.2165]}
        ahub_info = {"query": str(arrival_hub), "name": "Port of Da Nang", "coordinates": [16.1215, 108.223]}
        dest_info = {"query": str(dest_facility), "name": "Kho Logistics Cáp Kim Khánh Đà Nẵng", "coordinates": [16.0765, 108.151]}

    # 4. Determine Progress, Current Leg & Vehicle State
    check_status = (shipment_doc.status if shipment_doc else status) or "Draft"

    if check_status in ["Completed", "Received", "Closed", "Giao hàng thành công", "Delivered"]:
        progress = 1.0
        status_text = "Đã giao hàng thành công tại Kho Cáp Kim Khánh Đà Nẵng"
        current_location = dest_info.get("name") or "Kho Cáp Kim Khánh Đà Nẵng (KCN Hòa Khánh)"
        current_leg_id = "last_mile"
        current_vehicle = "Truck"
    elif check_status == "Customs Clearance":
        progress = max(0.85, progress_thresholds[2] if len(progress_thresholds) > 2 else 0.85)
        status_text = "Đang thông quan hải quan tại Cảng/Sân bay Đà Nẵng"
        current_location = ahub_info.get("name") or "Cảng Tiên Sa / Sân bay Đà Nẵng"
        current_leg_id = "last_mile"
        current_vehicle = "Truck"
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
        status_text = "Chờ xuất kho tại nguồn (Draft)"
        current_location = origin_info.get("name") or "Kho nhà máy Cupertino"
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
    if shipment_doc and getattr(shipment_doc, "transit_route", None):
        for r in shipment_doc.transit_route:
            c_coords = get_location_coords(r.location)
            checkpoints.append({
                "location": r.location,
                "activity": r.activity,
                "date": str(r.date) if r.date else "",
                "coordinates": [c_coords[0], c_coords[1]] if c_coords else None,
            })

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
]
