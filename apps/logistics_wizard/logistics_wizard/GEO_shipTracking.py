
import os
import json
import math
import random
import urllib.parse

import frappe

# --------------------------------------------------------------------------
# 1. CƠ SỞ DỮ LIỆU TOẠ ĐỘ (Single Source of Truth: locations.json)
# --------------------------------------------------------------------------

def _load_locations_from_json():
    """
    Nạp dữ liệu toạ độ tự động từ file duy nhất locations.json (Single Source of Truth).
    Hỗ trợ alias, tiếng Việt, tiếng Anh, mã cảng UN/LOCODE, IATA, ICAO.
    """
    coords = {}
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "data", "locations.json")
    if not os.path.exists(json_path):
        try:
            json_path = frappe.get_app_path("logistics_wizard", "data", "locations.json")
        except Exception:
            pass
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                locations = data.get("locations", {})
                for loc_id, loc in locations.items():
                    c = loc.get("coordinates")
                    if not c:
                        continue
                    pt = [float(c["latitude"]), float(c["longitude"])]
                    coords[loc_id] = pt
                    coords[loc_id.replace("_", " ")] = pt
                    if loc.get("name"):
                        coords[loc["name"].lower().strip()] = pt
                    if loc.get("name_vi"):
                        coords[loc["name_vi"].lower().strip()] = pt
                    for alias in loc.get("aliases", []):
                        coords[alias.lower().strip()] = pt
                    codes = loc.get("codes", {})
                    for code_val in codes.values():
                        if code_val:
                            coords[str(code_val).lower().strip()] = pt
        except Exception as e:
            pass
    return coords


