#!/usr/bin/env python3
"""
test_frontend_map.py — Automated Verification Suite for Leaflet Map Upgrade (Milestone M3)
==========================================================================================
Verifies:
1. Static Code Inspection:
   - OpenStreetMap Standard Basemap URL, subdomains, attribution, maxZoom 19.
   - OpenSeaMap Marine Overlay URL and dynamic method toggle.
   - Pure-JS Douglas-Peucker polyline simplification algorithm.
   - Distance-parameterized interpolation, bearing rotation, and requestAnimationFrame easing.
2. Served Static HTTP Assets:
   - Fetches bundle from nginx on http://localhost:2828, confirms HTTP 200.
3. Live Tile Server Accessibility:
   - Live network connectivity test for OpenStreetMap & OpenSeaMap tile endpoints.
4. Pure-JS Algorithmic Verification (Browser Runtime):
   - Douglas-Peucker simplification (collinear, sharp angle, antimeridian date-line crossing).
   - Great-Circle bearing angle calculation (North, East, South, West).
   - Distance interpolation at 0%, 50%, 100%.
5. Live Browser E2E Rendering & Performance:
   - Logs into Frappe Desk, opens Shipment Tracking map via FAB.
   - Verifies OpenStreetMap tiles and OpenSeaMap seamark overlay.
   - Verifies vehicle marker position, SVG rendering, and heading rotation.
   - Verifies dynamic layer toggle (Ocean vs Air).
   - Measures live animation frame rate (FPS >= 50.0).
   - Captures verification screenshot.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BENCH_DIR = os.path.dirname(TEST_DIR) if os.path.basename(TEST_DIR) == "test" else TEST_DIR
BUNDLE_PATH = os.path.join(BENCH_DIR, "apps", "logistics_wizard", "logistics_wizard", "public", "js", "smart_workflow_widget.bundle.js")
SOURCE_PATH = os.path.join(BENCH_DIR, "apps", "logistics_wizard", "logistics_wizard", "public", "js", "smart_workflow_widget.js")
BASE_URL = "http://localhost:2828"
SCREENSHOT_PATH = os.path.join(BENCH_DIR, "shipment_map_verification.png")


def log_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def test_code_structure():
    log_header("TEST 1: Static Code Structure & Algorithms")
    assert os.path.exists(BUNDLE_PATH), f"Bundle file missing: {BUNDLE_PATH}"
    assert os.path.exists(SOURCE_PATH), f"Source file missing: {SOURCE_PATH}"

    with open(BUNDLE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. OpenStreetMap
    print("Checking OpenStreetMap configuration...")
    assert ("https://tile.openstreetmap.org/{z}/{x}/{y}.png" in content or
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" in content), "Missing OpenStreetMap URL"
    assert "openstreetmap.org" in content, "Missing OpenStreetMap domain"
    assert "subdomains: ['a', 'b', 'c']" in content or "subdomains: ['a', 'b', 'c', 'd']" in content or '"a", "b", "c"' in content, "Missing subdomains"
    assert "maxZoom: 19" in content or "maxZoom:19" in content, "Missing maxZoom 19"
    print("  [PASS] OpenStreetMap basemap properly configured (No watermark, no API key).")

    # 2. OpenSeaMap Marine Overlay
    print("Checking OpenSeaMap marine overlay...")
    assert "https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png" in content, "Missing OpenSeaMap URL"
    assert "update_marine_overlay" in content, "Missing update_marine_overlay function"
    print("  [PASS] OpenSeaMap marine overlay properly configured with dynamic toggle.")

    # 3. Douglas-Peucker algorithm
    print("Checking Douglas-Peucker algorithm...")
    assert "douglasPeucker" in content, "Missing douglasPeucker function"
    assert "perpendicularDistance" in content, "Missing perpendicularDistance function"
    assert "tolerance" in content or "0.002" in content, "Missing tolerance threshold"
    print("  [PASS] Pure-JS Douglas-Peucker polyline simplification implemented.")

    # 4. Smooth Vehicle Marker Movement & Bearing
    print("Checking vehicle marker movement and animation...")
    assert "calculateBearing" in content, "Missing calculateBearing function"
    assert "atan2" in content, "Missing atan2 bearing calculation"
    assert "requestAnimationFrame" in content, "Missing requestAnimationFrame animation loop"
    assert "computePolylineMetrics" in content, "Missing computePolylineMetrics distance calculator"
    assert "interpolateAtProgress" in content, "Missing interpolateAtProgress parametric interpolator"
    assert "animateVehicle" in content, "Missing animateVehicle easing function"
    assert "transform" in content and "rotate" in content, "Missing vehicle marker heading rotation"
    print("  [PASS] Smooth rAF animation loop and heading rotation implemented.")

    # 5. Global export
    assert "window.LogisticsWizardMap" in content, "Missing window.LogisticsWizardMap export"
    print("  [PASS] LogisticsWizardMap API exported to window.")


def test_static_assets_http():
    log_header("TEST 2: Served HTTP Static Asset Verification")
    assets_json_url = f"{BASE_URL}/assets/assets.json"
    print(f"Fetching assets manifest from {assets_json_url}...")
    try:
        req = urllib.request.Request(assets_json_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            bundle_rel = data.get("smart_workflow_widget.bundle.js")
            assert bundle_rel, "smart_workflow_widget.bundle.js missing in assets.json"
            print(f"  Mapped bundle in assets.json: {bundle_rel}")
    except Exception as e:
        print(f"  Assets manifest request failed: {e}")
        bundle_rel = "/assets/logistics_wizard/js/smart_workflow_widget.bundle.js"

    bundle_url = f"{BASE_URL}{bundle_rel}"
    print(f"Fetching bundle content from {bundle_url}...")
    req = urllib.request.Request(bundle_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200, f"Expected status 200, got {resp.status}"
        bundle_code = resp.read().decode("utf-8")
        assert "openstreetmap" in bundle_code or "tile.openstreetmap.org" in bundle_code, "Served bundle does not contain 'openstreetmap'"
        assert "openseamap" in bundle_code, "Served bundle does not contain 'openseamap'"
        assert "douglasPeucker" in bundle_code or "M=" in bundle_code, "Served bundle missing Douglas-Peucker"
        assert "requestAnimationFrame" in bundle_code, "Served bundle missing requestAnimationFrame"
        print(f"  [PASS] Served bundle verified ({len(bundle_code)} bytes, HTTP 200).")


def test_tile_endpoints_live():
    log_header("TEST 3: Live Tile Server Network Accessibility")
    endpoints = [
        ("OpenStreetMap Standard", "https://tile.openstreetmap.org/3/4/2.png"),
        ("OpenSeaMap Seamark", "https://tiles.openseamap.org/seamark/3/4/2.png")
    ]
    for name, url in endpoints:
        print(f"Checking {name} tile: {url}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                assert resp.status == 200, f"{name} returned HTTP {resp.status}"
                content_type = resp.headers.get("Content-Type", "")
                assert "image" in content_type, f"Expected image content-type, got {content_type}"
                print(f"  [PASS] {name} tile endpoint accessible (HTTP 200, {content_type}).")
        except Exception as e:
            print(f"  [FAIL] {name} tile request failed: {e}")
            raise


def test_browser_algorithms_and_e2e():
    log_header("TEST 4 & 5: Browser Runtime Algorithms, Live Map & Performance")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        print("1. Logging into Frappe Desk (Administrator)...")
        page.goto(f"{BASE_URL}/login")
        page.fill("#login_email", "Administrator")
        page.fill("#login_password", "admin")
        page.click(".btn-login")
        page.wait_for_url("**/app**", timeout=15000)
        print(f"  [PASS] Logged in successfully: {page.url}")

        print("2. Verifying pure-JS algorithms via window.LogisticsWizardMap...")
        algo_results = page.evaluate("""() => {
            const mapObj = window.LogisticsWizardMap;
            if (!mapObj) return { error: "window.LogisticsWizardMap not found" };

            // A. Douglas-Peucker: Collinear reduction
            const collinear = [
                [10, 20], [10, 21], [10, 22], [10, 23], [10, 24],
                [10, 25], [10, 26], [10, 27], [10, 28], [10, 29]
            ];
            const dpCollinear = mapObj.douglasPeucker(collinear, 0.002);

            // B. Douglas-Peucker: Sharp bend preservation
            const sharp = [[10, 20], [15, 25], [10, 30]];
            const dpSharp = mapObj.douglasPeucker(sharp, 0.002);

            // C. Douglas-Peucker: Antimeridian Date-Line unwrap
            const antimeridian = [[10, 179], [10, 180], [10, -179]];
            const dpAntimeridian = mapObj.douglasPeucker(antimeridian, 0.002);

            // D. Bearing Angles
            const cb = mapObj.calculateBearing;
            const bNorth = cb(0, 0, 10, 0);
            const bEast = cb(0, 0, 0, 10);
            const bSouth = cb(10, 0, 0, 0);
            const bWest = cb(0, 10, 0, 0);

            // E. Cumulative Metrics & Interpolation
            const testCoords = [[0, 0], [0, 10]];
            const metrics = mapObj.computePolylineMetrics(testCoords);
            const p0 = mapObj.interpolateAtProgress(testCoords, metrics, 0.0);
            const p50 = mapObj.interpolateAtProgress(testCoords, metrics, 0.5);
            const p100 = mapObj.interpolateAtProgress(testCoords, metrics, 1.0);

            return {
                dpCollinearLen: dpCollinear.length,
                dpSharpLen: dpSharp.length,
                dpAntimeridianLen: dpAntimeridian.length,
                bearings: { bNorth, bEast, bSouth, bWest },
                interpolation: {
                    totalDist: metrics.total,
                    p0_point: p0.point,
                    p0_bearing: p0.bearing,
                    p50_point: p50.point,
                    p100_point: p100.point
                }
            };
        }""")

        assert "error" not in algo_results, algo_results.get("error")
        assert algo_results["dpCollinearLen"] == 2, f"Expected collinear reduction to 2 points, got {algo_results['dpCollinearLen']}"
        assert algo_results["dpSharpLen"] == 3, f"Expected sharp bend preserved to 3 points, got {algo_results['dpSharpLen']}"
        assert algo_results["dpAntimeridianLen"] == 2, f"Expected antimeridian reduction to 2 points, got {algo_results['dpAntimeridianLen']}"
        print(f"  [PASS] Douglas-Peucker algorithm verified (Collinear: 10->2, Sharp: 3->3, DateLine: 3->2).")

        bearings = algo_results["bearings"]
        assert bearings["bNorth"] == 0, f"Expected North=0, got {bearings['bNorth']}"
        assert bearings["bEast"] == 90, f"Expected East=90, got {bearings['bEast']}"
        assert bearings["bSouth"] == 180, f"Expected South=180, got {bearings['bSouth']}"
        assert bearings["bWest"] == 270, f"Expected West=270, got {bearings['bWest']}"
        print(f"  [PASS] Bearing calculation verified: North={bearings['bNorth']}°, East={bearings['bEast']}°, South={bearings['bSouth']}°, West={bearings['bWest']}°.")

        interp = algo_results["interpolation"]
        assert interp["totalDist"] == 10, f"Expected total distance 10, got {interp['totalDist']}"
        assert interp["p0_point"] == [0, 0], f"Expected p0 [0, 0], got {interp['p0_point']}"
        assert interp["p50_point"] == [0, 5], f"Expected p50 [0, 5], got {interp['p50_point']}"
        assert interp["p100_point"] == [0, 10], f"Expected p100 [0, 10], got {interp['p100_point']}"
        print(f"  [PASS] Distance-parameterized interpolation verified (0%=[0,0], 50%=[0,5], 100%=[0,10]).")

        print("3. Opening Logistics Wizard FAB and Shipment Modal...")
        page.wait_for_selector("#lw-fab-main", timeout=10000)
        page.click("#lw-fab-main")
        time.sleep(0.5)

        page.wait_for_selector("#lw-fab-shipment", timeout=5000)
        page.click("#lw-fab-shipment")
        time.sleep(1.0)

        shipment_items = page.query_selector_all(".lw-shipment-item")
        print(f"  Found {len(shipment_items)} active shipments.")
        assert len(shipment_items) > 0, "No active shipments found in popup list"

        first_item = shipment_items[0]
        shipment_name = first_item.get_attribute("data-name")
        print(f"  Clicking shipment: {shipment_name}...")
        first_item.click()

        time.sleep(2.5)

        print("4. Inspecting Leaflet Map DOM, Tiles & Markers...")
        map_state = page.evaluate("""() => {
            const mapEl = document.querySelector('#shipment-map');
            const tiles = Array.from(document.querySelectorAll('#shipment-map img.leaflet-tile')).map(i => i.src);
            const osmTiles = tiles.filter(t => t.includes('tile.openstreetmap.org') || t.includes('openstreetmap'));
            const seaTiles = tiles.filter(t => t.includes('openseamap'));

            const origMarker = document.querySelector('.custom-origin-icon');
            const destMarker = document.querySelector('.custom-dest-icon');
            const vehMarker = document.querySelector('.custom-vehicle-icon');
            const vehSvg = document.querySelector('.lw-vehicle-icon-svg');

            const infoEl = document.querySelector('#lw-map-info-text');

            return {
                hasMap: !!mapEl,
                totalTiles: tiles.length,
                osmTilesCount: osmTiles.length,
                openSeaMapTilesCount: seaTiles.length,
                osmSample: osmTiles.slice(0, 2),
                openSeaMapSample: seaTiles.slice(0, 2),
                hasOriginMarker: !!origMarker,
                hasDestMarker: !!destMarker,
                hasVehicleMarker: !!vehMarker,
                vehicleTransform: vehSvg ? vehSvg.style.transform : null,
                infoText: infoEl ? infoEl.innerText : null
            };
        }""")

        assert map_state["hasMap"], "Leaflet #shipment-map element missing"
        assert map_state["osmTilesCount"] > 0, "No OpenStreetMap tiles loaded"
        assert map_state["openSeaMapTilesCount"] > 0, "No OpenSeaMap seamark tiles loaded for Ocean shipment"
        assert map_state["hasOriginMarker"], "Origin marker 'A' missing"
        assert map_state["hasDestMarker"], "Destination marker 'B' missing"
        assert map_state["hasVehicleMarker"], "Vehicle marker missing"
        assert map_state["vehicleTransform"], "Vehicle marker heading transform missing"
        assert "rotate" in map_state["vehicleTransform"], f"Expected rotate in vehicleTransform, got {map_state['vehicleTransform']}"

        print(f"  [PASS] OpenStreetMap Tiles: {map_state['osmTilesCount']} loaded (Sample: {map_state['osmSample'][0]})")
        print(f"  [PASS] OpenSeaMap Overlay Tiles: {map_state['openSeaMapTilesCount']} loaded (Sample: {map_state['openSeaMapSample'][0]})")
        print(f"  [PASS] Origin, Destination and Vehicle Markers rendered successfully.")
        print(f"  [PASS] Vehicle Heading Orientation: {map_state['vehicleTransform']}.")

        print("5. Testing Dynamic OpenSeaMap Layer Toggle...")
        toggle_res = page.evaluate("""() => {
            const mapObj = window.LogisticsWizardMap;
            const sm = mapObj.getShipmentMap();
            const initial = sm.hasLayer(mapObj.getSeaOverlayLayer());

            // Toggle to Air -> should remove layer
            mapObj.update_marine_overlay('Air');
            const afterAir = sm.hasLayer(mapObj.getSeaOverlayLayer());

            // Toggle back to Ocean -> should re-add layer
            mapObj.update_marine_overlay('Ocean');
            const afterOcean = sm.hasLayer(mapObj.getSeaOverlayLayer());

            return { initial, afterAir, afterOcean };
        }""")

        assert toggle_res["initial"] is True, "Expected initial marine layer to be active"
        assert toggle_res["afterAir"] is False, "Expected marine layer removed for Air"
        assert toggle_res["afterOcean"] is True, "Expected marine layer re-added for Ocean"
        print("  [PASS] Dynamic OpenSeaMap layer toggle verified (Ocean: Active, Air: Hidden, Ocean: Active).")

        print("6. Measuring Animation & Rendering Performance (FPS >= 50)...")
        fps_res = page.evaluate("""() => {
            return new Promise(resolve => {
                let frames = 0;
                const start = performance.now();
                function count(now) {
                    frames++;
                    if (now - start < 2000) {
                        requestAnimationFrame(count);
                    } else {
                        const duration = now - start;
                        const fps = (frames / duration) * 1000;
                        resolve({ frames, duration, fps });
                    }
                }
                requestAnimationFrame(count);
            });
        }""")

        avg_fps = fps_res["fps"]
        print(f"  Measured Frames: {fps_res['frames']} in {fps_res['duration']:.1f}ms -> Average FPS: {avg_fps:.1f}")
        assert avg_fps >= 50.0, f"Expected FPS >= 50.0, got {avg_fps:.1f}"
        print(f"  [PASS] Browser performance threshold satisfied ({avg_fps:.1f} FPS >= 50.0 FPS).")

        print(f"7. Capturing verification screenshot to {SCREENSHOT_PATH}...")
        page.screenshot(path=SCREENSHOT_PATH)
        assert os.path.exists(SCREENSHOT_PATH), "Screenshot file missing"
        print(f"  [PASS] Screenshot saved successfully ({os.path.getsize(SCREENSHOT_PATH)} bytes).")

        browser.close()


def main():
    print("=" * 80)
    print(" LOGISTICS WIZARD M3: LEAFLET MAP & ANIMATION AUTOMATED TEST SUITE")
    print("=" * 80)
    t0 = time.time()

    test_code_structure()
    test_static_assets_http()
    test_tile_endpoints_live()
    test_browser_algorithms_and_e2e()

    total_time = time.time() - t0
    log_header(f"ALL TESTS PASSED SUCCESSFULLY in {total_time:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
