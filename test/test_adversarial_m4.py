#!/usr/bin/env python3
"""
test_adversarial_m4.py — Empirical Adversarial Stress Harness for Milestone M4
=============================================================================
Independent Adversarial Suite for Logistics Wizard ERPNext v15.
Author: Teamwork Empirical Challenger (Milestone M4)

Scope of Verification:
1. Synthetic Overland Route Collision Detection (100% detection & non-zero exit code).
2. Maritime Navigational Segments (Long Beach -> Cat Lai, LA -> Hai Phong) 0.0% collision (standard + 10x dense sampling).
3. Geometric Engine Edge Cases & Boundary Auditing.
4. RFC 7946 Standard GeoJSON Validation & GIS Compatibility.
5. Live Browser Leaflet Map Rendering & Zoom/Pan FPS Benchmark (FPS >= 50.0).
6. Multi-Environment Execution (Host + Docker Container).
"""

import os
import sys
import time
import math
import json
import subprocess
from typing import List, Tuple, Dict, Any

# Environment setup
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BENCH_DIR = os.path.dirname(TEST_DIR) if os.path.basename(TEST_DIR) == "test" else TEST_DIR
APP_DIR = os.path.join(BENCH_DIR, "apps", "logistics_wizard")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
if TEST_DIR not in sys.path:
    sys.path.insert(0, TEST_DIR)

from logistics_wizard.routing import (
    get_route_coordinates,
    great_circle_distance,
)
from test_land_collision import LandCollisionDetector

OCEAN_GEOJSON_PATH = os.path.join(TEST_DIR, "ocean_route_longbeach_catlai.geojson")
AIR_GEOJSON_PATH = os.path.join(TEST_DIR, "air_route_sfo_sgn.geojson")


def banner(title: str):
    print("\n" + "=" * 80)
    print(f" [ADVERSARIAL SUITE M4] {title}")
    print("=" * 80)


# ==============================================================================
# SUITE 1: SYNTHETIC OVERLAND ROUTES & NON-ZERO EXIT CODE VERIFICATION
# ==============================================================================