OFFLINE_LOCATION_COORDINATES = {
    # ---------------- Apple / California / US West Coast ----------------
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
    "port of long beach": [33.7542, -118.2165],
    "long beach port": [33.7542, -118.2165],
    "long beach": [33.7542, -118.2165],
    "port of los angeles": [33.7395, -118.2610],
    "la port": [33.7395, -118.2610],
    "port of oakland": [37.7955, -122.2779],
    "oakland": [37.7955, -122.2779],
    "california": [36.7783, -119.4179],
    "united states": [37.0902, -95.7129],
    "usa": [37.0902, -95.7129],

    # ---------------- Texas / US Inland (đã sửa) ----------------
    # Dell HQ thực tế: One Dell Way, Round Rock, TX 78682
    "dell factory, texas": [30.4991, -97.6786],
    "dell factory": [30.4991, -97.6786],
    "texas": [31.9686, -99.9018],
    # Cảng Houston — điểm trung chuyển đường bộ hợp lý cho hàng từ Texas
    # ra biển (qua Houston Ship Channel), thay cho "Highway 45 to New York"
    # (entry cũ vô nghĩa về địa lý vì I-45 không đi tới New York).
    "houston port": [29.7300, -95.2600],
    "port of houston": [29.7300, -95.2600],

    # ---------------- US East Coast / Gulf (đã sửa) ----------------
    # Port Newark-Elizabeth Marine Terminal (NJ) — nơi xử lý container
    # thực tế, KHÔNG phải toạ độ cũ rơi vào khu Manhattan/Brooklyn.
    "port of new york": [40.6864, -74.1451],
    "new york": [40.7128, -74.0060],
    "american": [37.0902, -95.7129],
    "american port": [40.6864, -74.1451],
    "us port": [40.6864, -74.1451],

    # ---------------- Kênh đào Panama (dùng cho tuyến Bờ Đông/Gulf) ------
    "panama canal atlantic": [9.3500, -79.9000],   # Cửa Colón
    "panama canal pacific": [8.9500, -79.5700],    # Cửa Balboa

    # ---------------- Ocean / Maritime & Air Corridors ----------------
    "pacific ocean": [20.0, -160.0],
    "ocean": [20.0, -160.0],
    # Hawaii/Guam: hợp lý cho tuyến QUA PANAMA (vĩ độ thấp), không dùng
    # cho tuyến Bờ Tây Mỹ (tuyến đó đi theo Bắc Thái Bình Dương).
    "hawaii transit hub": [21.3069, -157.8583],
    "mid-pacific ocean": [15.0, -150.0],
    "guam maritime corridor": [13.4443, 144.7937],
    # Đỉnh vòng cung Bắc Thái Bình Dương (North Pacific Great Circle
    # vertex) cho tuyến Bờ Tây Mỹ → Châu Á, phía Nam quần đảo Aleutian.
    "north pacific vertex": [48.0, 175.0],
    "off japan": [33.0, 142.0],
    "east china sea": [27.0, 126.0],
    "luzon strait": [21.0, 121.0],
    "south china sea": [12.0, 114.0],
    "pacific flight corridor": [28.0, -165.0],
    "tokyo narita airspace": [35.7720, 140.3929],

    # ---------------- Vietnam Ports & Gateways ----------------
    "cat lai port, ho chi minh": [10.7626, 106.7898],
    "cat lai port": [10.7626, 106.7898],
    "vn port": [10.7626, 106.7898],
    "cai mep terminal": [10.5172, 107.0142],
    "vung tau approach": [10.3278, 107.0333],
    "cap khanhs warehouse": [16.0765, 108.1510],
    "cap khanh logistics warehouse": [16.0765, 108.1510],
    "cap khanh logistics": [16.0765, 108.1510],
    "stores - ck": [16.0765, 108.1510],
    "ck store": [16.0765, 108.1510],
    "kho cap khanh": [16.0765, 108.1510],
    "kho cáp kim khánh": [16.0765, 108.1510],
    "kho cap khanh da nang": [16.0765, 108.1510],
    "kho cáp kim khánh đà nẵng": [16.0765, 108.1510],
    "tan son nhat airport": [10.8188, 106.6520],
    "tan son nhat": [10.8188, 106.6520],
    "sgn airport": [10.8188, 106.6520],
    "sgn": [10.8188, 106.6520],
    "noi bai airport": [21.2212, 105.8072],
    "noi bai": [21.2212, 105.8072],
    "han airport": [21.2212, 105.8072],
    "da nang port": [16.1215, 108.2230],
    "cảng tiên sa": [16.1215, 108.2230],
    "cảng đà nẵng": [16.1215, 108.2230],
    "da nang airport": [16.0439, 108.1994],
    "sân bay đà nẵng": [16.0439, 108.1994],
    "dad airport": [16.0439, 108.1994],
    "dad": [16.0439, 108.1994],
    "da nang": [16.0765, 108.1510],
    "đà nẵng": [16.0765, 108.1510],
    "ho chi minh city": [10.8231, 106.6297],
    "tp. hồ chí minh": [10.8231, 106.6297],
    "ho chi minh": [10.8231, 106.6297],
    "hanoi": [21.0285, 105.8542],
    "hà nội": [21.0285, 105.8542],
    "hai phong port": [20.8656, 106.7620],
    "hai phong": [20.8449, 106.6881],
    "hải phòng": [20.8449, 106.6881],
    "vietnam": [14.0583, 108.2772],

    # ---------------- International Hubs (dùng cho Air, nếu cần) --------
    "singapore": [1.3521, 103.8198],
    "tokyo": [35.6762, 139.6503],
    "shanghai": [31.2304, 121.4737],
    "hong kong airport": [22.3080, 113.9185],
    "incheon airport": [37.4602, 126.4407],
    "taipei taoyuan airport": [25.0797, 121.2342],
}

# Đồng bộ toạ độ từ file duy nhất locations.json (Single Source of Truth)
try:
    OFFLINE_LOCATION_COORDINATES.update(_load_locations_from_json())
except Exception:
    pass



# --------------------------------------------------------------------------
# 2. NỘI SUY GREAT-CIRCLE (thay thế nội suy tuyến tính cũ)
# --------------------------------------------------------------------------

