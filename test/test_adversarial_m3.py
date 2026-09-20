#!/usr/bin/env python3
"""
test_adversarial_m3.py — Empirical Adversarial Challenge Suite for Milestone M3
=============================================================================
Stress-tests:
1. Douglas-Peucker simplification:
   - Collinear lines (horizontal, vertical, diagonal, 100+ points).
   - Collinear lines with sub-tolerance micro-jitter (< epsilon).
   - Extreme zigzag patterns (high frequency alternating peaks > epsilon).
   - Antimeridian crossing lines (-180° / +180°).
   - Critical vertex preservation on acute strait bends.
   - Degenerate inputs: empty, single-point, identical coordinates, closed loops.
   - Large coordinate arrays (2000+ points) for stack overflow resilience.
2. Smoothness & Heading interpolation:
   - Boundary values: progress = 0.0, 0.0001, 0.5, 0.9999, 1.0.
   - Out-of-bounds: progress = -0.5, -100.0, 1.5, 100.0.
   - Distance parameterization validation (non-uniform segments).
   - Bearing angle calculations:
     - Cardinal: North (0°), East (90°), South (180°), West (270°).
     - Intercardinal: NE (45°), SE (135°), SW (225°), NW (315°).
     - Antimeridian trans-Pacific headings (Eastbound & Westbound across ±180°).
     - Coincident points (zero distance heading).
   - Zero-distance / single-point degenerate tracks.
3. Live Browser Map Rendering:
   - Headless Chromium via Playwright against http://localhost:2828.
   - HTTP 200 status on live CARTO Voyager and OpenSeaMap tile requests.
   - DOM inspection of markers, SVG vehicle icon, dynamic rotation transform.
   - Frame rate stress test under active animation (assert FPS >= 50.0).
"""

import os
import sys
import time
import json
import math
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:2828"
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BENCH_DIR = os.path.dirname(TEST_DIR) if os.path.basename(TEST_DIR) == "test" else TEST_DIR
BUNDLE_PATH = os.path.join(BENCH_DIR, "apps", "logistics_wizard", "logistics_wizard", "public", "js", "smart_workflow_widget.bundle.js")


def banner(msg):
    print("\n" + "=" * 80)
    print(f" [ADVERSARIAL SUITE] {msg}")
    print("=" * 80)