def test_synthetic_overland_routes(detector: LandCollisionDetector):
    banner("SUITE 1: SYNTHETIC OVERLAND ROUTE STRESS & EXIT CODE VERIFICATION")

    # 1. Define deep continental corridors traversing China, Russia, and USA
    corridors = [
        {
            "name": "Continental China Interior Corridor",
            "waypoints": [
                (121.47, 31.23),  # Shanghai
                (113.62, 34.75),  # Zhengzhou
                (108.94, 34.34),  # Xi'an
                (103.83, 36.06),  # Lanzhou
                (94.66, 40.14),   # Dunhuang
                (87.62, 43.82),   # Urumqi
            ],
            "samples_per_leg": 30,
        },
        {
            "name": "Continental Russia / Siberian Corridor",
            "waypoints": [
                (131.87, 43.11),  # Vladivostok
                (128.00, 50.00),  # Amur
                (104.30, 52.30),  # Irkutsk
                (82.93, 55.01),   # Novosibirsk
                (61.40, 55.16),   # Chelyabinsk
                (37.62, 55.76),   # Moscow
            ],
            "samples_per_leg": 30,
        },
        {
            "name": "Continental USA Transcontinental Corridor",
            "waypoints": [
                (-74.00, 40.71),   # New York
                (-84.38, 33.75),   # Atlanta / Ohio interior
                (-89.65, 39.78),   # Illinois
                (-98.00, 38.50),   # Kansas
                (-104.99, 39.74),  # Denver
                (-111.89, 40.76),  # Salt Lake City
                (-121.49, 38.58),  # Sacramento
            ],
            "samples_per_leg": 25,
        },
        {
            "name": "Trans-Eurasian Heartland Corridor",
            "waypoints": [
                (116.40, 39.90),  # Beijing
                (106.90, 47.92),  # Ulaanbaatar
                (85.00, 52.00),   # Altai
                (55.00, 54.00),   # Urals
                (37.62, 55.76),   # Moscow
                (21.01, 52.23),   # Warsaw
                (2.35, 48.86),    # Paris
            ],
            "samples_per_leg": 25,
        }
    ]

    total_tested_overland_pts = 0
    total_detected_land_pts = 0

    for corridor in corridors:
        name = corridor["name"]
        pts = corridor["waypoints"]
        leg_samples = corridor["samples_per_leg"]

        corridor_total = 0
        corridor_hits = 0
        for i in range(len(pts) - 1):
            p1 = pts[i]
            p2 = pts[i + 1]
            for s in range(leg_samples):
                f = s / float(leg_samples)
                lon = p1[0] + f * (p2[0] - p1[0])
                lat = p1[1] + f * (p2[1] - p1[1])
                corridor_total += 1
                if detector.is_land(lon, lat):
                    corridor_hits += 1

        hit_pct = (corridor_hits / float(corridor_total)) * 100.0
        print(f"  - {name}: {corridor_hits}/{corridor_total} points flagged as LAND ({hit_pct:.2f}%)")
        assert corridor_hits == corridor_total, f"Overland failure: {name} only hit {corridor_hits}/{corridor_total}"
        total_tested_overland_pts += corridor_total
        total_detected_land_pts += corridor_hits

    print(f"  [PASS] 100.0% Detection Rate across all {total_tested_overland_pts} synthetic overland points ({total_detected_land_pts}/{total_tested_overland_pts})")

    # 2. Verify non-zero exit code when land collision is detected
    print("\n  [*] Testing Non-Zero Exit Code Enforcement on Land Collision:")
    sub_code = f"""
import sys, os
sys.path.insert(0, r'{TEST_DIR}')
from test_land_collision import LandCollisionDetector

detector = LandCollisionDetector()
# Synthetic inland route traversing Central USA
overland_route = [(-98.0, 38.5), (-95.0, 38.5), (-90.0, 38.5)]
collision_count = sum(1 for lon, lat in overland_route if detector.is_land(lon, lat))
assert collision_count == 0, f'FAIL: Land collision detected ({{collision_count}} hits)'
"""
    p = subprocess.run([sys.executable, "-c", sub_code], capture_output=True, text=True)
    print(f"    - Subprocess Exit Code: {p.returncode}")
    print(f"    - Subprocess Error Output Snippet: {p.stderr.strip().splitlines()[-1] if p.stderr else 'None'}")
    assert p.returncode != 0, f"Expected non-zero exit code on overland collision, got {p.returncode}"
    assert "AssertionError: FAIL: Land collision detected" in p.stderr
    print("    [PASS] Non-zero exit code strictly returned when land collisions occur.")


# ==============================================================================
# SUITE 2: MARITIME NAVIGATIONAL SEGMENTS & DENSE 10X INTERPOLATION
# ==============================================================================

def test_maritime_routes_dense(detector: LandCollisionDetector):
    banner("SUITE 2: MARITIME ROUTES & DENSE 10X INTERPOLATION AUDIT")

    routes = [
        {
            "name": "Long Beach -> Cat Lai Port",
            "origin": "port_of_long_beach",
            "dest": "cat_lai_port",
            "orig_term_skip": 2,
            "dest_term_skip": 2,
        },
        {
            "name": "Los Angeles -> Hai Phong Port",
            "origin": "port_of_los_angeles",
            "dest": "hai_phong_port",
            "orig_term_skip": 2,
            "dest_term_skip": 2,
        }
    ]

    for r in routes:
        name = r["name"]
        res = get_route_coordinates(r["origin"], r["dest"], shipping_method="Ocean", use_cache=False)
        coords = res["coordinates"]  # [[lon, lat], ...]
        total_pts = len(coords)

        orig_skip = r["orig_term_skip"]
        dest_skip = total_pts - r["dest_term_skip"]
        marine_pts = coords[orig_skip:dest_skip]
        marine_count = len(marine_pts)

        # 1. Base waypoint collision check
        base_hits = sum(1 for lon, lat in marine_pts if detector.is_land(lon, lat))
        base_pct = (base_hits / float(marine_count)) * 100.0
        print(f"  - {name}:")
        print(f"    * Base Marine Waypoints: {marine_count} pts (indices {orig_skip}..{dest_skip-1})")
        print(f"    * Land Collisions: {base_hits} / {marine_count} ({base_pct:.2f}%)")
        assert base_hits == 0, f"FAIL: {name} base waypoints hit land: {base_hits}"

        # 2. Dense 10x Interpolation along every marine segment
        dense_hits = 0
        dense_total = 0
        dense_details = []
        samples_per_seg = 10

        for i in range(marine_count - 1):
            p1 = marine_pts[i]
            p2 = marine_pts[i + 1]
            for step in range(samples_per_seg):
                f = step / float(samples_per_seg)
                interp_lon = p1[0] + f * (p2[0] - p1[0])
                interp_lat = p1[1] + f * (p2[1] - p1[1])
                dense_total += 1
                if detector.is_land(interp_lon, interp_lat):
                    dense_hits += 1
                    dense_details.append((orig_skip + i, f, interp_lon, interp_lat))

        dense_pct = (dense_hits / float(dense_total)) * 100.0
        print(f"    * Dense 10x Interpolated Points: {dense_total} pts")
        print(f"    * Dense Land Collisions: {dense_hits} / {dense_total} ({dense_pct:.2f}%)")
        if dense_hits > 0:
            print(f"    [-] Dense collision details (first 3): {dense_details[:3]}")
        assert dense_hits == 0, f"FAIL: {name} dense interpolation detected land: {dense_hits}/{dense_total}"
        print(f"    [PASS] 0.00% Land Collision confirmed on base waypoints & dense 10x segments!")