def great_circle_points(lat1, lon1, lat2, lon2, n=8):
    """
    Sinh n+1 điểm nằm trên đường great-circle (đường ngắn nhất trên mặt
    cầu) giữa (lat1, lon1) và (lat2, lon2).

    Dùng công thức nội suy điểm trung gian chuẩn (Ed Williams' Aviation
    Formulary), tính trong không gian Cartesian 3D nên xử lý đúng cả
    trường hợp tuyến đi qua đường đổi ngày quốc tế (kinh độ +170/-170) —
    đây là lỗi mà cách nội suy tuyến tính cũ (lat1+lat2)/2 mắc phải.
    """
    lat1r, lon1r, lat2r, lon2r = map(math.radians, [lat1, lon1, lat2, lon2])

    d = 2 * math.asin(math.sqrt(
        math.sin((lat1r - lat2r) / 2) ** 2 +
        math.cos(lat1r) * math.cos(lat2r) * math.sin((lon1r - lon2r) / 2) ** 2
    ))

    if d == 0:
        return [[lat1, lon1]]

    points = []
    for i in range(n + 1):
        f = i / n
        a = math.sin((1 - f) * d) / math.sin(d)
        b = math.sin(f * d) / math.sin(d)
        x = a * math.cos(lat1r) * math.cos(lon1r) + b * math.cos(lat2r) * math.cos(lon2r)
        y = a * math.cos(lat1r) * math.sin(lon1r) + b * math.cos(lat2r) * math.sin(lon2r)
        z = a * math.sin(lat1r) + b * math.sin(lat2r)
        lat = math.degrees(math.atan2(z, math.sqrt(x ** 2 + y ** 2)))
        lon = math.degrees(math.atan2(y, x))
        points.append([lat, lon])
    return points


def build_route(waypoints, points_per_segment=6):
    """
    Nhận danh sách các "chokepoint" bắt buộc [[lat, lon], ...] và trả về
    một đường đi mượt bằng cách nội suy great-circle giữa từng cặp điểm
    liên tiếp (thay vì nối thẳng như code cũ, dễ cắt ngang qua đất liền
    hoặc bị gãy khúc khi vẽ lên bản đồ).
    """
    full_route = []
    for i in range(len(waypoints) - 1):
        segment = great_circle_points(
            waypoints[i][0], waypoints[i][1],
            waypoints[i + 1][0], waypoints[i + 1][1],
            n=points_per_segment,
        )
        if i > 0:
            segment = segment[1:]  # tránh trùng điểm nối giữa 2 đoạn
        full_route.extend(segment)
    return full_route


# --------------------------------------------------------------------------
# 3. GEOCODING (offline lookup trước, online fallback sau)
# --------------------------------------------------------------------------

def geocode_location(city, country):
    if not city and not country:
        return None
    query = f"{city or ''}, {country or ''}".strip(", ")
    q_lower = query.lower().strip()

    cache_key = f"geocache_{q_lower}"
    try:
        cached = frappe.cache().get_value(cache_key)
        if cached:
            return cached
    except Exception:
        pass

    # 0) Tra cứu chuẩn xác qua Routing Engine (locations.json Single Source of Truth)
    try:
        from .routing import get_location_coords
        res = None
        if city:
            res = get_location_coords(city)
        if not res and query:
            res = get_location_coords(query)
        if res:
            coords = [float(res[0]), float(res[1])]
            _cache_coords(cache_key, coords)
            return coords
    except Exception:
        pass

    # 1) Khớp chính xác trong OFFLINE_LOCATION_COORDINATES
    if q_lower in OFFLINE_LOCATION_COORDINATES:
        coords = OFFLINE_LOCATION_COORDINATES[q_lower]
        _cache_coords(cache_key, coords)
        return coords


    # 2) Khớp gần đúng — chỉ chấp nhận khi key đủ dài (>=4 ký tự) để
    #    giảm rủi ro khớp nhầm (vd "sgn" khớp bừa vào chuỗi khác).
    for key, coords in OFFLINE_LOCATION_COORDINATES.items():
        if len(key) >= 4 and (key in q_lower or q_lower in key):
            _cache_coords(cache_key, coords)
            return coords

    # 3) Fallback online (Nominatim) khi không có trong offline DB
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
    headers = {"User-Agent": "ERPNext-LogisticsWizard-App"}
    try:
        import requests
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200 and r.json():
            data = r.json()[0]
            result = [float(data["lat"]), float(data["lon"])]
            _cache_coords(cache_key, result)
            return result
    except Exception as e:
        frappe.log_error(title="Geocoding Error", message=f"Query: {query}, Error: {str(e)}")
    return None


def _cache_coords(cache_key, coords):
    try:
        frappe.cache().set_value(cache_key, coords, expires_in_sec=86400)
    except Exception:
        pass


# --------------------------------------------------------------------------
# 4. ĐỊNH TUYẾN OCEAN — phân biệt đúng Bờ Tây vs Bờ Đông/Gulf
# --------------------------------------------------------------------------