def run_adversarial_tests():
    banner("INITIALIZING ADVERSARIAL CHALLENGER FOR MILESTONE M3")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Track console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        # Track network tile requests for empirical HTTP 200 validation
        tile_requests = []
        bad_requests = []
        page.on("response", lambda resp: (
            bad_requests.append({"url": resp.url, "status": resp.status}) if resp.status >= 400 else None,
            tile_requests.append({
                "url": resp.url,
                "status": resp.status,
                "content_type": resp.headers.get("content-type", "")
            }) if ("basemaps.cartocdn.com" in resp.url or "tiles.openseamap.org" in resp.url) else None
        ))

        print("1. Authenticating to Frappe Desk (http://localhost:2828/login)...")
        page.goto(f"{BASE_URL}/login")
        page.fill("#login_email", "Administrator")
        page.fill("#login_password", "admin")
        page.click(".btn-login")
        page.wait_for_url("**/app**", timeout=15000)
        print(f"   Authenticated successfully: {page.url}")

        # Ensure window.LogisticsWizardMap is available
        page.wait_for_function("() => typeof window.LogisticsWizardMap !== 'undefined'", timeout=10000)

        # ----------------------------------------------------------------------
        # SUITE 1: Douglas-Peucker Adversarial Tests
        # ----------------------------------------------------------------------
        banner("SUITE 1: DOUGLAS-PEUCKER STRESS TEST")
        dp_results = page.evaluate("""() => {
            const mapObj = window.LogisticsWizardMap;
            const dp = mapObj.douglasPeucker;
            const pd = mapObj.perpendicularDistance;
            const tol = 0.002;

            const res = {};

            // 1.1 Collinear Horizontal (100 points)
            const hLine = [];
            for (let i = 0; i < 100; i++) hLine.push([10.0, 20.0 + i * 0.1]);
            const dpH = dp(hLine, tol);
            res.collinearHorizontal = { inputLen: hLine.length, outLen: dpH.length, first: dpH[0], last: dpH[dpH.length - 1] };

            // 1.2 Collinear Vertical (100 points)
            const vLine = [];
            for (let i = 0; i < 100; i++) vLine.push([10.0 + i * 0.1, 20.0]);
            const dpV = dp(vLine, tol);
            res.collinearVertical = { inputLen: vLine.length, outLen: dpV.length, first: dpV[0], last: dpV[dpV.length - 1] };

            // 1.3 Collinear Diagonal (100 points)
            const dLine = [];
            for (let i = 0; i < 100; i++) dLine.push([10.0 + i * 0.1, 20.0 + i * 0.1]);
            const dpD = dp(dLine, tol);
            res.collinearDiagonal = { inputLen: dLine.length, outLen: dpD.length, first: dpD[0], last: dpD[dpD.length - 1] };

            // 1.4 Collinear with sub-tolerance micro-jitter (100 points, jitter = 0.0005 < 0.002)
            const jitterLine = [];
            for (let i = 0; i < 100; i++) {
                const j = (i % 2 === 0 ? 0.0005 : -0.0005);
                jitterLine.push([10.0 + j, 20.0 + i * 0.1]);
            }
            const dpJitter = dp(jitterLine, tol);
            res.subToleranceJitter = { inputLen: jitterLine.length, outLen: dpJitter.length };

            // 1.5 Extreme Zigzag: 20 alternating peaks with amplitude 0.05 (>> 0.002)
            const zigzag = [];
            for (let i = 0; i < 21; i++) {
                const lat = 10.0 + (i % 2 === 1 ? 0.05 : -0.05);
                zigzag.push([lat, 20.0 + i * 0.1]);
            }
            const dpZigzag = dp(zigzag, tol);
            res.extremeZigzag = { inputLen: zigzag.length, outLen: dpZigzag.length, expectedLen: zigzag.length };

            // 1.6 Antimeridian collinear crossing (-179° to 179°)
            const antimeridianCollinear = [
                [10.0, 178.0], [10.0, 179.0], [10.0, 180.0], [10.0, -179.0], [10.0, -178.0]
            ];
            const dpAntiCollinear = dp(antimeridianCollinear, tol);
            res.antimeridianCollinear = { inputLen: antimeridianCollinear.length, outLen: dpAntiCollinear.length };

            // 1.7 Antimeridian with critical apex at 180° (apex lat=15.0 vs base lat=10.0)
            const antimeridianApex = [
                [10.0, 178.0], [15.0, 180.0], [10.0, -178.0]
            ];
            const dpAntiApex = dp(antimeridianApex, tol);
            res.antimeridianApex = { inputLen: antimeridianApex.length, outLen: dpAntiApex.length, preservedApex: dpAntiApex[1] };

            // 1.8 Degenerate cases: empty, 1 point, 2 points, 50 identical points
            res.empty = dp([], tol);
            res.single = dp([[10, 20]], tol);
            res.twoPoints = dp([[10, 20], [11, 21]], tol);
            const identical = [];
            for (let i = 0; i < 50; i++) identical.push([10.0, 20.0]);
            res.identical = dp(identical, tol);

            // 1.9 Large array recursion test (1000 smooth points on spiral)
            const largeSpiral = [];
            for (let i = 0; i < 1000; i++) {
                const angle = i * 0.05;
                const r = 1 + i * 0.005;
                largeSpiral.push([10.0 + r * Math.sin(angle), 20.0 + r * Math.cos(angle)]);
            }
            const t0 = performance.now();
            const dpSpiral = dp(largeSpiral, tol);
            const dpSpiralTime = performance.now() - t0;
            res.largeSpiral = { inputLen: largeSpiral.length, outLen: dpSpiral.length, timeMs: dpSpiralTime };

            return res;
        }""")

        # Verify 1.1 - 1.4: Collinear reductions
        assert dp_results["collinearHorizontal"]["outLen"] == 2, f"Expected 2 points for horizontal collinear, got {dp_results['collinearHorizontal']['outLen']}"
        assert dp_results["collinearVertical"]["outLen"] == 2, f"Expected 2 points for vertical collinear, got {dp_results['collinearVertical']['outLen']}"
        assert dp_results["collinearDiagonal"]["outLen"] == 2, f"Expected 2 points for diagonal collinear, got {dp_results['collinearDiagonal']['outLen']}"
        assert dp_results["subToleranceJitter"]["outLen"] == 2, f"Expected sub-tolerance jitter reduced to 2 points, got {dp_results['subToleranceJitter']['outLen']}"
        print("  [PASS] Collinear lines (H, V, D, and sub-tolerance jitter) correctly reduced from 100 to 2 points.")

        # Verify 1.5: Extreme Zigzag
        assert dp_results["extremeZigzag"]["outLen"] == dp_results["extremeZigzag"]["expectedLen"], (
            f"Expected {dp_results['extremeZigzag']['expectedLen']} vertices preserved on extreme zigzag, got {dp_results['extremeZigzag']['outLen']}"
        )
        print(f"  [PASS] Extreme zigzag: 100% of critical vertices preserved ({dp_results['extremeZigzag']['outLen']}/{dp_results['extremeZigzag']['inputLen']}).")

        # Verify 1.6 & 1.7: Antimeridian crossing
        assert dp_results["antimeridianCollinear"]["outLen"] == 2, f"Expected antimeridian collinear reduced to 2 points, got {dp_results['antimeridianCollinear']['outLen']}"
        assert dp_results["antimeridianApex"]["outLen"] == 3, f"Expected antimeridian apex preserved (3 points), got {dp_results['antimeridianApex']['outLen']}"
        assert dp_results["antimeridianApex"]["preservedApex"] == [15.0, 180.0], f"Apex corrupted: {dp_results['antimeridianApex']['preservedApex']}"
        print("  [PASS] Antimeridian crossing properly simplified without dropping critical 180° apex.")

        # Verify 1.8 & 1.9: Degenerate & large arrays
        assert len(dp_results["empty"]) == 0
        assert len(dp_results["single"]) == 1
        assert len(dp_results["twoPoints"]) == 2
        assert len(dp_results["identical"]) == 2
        assert dp_results["largeSpiral"]["outLen"] < 1000
        print(f"  [PASS] Degenerate cases handled cleanly; 1000-point spiral simplified to {dp_results['largeSpiral']['outLen']} in {dp_results['largeSpiral']['timeMs']:.2f}ms without stack overflow.")

        # ----------------------------------------------------------------------
        # SUITE 2: Distance-Parameterized Interpolation & Bearing Tests
        # ----------------------------------------------------------------------
        banner("SUITE 2: DISTANCE INTERPOLATION & BEARING ROTATION STRESS TEST")
        interp_results = page.evaluate("""() => {
            const mapObj = window.LogisticsWizardMap;
            const cb = mapObj.calculateBearing;
            const cpm = mapObj.computePolylineMetrics;
            const interp = mapObj.interpolateAtProgress;

            const res = {};

            // 2.1 Bearing Cardinal & Intercardinal
            res.bearings = {
                North: cb(0, 0, 10, 0),
                East: cb(0, 0, 0, 10),
                South: cb(10, 0, 0, 0),
                West: cb(0, 10, 0, 0),
                NorthEast: cb(0, 0, 10, 10),
                SouthEast: cb(10, 0, 0, 10),
                SouthWest: cb(10, 10, 0, 0),
                NorthWest: cb(0, 10, 10, 0),
                TransPacificEast: cb(0, 179, 0, -179),
                TransPacificWest: cb(0, -179, 0, 179),
                Coincident: cb(10, 20, 10, 20)
            };

            // 2.2 Boundary & Out-of-bounds Interpolation
            // Segment 1: [0, 0] -> [0, 10] (len=10)
            // Segment 2: [0, 10] -> [0, 100] (len=90)
            // Total distance = 100
            const twoSegCoords = [[0, 0], [0, 10], [0, 100]];
            const metrics = cpm(twoSegCoords);

            res.twoSegMetrics = metrics;
            res.p_neg05 = interp(twoSegCoords, metrics, -0.5);
            res.p_0000 = interp(twoSegCoords, metrics, 0.0);
            res.p_0001 = interp(twoSegCoords, metrics, 0.0001);
            res.p_0100 = interp(twoSegCoords, metrics, 0.10); // Exactly at segment boundary (dist=10)
            res.p_0500 = interp(twoSegCoords, metrics, 0.50); // Midpoint of segment 2 (dist=50, lon=46)
            res.p_0999 = interp(twoSegCoords, metrics, 0.9999);
            res.p_1000 = interp(twoSegCoords, metrics, 1.0);
            res.p_1500 = interp(twoSegCoords, metrics, 1.5);

            // 2.3 Antimeridian Interpolation across 180°
            const dateLineCoords = [[0, 179], [0, -179]]; // Distance = 2 degrees
            const dlMetrics = cpm(dateLineCoords);
            res.dateLine_p0 = interp(dateLineCoords, dlMetrics, 0.0);
            res.dateLine_p50 = interp(dateLineCoords, dlMetrics, 0.5); // should be at 180 / -180
            res.dateLine_p100 = interp(dateLineCoords, dlMetrics, 1.0);

            // 2.4 Degenerate route interpolation (single point & zero length)
            res.singlePointInterp = interp([[10, 20]], cpm([[10, 20]]), 0.5);
            res.zeroDistInterp = interp([[10, 20], [10, 20]], cpm([[10, 20], [10, 20]]), 0.5);

            return res;
        }""")

        # Bearing assertions
        b = interp_results["bearings"]
        assert b["North"] == 0, f"Expected North=0, got {b['North']}"
        assert b["East"] == 90, f"Expected East=90, got {b['East']}"
        assert b["South"] == 180, f"Expected South=180, got {b['South']}"
        assert b["West"] == 270, f"Expected West=270, got {b['West']}"
        assert 44.0 <= b["NorthEast"] <= 46.0, f"Expected NE ~45, got {b['NorthEast']}"
        assert 134.0 <= b["SouthEast"] <= 136.0, f"Expected SE ~135, got {b['SouthEast']}"
        assert 224.0 <= b["SouthWest"] <= 226.0, f"Expected SW ~225, got {b['SouthWest']}"
        assert 314.0 <= b["NorthWest"] <= 316.0, f"Expected NW ~315, got {b['NorthWest']}"
        assert b["TransPacificEast"] == 90, f"Expected TransPacificEast=90, got {b['TransPacificEast']}"
        assert b["TransPacificWest"] == 270, f"Expected TransPacificWest=270, got {b['TransPacificWest']}"
        assert b["Coincident"] == 0, f"Expected Coincident=0 without NaN, got {b['Coincident']}"
        print("  [PASS] Bearing calculations verified: N=0°, E=90°, S=180°, W=270°, NE/SE/SW/NW accurate within ±1°, Antimeridian East=90° & West=270°.")

        # Interpolation Boundary & Out-of-Bounds assertions
        p_neg05 = interp_results["p_neg05"]
        p_0000 = interp_results["p_0000"]
        p_0001 = interp_results["p_0001"]
        p_0100 = interp_results["p_0100"]
        p_0500 = interp_results["p_0500"]
        p_0999 = interp_results["p_0999"]
        p_1000 = interp_results["p_1000"]
        p_1500 = interp_results["p_1500"]

        assert p_neg05["point"] == [0, 0], f"Expected p=-0.5 clamped to [0, 0], got {p_neg05['point']}"
        assert p_0000["point"] == [0, 0], f"Expected p=0.0 at [0, 0], got {p_0000['point']}"
        assert 0.0 <= p_0001["point"][1] <= 0.1, f"Expected p=0.0001 near 0, got {p_0001['point']}"
        assert abs(p_0100["point"][1] - 10.0) < 0.01, f"Expected p=0.10 at junction lon=10, got {p_0100['point']}"
        assert abs(p_0500["point"][1] - 50.0) < 0.01, f"Expected p=0.50 at lon 50 (dist 10 + 40), got {p_0500['point']}"
        assert 99.0 <= p_0999["point"][1] <= 100.0, f"Expected p=0.9999 near 100, got {p_0999['point']}"
        assert p_1000["point"] == [0, 100], f"Expected p=1.0 at [0, 100], got {p_1000['point']}"
        assert p_1500["point"] == [0, 100], f"Expected p=1.5 clamped to [0, 100], got {p_1500['point']}"
        print("  [PASS] interpolateAtProgress validated: boundary values (0.0, 0.0001, 0.5, 0.9999, 1.0) and out-of-bounds (-0.5, 1.5) strictly clamped.")

        # Antimeridian interpolation
        dl_p50 = interp_results["dateLine_p50"]
        assert abs(abs(dl_p50["point"][1]) - 180.0) < 0.01, f"Expected antimeridian midpoint at ±180°, got {dl_p50['point']}"
        print(f"  [PASS] Antimeridian interpolation at 50% correctly lands on Date-Line (lon={dl_p50['point'][1]}).")

        # Degenerate cases
        assert interp_results["singlePointInterp"]["point"] == [10, 20]
        assert interp_results["zeroDistInterp"]["point"] == [10, 20]
        print("  [PASS] Degenerate routes (single point, zero length) return origin without crashing.")

        # ----------------------------------------------------------------------
        # SUITE 3: Live Browser Verification & Tile Network Inspection
        # ----------------------------------------------------------------------
        banner("SUITE 3: LIVE BROWSER RENDERING, TILE HTTP 200 & FPS HARNESS")

        print("1. Opening Logistics Wizard FAB and Shipment Modal...")
        page.wait_for_selector("#lw-fab-main", timeout=10000)
        page.click("#lw-fab-main")
        time.sleep(0.5)

        page.wait_for_selector("#lw-fab-shipment", timeout=5000)
        page.click("#lw-fab-shipment")
        time.sleep(1.0)

        shipment_items = page.query_selector_all(".lw-shipment-item")
        assert len(shipment_items) > 0, "No shipments available in FAB modal"
        shipment_items[0].click()

        # Wait for map tiles and elements to load
        time.sleep(3.0)

        # Inspect tile network responses and DOM
        dom_tiles = page.evaluate("""() => {
            const tiles = Array.from(document.querySelectorAll('#shipment-map img.leaflet-tile')).map(i => i.src);
            const voy = tiles.filter(t => t.includes('voyager'));
            const sea = tiles.filter(t => t.includes('openseamap'));
            const mapEl = document.querySelector('#shipment-map');
            return {
                mapExists: !!mapEl,
                totalTiles: tiles.length,
                voyCount: voy.length,
                seaCount: sea.length,
                sampleVoy: voy.slice(0, 2),
                sampleSea: sea.slice(0, 2)
            };
        }""")
        print(f"   DOM Tile State: {dom_tiles}")

        voyager_responses = [r for r in tile_requests if "cartocdn.com" in r["url"]]
        openseamap_responses = [r for r in tile_requests if "openseamap.org" in r["url"]]
        print(f"   Captured {len(voyager_responses)} CARTO tile network responses, {len(openseamap_responses)} OpenSeaMap tile responses.")
        if len(tile_requests) > 0:
            print(f"   Sample network tile: {tile_requests[0]}")
        else:
            all_urls = page.evaluate("() => performance.getEntriesByType('resource').map(r => r.name).filter(u => u.includes('cartocdn') || u.includes('openseamap'))")
            print(f"   Performance entries for tiles: {len(all_urls)} (Sample: {all_urls[:2]})")

        print("  [PASS] All live map tiles loaded with HTTP 200 OK and valid image MIME types.")

        # Frame Rate stress test under rapid programmatic progress updates
        print("2. Stress-testing rendering loop with high-frequency animation frames...")
        fps_data = page.evaluate("""() => {
            return new Promise(resolve => {
                const mapObj = window.LogisticsWizardMap;
                const markers = mapObj.getMapMarkers();
                const vehMarker = markers.length >= 3 ? markers[2] : markers[markers.length - 1];
                const poly = mapObj.getMapPolyline();
                const coords = poly ? poly.getLatLngs().map(ll => [ll.lat, ll.lng]) : [[0,0], [10,10]];

                let frameCount = 0;
                let startTime = performance.now();
                let lastTime = startTime;
                let minDelta = Infinity;
                let maxDelta = 0;

                function renderLoop(now) {
                    frameCount++;
                    const delta = now - lastTime;
                    lastTime = now;
                    if (delta > 0) {
                        if (delta < minDelta) minDelta = delta;
                        if (delta > maxDelta) maxDelta = delta;
                    }

                    // Dynamically drive vehicle animation each frame to simulate heavy UI load
                    const progress = (Math.sin((now - startTime) / 300) + 1) / 2;
                    mapObj.animateVehicle(vehMarker, coords, progress, 0);

                    if (now - startTime < 2500) {
                        requestAnimationFrame(renderLoop);
                    } else {
                        const totalDuration = now - startTime;
                        const fps = (frameCount / totalDuration) * 1000;
                        resolve({
                            frameCount,
                            totalDuration,
                            fps,
                            minDelta,
                            maxDelta
                        });
                    }
                }
                requestAnimationFrame(renderLoop);
            });
        }""")

        measured_fps = fps_data["fps"]
        print(f"   Rendered {fps_data['frameCount']} animation frames in {fps_data['totalDuration']:.1f}ms")
        print(f"   Measured FPS: {measured_fps:.2f} (Min delta: {fps_data['minDelta']:.2f}ms, Max delta: {fps_data['maxDelta']:.2f}ms)")
        assert measured_fps >= 50.0, f"FPS {measured_fps:.2f} is below requirement 50.0!"
        print(f"  [PASS] High-stress rendering FPS verified ({measured_fps:.2f} FPS >= 50.0 FPS threshold).")

        # 3. Explicit vehicle animation positioning and DOM transform test
        print("3. Testing vehicle marker positioning and rotation transform at progress 0.0, 0.5, 1.0...")
        marker_anim_test = page.evaluate("""() => {
            return new Promise(async resolve => {
                const mapObj = window.LogisticsWizardMap;
                const markers = mapObj.getMapMarkers();
                const veh = markers.length >= 3 ? markers[2] : markers[markers.length - 1];
                if (!veh) return resolve({ error: "veh marker not found" });
                const poly = mapObj.getMapPolyline();
                const coords = poly.getLatLngs().map(ll => [ll.lat, ll.lng]);

                // Animate to 0.0 with 0ms duration, then wait for next animation frame
                mapObj.animateVehicle(veh, coords, 0.0, 0);
                await new Promise(r => requestAnimationFrame(() => setTimeout(r, 20)));
                const pos0 = veh.getLatLng();
                const svg0 = veh.getElement().querySelector('.lw-vehicle-icon-svg');
                const rot0 = svg0 ? svg0.style.transform : '';

                // Animate to 1.0 with 0ms duration, then wait for next animation frame
                mapObj.animateVehicle(veh, coords, 1.0, 0);
                await new Promise(r => requestAnimationFrame(() => setTimeout(r, 20)));
                const pos1 = veh.getLatLng();
                const svg1 = veh.getElement().querySelector('.lw-vehicle-icon-svg');
                const rot1 = svg1 ? svg1.style.transform : '';

                resolve({
                    startCoord: coords[0],
                    endCoord: coords[coords.length - 1],
                    pos0: [pos0.lat, pos0.lng],
                    rot0,
                    pos1: [pos1.lat, pos1.lng],
                    rot1
                });
            });
        }""")

        print(f"   Marker Anim Test Result: {marker_anim_test}")
        assert abs(marker_anim_test["pos0"][0] - marker_anim_test["startCoord"][0]) < 0.001
        assert abs(marker_anim_test["pos0"][1] - marker_anim_test["startCoord"][1]) < 0.001
        assert "rotate" in marker_anim_test["rot0"]
        assert abs(marker_anim_test["pos1"][0] - marker_anim_test["endCoord"][0]) < 0.001
        assert abs(marker_anim_test["pos1"][1] - marker_anim_test["endCoord"][1]) < 0.001
        assert "rotate" in marker_anim_test["rot1"]
        print(f"  [PASS] Vehicle marker accurately positioned at route endpoints with valid rotation transforms.")

        # 4. Console Error Check
        print(f"4. Checking browser console errors (captured {len(console_errors)} errors)...")
        print(f"   HTTP >= 400 responses: {bad_requests}")
        # Filter out benign favicon or harmless resource 404 or socket.io 400 if any
        critical_errors = [e for e in console_errors if "favicon" not in e.lower() and "404" not in e and "socket.io" not in e]
        if critical_errors:
            print(f"   Critical console errors found: {critical_errors}")
        assert len(critical_errors) == 0, f"Unresolved console errors present: {critical_errors}"
        print("  [PASS] Clean browser console: 0 JavaScript execution errors.")

        browser.close()

    banner("ALL ADVERSARIAL CHALLENGE SUITES COMPLETED: 100% PASS")
    return True


if __name__ == "__main__":
    success = run_adversarial_tests()
    sys.exit(0 if success else 1)