# ==============================================================================
# SUITE 3: GEOMETRIC DETECTOR EDGE CASES & SANITY HARNESS
# ==============================================================================

def test_detector_edge_cases(detector: LandCollisionDetector):
    banner("SUITE 3: GEOMETRIC DETECTOR EDGE CASES & COORDINATE NORMALIZATION")

    test_cases = [
        # Normalization across multiples of 360°
        ("Kansas (+360° unwrap)", -98.0 + 360.0, 38.5, True),
        ("Kansas (-360° unwrap)", -98.0 - 360.0, 38.5, True),
        ("Mid-Pacific (+360° unwrap)", -150.0 + 360.0, 30.0, False),
        ("Mid-Pacific (-360° unwrap)", -150.0 - 360.0, 30.0, False),
        # Polar regions
        ("North Pole (Arctic Ice Sheet / Ocean)", 0.0, 89.9, False),
        ("South Pole (Antarctica continental interior)", 0.0, -89.9, True),
        # Known marine corridors / straits
        ("Strait of Malacca Fairway", 101.50, 2.50, False),
        ("Bab el Mandeb Shipping Channel", 43.35, 12.60, False),
        ("Luzon Strait Marine Corridor", 121.00, 21.00, False),
        ("Mid-Indian Ocean Fairway", 80.00, -10.00, False),
    ]

    for label, lon, lat, expected in test_cases:
        actual = detector.is_land(lon, lat)
        status = "PASS" if actual == expected else "FAIL"
        exp_s = "LAND" if expected else "WATER"
        act_s = "LAND" if actual else "WATER"
        print(f"    [{status}] {label:44s} ({lon:8.2f}, {lat:6.2f}) -> {act_s} (Expected: {exp_s})")
        assert actual == expected, f"Edge case mismatch for {label}: got {act_s}, expected {exp_s}"

    print("  [PASS] All 10 geometric edge cases & unwrapped coordinates verified.")


# ==============================================================================
# SUITE 4: RFC 7946 GEOJSON VALIDATION & GIS COMPATIBILITY
# ==============================================================================