def _classify_us_coast(lng):
    """
    US ports với kinh độ < -100 được xem là Bờ Tây (Pacific-facing:
    California, Oregon, Washington). Từ -100 trở về phía Đông là
    Bờ Đông/Gulf (Texas Gulf, New York, Savannah...) — nhóm này bắt
    buộc phải đi qua kênh đào Panama để ra Thái Bình Dương.
    """
    return "west" if lng < -100 else "east_or_gulf"


def get_maritime_waypoints(origin, dest):
    """
    origin, dest: [lat, lng]
    Trả về route thực tế dựa trên great-circle interpolation qua các
    chokepoint địa lý bắt buộc.
    """
    o_lat, o_lng = origin
    d_lat, d_lng = dest

    is_us_to_vn = o_lng < -60 and 100 < d_lng < 130
    is_vn_to_us = d_lng < -60 and 100 < o_lng < 130

    if is_us_to_vn or is_vn_to_us:
        us_point = origin if is_us_to_vn else dest
        vn_point = dest if is_us_to_vn else origin
        coast = _classify_us_coast(us_point[1])

        if coast == "west":
            # Tuyến North Pacific Great Circle Route thực tế:
            # cảng Bờ Tây -> vòng lên ~48°N (Nam Aleutian) -> ngoài
            # khơi Nhật Bản -> Luzon Strait -> Biển Đông -> Vũng Tàu
            mandatory = [
                us_point,
                [48.0, 175.0],
                [33.0, 142.0],
                [21.0, 121.0],
                [12.0, 114.0],
                [10.30, 107.10],
                vn_point,
            ]
        else:
            # Bờ Đông/Gulf: bắt buộc qua kênh đào Panama, sau đó cắt
            # Thái Bình Dương ở vĩ độ thấp (khu vực Hawaii/Guam hợp lý
            # cho tuyến này).
            mandatory = [
                us_point,
                [9.35, -79.90],
                [8.95, -79.57],
                [15.0, -150.0],
                [13.4443, 144.7937],
                [12.0, 114.0],
                [10.30, 107.10],
                vn_point,
            ]

        route = build_route(mandatory, points_per_segment=6)
        return route if is_us_to_vn else list(reversed(route))

    # Fallback chung cho các cặp điểm khác: great-circle trực tiếp
    return build_route([origin, dest], points_per_segment=8)


# --------------------------------------------------------------------------
# 5. ĐỊNH TUYẾN AIR — great-circle thuần ("bay thẳng")
# --------------------------------------------------------------------------

def get_air_waypoints(origin, dest, via_hub=None):
    """
    Mặc định: bay thẳng theo great-circle (đúng bản chất vật lý của
    máy bay — không bị cản bởi địa hình như tàu biển).

    Truyền via_hub=[lat, lon] nếu muốn mô phỏng transit qua 1 sân bay
    trung chuyển châu Á — thực tế cargo LAX-SGN mất ~20h17m (dài hơn
    bay thẳng lý thuyết ~15-16h) vì thường transit qua Hong Kong,
    Narita hoặc Incheon.
    """
    if via_hub:
        return build_route([origin, via_hub, dest], points_per_segment=6)
    return build_route([origin, dest], points_per_segment=10)


# Sân bay hub châu Á thường dùng để mô phỏng transit (tuỳ chọn)
ASIA_AIR_HUBS = {
    "hong kong": [22.3080, 113.9185],
    "narita": [35.7720, 140.3929],
    "incheon": [37.4602, 126.4407],
    "taipei": [25.0797, 121.2342],
}


# --------------------------------------------------------------------------
# 6. WHITELISTED API — dùng cho ERPNext client-side (bản đồ theo dõi)
# --------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_active_shipments():
    """Trả về danh sách Purchase Order đang trong quá trình vận chuyển."""
    pos = frappe.get_all(
        "Purchase Order",
        filters={
            "docstatus": 1,
            "status": ["not in", ["Draft", "Completed", "Closed", "Received", "Cancelled", "Giao hàng thành công"]],
        },
        fields=["name", "status", "transaction_date", "supplier_name"],
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
    status = getattr(doc, "status", "Draft")

    shipment_doc = None
    if doctype == "Purchase Order":
        shipment_name = frappe.db.get_value("Shipment Tracking", {"purchase_order": docname}, "name")
        if shipment_name:
            shipment_doc = frappe.get_doc("Shipment Tracking", shipment_name)
    elif doctype == "Shipment Tracking":
        shipment_doc = doc

    method = "Road"
    if shipment_doc and getattr(shipment_doc, "shipping_method", None):
        method = shipment_doc.shipping_method
    elif getattr(doc, "shipping_method", None):
        method = doc.shipping_method
    elif getattr(doc, "ship_via", None):
        method = doc.ship_via
    else:
        method = random.choice(["Air", "Ocean", "Road"])

    origin_city, origin_country = "Hanoi", "Vietnam"
    dest_city, dest_country = "Ho Chi Minh City", "Vietnam"
    origin_str, dest_str = "Hà Nội", "TP. Hồ Chí Minh"

    if doctype == "Purchase Order":
        if doc.supplier_address:
            addr = frappe.get_doc("Address", doc.supplier_address)
            if addr.city:
                origin_city = addr.city
            if addr.country:
                origin_country = addr.country
            origin_str = f"{origin_city}, {origin_country}"

        if doc.shipping_address:
            addr = frappe.get_doc("Address", doc.shipping_address)
            if addr.city:
                dest_city = addr.city
            if addr.country:
                dest_country = addr.country
            dest_str = f"{dest_city}, {dest_country}"
        elif doc.billing_address:
            addr = frappe.get_doc("Address", doc.billing_address)
            if addr.city:
                dest_city = addr.city
            if addr.country:
                dest_country = addr.country
            dest_str = f"{dest_city}, {dest_country}"

    # ---- Xác định toàn bộ tuyến đường (full_route) ----
    full_route = []

    # Nếu Shipment Tracking đã có transit_route (dữ liệu thực từ sync),
    # ưu tiên dùng dữ liệu đó thay vì tự sinh route lý thuyết.
    if shipment_doc and shipment_doc.transit_route:
        for row in shipment_doc.transit_route:
            if row.location:
                loc_coords = geocode_location(row.location, "")
                if loc_coords:
                    full_route.append(loc_coords)

    if not full_route:
        origin_coords = geocode_location(origin_city, origin_country) or [21.0285, 105.8542]
        dest_coords = geocode_location(dest_city, dest_country) or [10.8231, 106.6297]

        if method == "Ocean":
            full_route = get_maritime_waypoints(origin_coords, dest_coords)
        elif method == "Air":
            full_route = get_air_waypoints(origin_coords, dest_coords)
        else:
            full_route = build_route([origin_coords, dest_coords], points_per_segment=4)

    # ---- Xác định tiến độ (progress) ----
    progress = 0.5
    status_text = "Đang vận chuyển (In Transit)"

    if method == "Air":
        current_location = "Đang bay qua không phận Quốc tế"
    elif method == "Ocean":
        current_location = "Đang trên biển (Maritime Transit)"
    else:
        current_location = "Đang trên tuyến đường bộ"

    if docstatus == 1 and status in ["Completed", "Received", "Closed", "Giao hàng thành công", "Delivered"]:
        progress = 1.0
        status_text = "Đã giao hàng thành công"
        current_location = dest_str
        if shipment_doc and shipment_doc.transit_route:
            current_location = shipment_doc.transit_route[-1].location
    elif docstatus == 2 or docstatus == 0:
        progress = 0.0
        status_text = "Chờ xử lý"
        current_location = origin_str
        if shipment_doc and shipment_doc.transit_route:
            current_location = shipment_doc.transit_route[0].location

    # ---- Cắt current_route trực tiếp theo tỉ lệ progress ----
    # (thay cho các nhánh if/else thủ công cũ, vốn dễ sai khi số lượng
    # điểm trong full_route thay đổi)
    if not full_route:
        current_route = []
    elif progress <= 0.0:
        current_route = [full_route[0]]
    elif progress >= 1.0:
        current_route = full_route
    else:
        cut_index = max(1, int(len(full_route) * progress))
        current_route = full_route[: cut_index + 1]
        if shipment_doc and shipment_doc.transit_route and len(shipment_doc.transit_route) > 1:
            current_location = shipment_doc.transit_route[-2].location

    return {
        "status": "success",
        "data": {
            "method": method,
            "route": current_route,
            "full_route": full_route,
            "progress": progress,
            "status_text": status_text,
            "current_location": current_location,
            "docname": docname,
        },
    }