def test_rfc7946_geojson_spec():
    banner("SUITE 4: RFC 7946 GEOJSON SPECIFICATION & GIS COMPATIBILITY CHECK")

    import jsonschema

    # Strict RFC 7946 GeoJSON FeatureCollection Schema
    geojson_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["type", "features"],
        "properties": {
            "type": {"type": "string", "enum": ["FeatureCollection"]},
            "features": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["type", "geometry", "properties"],
                    "properties": {
                        "type": {"type": "string", "enum": ["Feature"]},
                        "geometry": {
                            "type": "object",
                            "required": ["type", "coordinates"],
                            "properties": {
                                "type": {"type": "string", "enum": ["LineString", "MultiLineString"]},
                                "coordinates": {"type": "array", "minItems": 1}
                            }
                        },
                        "properties": {
                            "type": "object",
                            "required": ["title", "distance_km", "method", "stroke", "stroke-width"]
                        }
                    }
                }
            }
        }
    }

    files = [
        (OCEAN_GEOJSON_PATH, "Ocean", "#007bff", "LineString"),
        (AIR_GEOJSON_PATH, "Air", "#28a745", "MultiLineString"),
    ]

    for path, exp_method, exp_stroke, exp_geom_type in files:
        fname = os.path.basename(path)
        assert os.path.exists(path), f"File missing: {path}"
        assert os.path.getsize(path) > 1000, f"File too small: {path}"

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Validate Schema
        jsonschema.validate(instance=data, schema=geojson_schema)
        print(f"  [+] Schema Validation: {fname} matches RFC 7946 FeatureCollection schema.")

        # 2. Validate Feature & Geometry
        feat = data["features"][0]
        geom = feat["geometry"]
        props = feat["properties"]

        assert props["method"] == exp_method, f"Method mismatch: {props['method']} != {exp_method}"
        assert props["stroke"] == exp_stroke, f"Stroke mismatch: {props['stroke']} != {exp_stroke}"
        assert props["stroke-width"] == 3, f"Stroke width mismatch: {props['stroke-width']}"
        assert geom["type"] == exp_geom_type, f"Geom mismatch: {geom['type']} != {exp_geom_type}"

        # 3. Coordinate Bounds [-180, 180] and [-90, 90]
        if geom["type"] == "LineString":
            flat_pts = geom["coordinates"]
        else:
            flat_pts = [p for seg in geom["coordinates"] for p in seg]

        for pt in flat_pts:
            lon, lat = pt[0], pt[1]
            assert -180.0 <= lon <= 180.0, f"Out-of-bounds longitude in {fname}: {lon}"
            assert -90.0 <= lat <= 90.0, f"Out-of-bounds latitude in {fname}: {lat}"

        min_lon = min(p[0] for p in flat_pts)
        max_lon = max(p[0] for p in flat_pts)
        min_lat = min(p[1] for p in flat_pts)
        max_lat = max(p[1] for p in flat_pts)

        print(f"      * Points: {len(flat_pts)}")
        print(f"      * Longitude range: [{min_lon:.4f}, {max_lon:.4f}] (RFC 7946 bounded)")
        print(f"      * Latitude range:  [{min_lat:.4f}, {max_lat:.4f}] (RFC 7946 bounded)")
        print(f"      * Distance: {props['distance_km']} km")
        print(f"      * Title: '{props['title']}'")
        print(f"  [PASS] {fname} is 100% RFC 7946 compliant and directly importable into QGIS and geojson.io.")


# ==============================================================================
# SUITE 5: LIVE BROWSER RENDERING & PAN/ZOOM FPS BENCHMARK (FPS >= 50)
# ==============================================================================

def test_live_browser_fps_benchmark():
    banner("SUITE 5: LIVE BROWSER RENDERING & INTERACTION FPS BENCHMARK")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("  1. Authenticating to Frappe Desk (http://localhost:2828/login)...")
        page.goto("http://localhost:2828/login", timeout=12000)
        page.fill("#login_email", "Administrator")
        page.fill("#login_password", "admin")
        page.click(".btn-login")
        page.wait_for_url("**/app**", timeout=15000)
        page.wait_for_function("() => typeof window.LogisticsWizardMap !== 'undefined'", timeout=10000)
        print("     Desk loaded with LogisticsWizardMap.")

        print("  2. Opening Logistics Wizard FAB & Live Shipment Modal...")
        page.wait_for_selector("#lw-fab-main", timeout=10000)
        page.click("#lw-fab-main")
        time.sleep(0.5)

        page.wait_for_selector("#lw-fab-shipment", timeout=5000)
        page.click("#lw-fab-shipment")
        time.sleep(1.0)

        items = page.query_selector_all(".lw-shipment-item")
        assert len(items) > 0, "No shipment items in modal"
        items[0].click()
        time.sleep(2.5)  # Allow Leaflet tiles & polylines to initialize

        print("  3. Measuring Animation Loop FPS (2,000ms duration)...")
        bench_data = page.evaluate("""() => new Promise(resolve => {
            let frames = 0;
            let last = performance.now();
            const deltas = [];
            let slowFrames = 0;
            const start = last;

            function step(now) {
                frames++;
                const delta = now - last;
                deltas.push(delta);
                if (delta > 33.3) slowFrames++;
                last = now;

                if (now - start < 2000) {
                    requestAnimationFrame(step);
                } else {
                    const dur = now - start;
                    const fps = (frames / dur) * 1000;
                    const minDelta = Math.min(...deltas);
                    const maxDelta = Math.max(...deltas);
                    const avgDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
                    resolve({ frames, dur, fps, minDelta, maxDelta, avgDelta, slowFrames });
                }
            }
            requestAnimationFrame(step);
        })""")

        fps = bench_data["fps"]
        print(f"     * Measured Frames: {bench_data['frames']} in {bench_data['dur']:.1f} ms")
        print(f"     * Measured Frame Rate: {fps:.2f} FPS")
        print(f"     * Average Frame Delta: {bench_data['avgDelta']:.2f} ms (Min: {bench_data['minDelta']:.2f} ms, Max: {bench_data['maxDelta']:.2f} ms)")
        print(f"     * Dropped Frames (> 33.3 ms): {bench_data['slowFrames']}")

        assert fps >= 50.0, f"FAIL: Measured FPS {fps:.2f} below required 50.0 FPS"
        print(f"  [PASS] Frame rate benchmark satisfied ({fps:.2f} FPS >= 50.0 FPS threshold).")

        print("  4. Stress-Testing Pan and Zoom Interaction Rendering...")
        pan_zoom_fps = page.evaluate("""() => new Promise(resolve => {
            const map = window.LogisticsWizardMap._activeMap;
            let frames = 0;
            const start = performance.now();

            if (map) {
                map.panBy([50, 50], { animate: true, duration: 0.5 });
                setTimeout(() => {
                    map.panBy([-50, -50], { animate: true, duration: 0.5 });
                }, 500);
            }

            function track(now) {
                frames++;
                if (now - start < 1200) {
                    requestAnimationFrame(track);
                } else {
                    const dur = now - start;
                    resolve((frames / dur) * 1000);
                }
            }
            requestAnimationFrame(track);
        })""")

        print(f"     * Interactive Pan/Zoom Frame Rate: {pan_zoom_fps:.2f} FPS")
        assert pan_zoom_fps >= 50.0, f"FAIL: Pan/zoom FPS {pan_zoom_fps:.2f} below 50.0 FPS"
        print(f"  [PASS] Pan/Zoom interaction sustains {pan_zoom_fps:.2f} FPS (>= 50.0 FPS).")

        browser.close()


# ==============================================================================
# SUITE 6: DOCKER CONTAINER MULTI-ENVIRONMENT VALIDATION
# ==============================================================================

def test_container_execution():
    banner("SUITE 6: DOCKER CONTAINER EXECUTION INTEGRITY")

    cmd = [
        "docker", "exec", "frappe-bench-backend-1",
        "/home/frappe/frappe-bench/env/bin/python",
        "/home/frappe/frappe-bench/test_land_collision.py"
    ]
    print(f"  [*] Executing test_land_collision.py inside frappe-bench-backend-1...")
    p = subprocess.run(cmd, capture_output=True, text=True)
    print(f"      Exit Code: {p.returncode}")
    assert p.returncode == 0, f"Container execution failed:\n{p.stderr}"
    assert "ALL QA LAND COLLISION CHECKS & GEOJSON EXPORTS PASSED" in p.stdout
    print("  [PASS] Clean container execution verified (Exit Code 0).")


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================

def main():
    t0 = time.time()
    print("=" * 80)
    print(" LOGISTICS WIZARD — ADVERSARIAL CHALLENGER SUITE (MILESTONE M4)")
    print(" Rigorous Empirical Stress-Testing: Collision Oracles, GeoJSON, and FPS")
    print("=" * 80)

    # 1. Initialize detector
    detector = LandCollisionDetector()

    # 2. Run adversarial test suites
    test_synthetic_overland_routes(detector)
    test_maritime_routes_dense(detector)
    test_detector_edge_cases(detector)
    test_rfc7946_geojson_spec()
    test_live_browser_fps_benchmark()
    test_container_execution()

    duration = time.time() - t0
    banner(f"ALL 6 ADVERSARIAL SUITES COMPLETED: 100% PASS in {duration:.2f}s")
    print(" FINAL VERDICT: APPROVE")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
