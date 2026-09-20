#!/usr/bin/env python3
"""
adversarial_test_m5.py — Empirical Challenger Adversarial Verification Suite
=============================================================================
Milestone M5: Adversarial Challenge, Mutation Testing & Mathematical Integrity
Logistics Wizard for ERPNext v15.

Tests:
1. Negative mutation testing across all 9 Acceptance Criteria (AC-1 to AC-9).
2. Verification of mathematical backing (Haversine, SLERP, Jordan Curve PIP, Douglas-Peucker, Bearing, rAF).
3. Discovery of potential false positives, silent failure swallows, or trivial passes.
"""

import os
import sys
import time
import json
import math
import urllib
import urllib.request
import urllib.error
from typing import Dict, Any, List, Tuple, Optional
import copy
import unittest
from unittest.mock import patch, MagicMock

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BENCH_DIR = os.path.dirname(TEST_DIR) if os.path.basename(TEST_DIR) == "test" else TEST_DIR
APP_DIR = os.path.join(BENCH_DIR, "apps", "logistics_wizard")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
if BENCH_DIR not in sys.path:
    sys.path.insert(0, BENCH_DIR)
if TEST_DIR not in sys.path:
    sys.path.insert(0, TEST_DIR)

from verify_coords import haversine_distance_km, verify_locations, DEFAULT_TOLERANCE_KM
from logistics_wizard.routing import (
    get_route_coordinates,
    get_location_coords,
    calculate_ocean_route,
    calculate_air_route,
    great_circle_distance,
    to_cartesian,
    from_cartesian,
    slerp_point,
    solve_antimeridian_crossing,
    interpolate_great_circle,
)
from test_land_collision import (
    LandCollisionDetector,
    test_detector_geodetic_oracles,
    test_ocean_routes_land_collision,
    export_standard_geojson_routes,
)
import test_e2e_acceptance as master_suite

REAL_GET_ROUTE = master_suite.get_route_coordinates
REAL_URLOPEN = urllib.request.urlopen

class AdversarialChallengeM5(unittest.TestCase):

    def setUp(self):
        self.tracker = master_suite.AcceptanceTracker()

    # ==========================================================================
    # AC-1: Locations Completeness & References
    # ==========================================================================
    def test_ac1_negative_mutation_missing_station(self):
        """Mutate locations.json by removing a critical station: must raise AssertionError."""
        with open(master_suite.LOCATIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        corrupted = copy.deepcopy(data)
        del corrupted["locations"]["cat_lai_port"]

        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(corrupted))):
            with self.assertRaises(AssertionError) as ctx:
                master_suite.verify_layer1_coordinates(self.tracker)
            self.assertIn("Missing coordinates in cat_lai_port", str(ctx.exception))

    def test_ac1_negative_mutation_missing_reference_fields(self):
        """Mutate reference in locations.json: must raise AssertionError."""
        with open(master_suite.LOCATIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        corrupted = copy.deepcopy(data)
        del corrupted["locations"]["san_francisco_airport"]["reference"]["benchmark_coordinates"]

        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(corrupted))):
            with self.assertRaises(AssertionError) as ctx:
                master_suite.verify_layer1_coordinates(self.tracker)
            self.assertIn("Missing benchmark_coordinates", str(ctx.exception))

    # ==========================================================================
    # AC-2: Geodesic Coordinate Discrepancy < 2.0 km
    # ==========================================================================
    def test_ac2_negative_mutation_exceeds_tolerance(self):
        """Shift Cat Lai coordinates by ~5km: AC-2 assertion must fail."""
        with open(master_suite.LOCATIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        corrupted = copy.deepcopy(data)
        # Shift latitude from 10.7626 to 10.8200 (~6.4 km shift)
        corrupted["locations"]["cat_lai_port"]["coordinates"]["latitude"] = 10.8200

        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(corrupted))):
            with self.assertRaises(AssertionError) as ctx:
                master_suite.verify_layer1_coordinates(self.tracker)
            self.assertIn("Discrepancy exceeds 2.0 km", str(ctx.exception))

    def test_ac2_haversine_mathematical_oracle(self):
        """Empirically test Haversine calculation against spherical geometry proofs."""
        # 1. Equator 1 degree longitude distance
        # Circumference = 2 * pi * 6371.0088 = 40030.173 km
        # 1 deg = 40030.173 / 360 = 111.1949 km
        d1 = haversine_distance_km(0.0, 0.0, 0.0, 1.0)
        self.assertAlmostEqual(d1, 111.1949, delta=0.01)

        # 2. Meridian 1 degree latitude distance
        d2 = haversine_distance_km(0.0, 0.0, 1.0, 0.0)
        self.assertAlmostEqual(d2, 111.1949, delta=0.01)

        # 3. Antipodal distance (half sphere = pi * R = 20015.086 km)
        d_antipodal = haversine_distance_km(0.0, 0.0, 0.0, 180.0)
        self.assertAlmostEqual(d_antipodal, math.pi * 6371.0088, delta=0.01)

        # 4. Same point distance must be exactly 0.0
        d_zero = haversine_distance_km(10.7626, 106.7898, 10.7626, 106.7898)
        self.assertEqual(d_zero, 0.0)

    # ==========================================================================
    # AC-3: Maritime Ocean Route & Land Collision
    # ==========================================================================
    def test_ac3_negative_mutation_land_collision_detected(self):
        """Mutate ocean route to cross through central Japan land: detector must flag collision."""
        detector = LandCollisionDetector()

        # Generate genuine route
        ocean_res = get_route_coordinates("port_of_long_beach", "cat_lai_port", shipping_method="Ocean", use_cache=False)
        coords = ocean_res["coordinates"]

        # Deliberately inject inland Tokyo waypoint into marine navigational segment
        corrupted_coords = copy.deepcopy(coords)
        tokyo_inland = [139.6917, 35.6895]  # Tokyo city center
        corrupted_coords[10] = tokyo_inland

        marine_pts = corrupted_coords[2:-2]
        hits = sum(1 for lon, lat in marine_pts if detector.is_land(((lon + 180.0) % 360.0) - 180.0, lat))
        self.assertGreater(hits, 0, "Detector failed to catch corrupted inland waypoint in ocean route!")

    def test_ac3_negative_mutation_bypassing_luzon(self):
        """Mutate ocean route to not pass Luzon: AC-3 assertion must fail."""
        def fake_get_route(*args, **kwargs):
            return {
                "coordinates": [[0, 0]] * 60,
                "coordinates_latlon": [[40.0, -170.0]] * 60,  # Never enters 15-23N, 115-125E
                "distance_km": 13000.0,
            }

        with patch("test_e2e_acceptance.get_route_coordinates", side_effect=fake_get_route):
            with self.assertRaises(AssertionError) as ctx:
                master_suite.verify_layer2_routing_and_cache(self.tracker)
            self.assertIn("Route failed to pass through Luzon Strait", str(ctx.exception))

    # ==========================================================================
    # AC-4: Aviation Air Route 3D Great-Circle & Distance
    # ==========================================================================
    def test_ac4_negative_mutation_distance_out_of_range(self):
        """Mutate air distance outside 12500-13500 km: AC-4 must fail."""
        def fake_air_route(*args, **kwargs):
            if kwargs.get("shipping_method") == "Air":
                return {
                    "distance_km": 9500.0,  # Too short
                    "coordinates_latlon": [[0, 0]] * 25,
                    "split_segments": [[], []],
                }
            return REAL_GET_ROUTE(*args, **kwargs)

        with patch("test_e2e_acceptance.get_route_coordinates", side_effect=fake_air_route):
            with self.assertRaises(AssertionError) as ctx:
                master_suite.verify_layer2_routing_and_cache(self.tracker)
            self.assertIn("Air distance 9500.0 km outside expected", str(ctx.exception))

    def test_ac4_negative_mutation_antimeridian_jump(self):
        """Simulate wrapped longitude jump > 30 degrees: AC-4 must fail."""
        def fake_air_route(*args, **kwargs):
            if kwargs.get("shipping_method") == "Air":
                return {
                    "distance_km": 13150.0,
                    "coordinates_latlon": [(37.0, 175.0), (37.0, -175.0)],  # 350 deg jump!
                    "split_segments": [[], []],
                }
            return REAL_GET_ROUTE(*args, **kwargs)

        with patch("test_e2e_acceptance.get_route_coordinates", side_effect=fake_air_route):
            with self.assertRaises(AssertionError) as ctx:
                master_suite.verify_layer2_routing_and_cache(self.tracker)
            self.assertIn("Antimeridian wrap jump detected", str(ctx.exception))

    # ==========================================================================
    # AC-5: Cache & API Response Time SLA
    # ==========================================================================
    def test_ac5_negative_mutation_cache_timeout(self):
        """Simulate cache latency exceeding 50ms: AC-5 must fail."""
        def slow_cached_route(*args, **kwargs):
            res = REAL_GET_ROUTE(*args, **kwargs)
            if kwargs.get("use_cache"):
                time.sleep(0.06)  # 60ms delay
            return res

        with patch("test_e2e_acceptance.get_route_coordinates", side_effect=slow_cached_route):
            with self.assertRaises(AssertionError) as ctx:
                master_suite.verify_layer2_routing_and_cache(self.tracker)
            self.assertIn("Cache retrieval exceeded 50ms", str(ctx.exception))

    def test_ac5_api_tested_fallback_behavior(self):
        """
        CRITICAL AUDIT: What happens if both HTTP API and in-process Frappe fail?
        Does AC-5 fail or does it pass with only cache latency?
        """
        def failing_urlopen(*args, **kwargs):
            raise urllib.error.URLError("Connection refused")

        with patch("urllib.request.urlopen", side_effect=failing_urlopen):
            with patch.dict("sys.modules", {"frappe": None}):
                tracker = master_suite.AcceptanceTracker()
                try:
                    master_suite.verify_layer2_routing_and_cache(tracker)
                except Exception as e:
                    print(f"\n[AUDIT AC-5] When API is down: raised {e}")

                passed = tracker.criteria["AC-5"]["passed"]
                telemetry = tracker.criteria["AC-5"]["telemetry"]
                print(f"\n[AUDIT AC-5] When API is down: passed={passed}, telemetry='{telemetry}'")
                if passed:
                    print(">>> DEFECT CONFIRMED: AC-5 produces FALSE POSITIVE when API is completely down!")
                    print(">>> Root Cause: Lines 380-406 omit asserting 'api_tested is True', unconditionally recording pass based solely on cache latency.")
                self.assertFalse(passed, "VULNERABILITY: test_e2e_acceptance passed AC-5 even though API was completely down/untested!")



    # ==========================================================================
    # AC-6: OpenStreetMap Basemap HTTP check
    # ==========================================================================
    def test_ac6_negative_mutation_tile_http_failure(self):
        """Simulate HTTP 404 or 500 when fetching OpenStreetMap tile: AC-6 must fail."""
        class MockHTTPResponse:
            def __init__(self, status):
                self.status = status
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        def mock_urlopen(req, *args, **kwargs):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if "tile.openstreetmap.org" in url:
                return MockHTTPResponse(404)
            return REAL_URLOPEN(req, *args, **kwargs)

        with patch("urllib.request.urlopen", side_effect=mock_urlopen):
            with self.assertRaises(AssertionError) as ctx:
                master_suite.verify_layer3_leaflet_and_animation(self.tracker)
            self.assertIn("OpenStreetMap tile returned 404", str(ctx.exception))

    # ==========================================================================
    # AC-7: OpenSeaMap Marine Overlay HTTP check
    # ==========================================================================
    def test_ac7_negative_mutation_tile_http_failure(self):
        """Simulate HTTP 500 on OpenSeaMap: AC-7 must fail."""
        class MockHTTPResponse:
            def __init__(self, status):
                self.status = status
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        def mock_urlopen(req, *args, **kwargs):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if "tiles.openseamap.org" in url:
                return MockHTTPResponse(500)
            return REAL_URLOPEN(req, *args, **kwargs)

        with patch("urllib.request.urlopen", side_effect=mock_urlopen):
            with self.assertRaises(AssertionError) as ctx:
                master_suite.verify_layer3_leaflet_and_animation(self.tracker)
            self.assertIn("OpenSeaMap tile returned 500", str(ctx.exception))


    # ==========================================================================
    # AC-8: JS Animation Math in Node.js
    # ==========================================================================
    def test_ac8_negative_mutation_bundle_algorithm(self):
        """If bundle JS is missing or calculateBearing is corrupted, AC-8 must fail."""
        with patch("subprocess.run") as mock_node:
            # Simulate corrupted Node output where bearing North is 45 deg instead of 0
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = json.dumps({
                "dpCollinearLen": 2,
                "dpSharpLen": 3,
                "bearings": { "bN": 45, "bE": 90, "bS": 180, "bW": 270 },
                "interpolation": { "p0": [0, 0], "p50": [0, 5], "p100": [0, 10] }
            })
            mock_node.return_value = mock_res

            with self.assertRaises(AssertionError) as ctx:
                master_suite.verify_layer3_leaflet_and_animation(self.tracker)
            self.assertIn("Bearing North failed", str(ctx.exception))

    # ==========================================================================
    # AC-9: FPS SLA >= 50.0 FPS & Vulnerability Audit
    # ==========================================================================
    def test_ac9_fps_exception_swallowing_audit(self):
        """
        CRITICAL AUDIT: If live browser FPS drops to 30 FPS (< 50 FPS),
        does verify_layer4_collision_and_fps fail the suite, or does it pass
        because line 592 is inside a try...except that swallows AssertionError?
        """
        # Mock Playwright to return 30.0 FPS
        mock_page = MagicMock()
        mock_page.evaluate.return_value = {"frames": 45, "dur": 1500.0, "fps": 30.0}
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context

        mock_p = MagicMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_p_ctx = MagicMock()
        mock_p_ctx.__enter__.return_value = mock_p
        mock_p_ctx.__exit__.return_value = None

        tracker = master_suite.AcceptanceTracker()

        with patch("test_e2e_acceptance.PLAYWRIGHT_AVAILABLE", True):
            with patch("test_e2e_acceptance.sync_playwright", return_value=mock_p_ctx):
                # Run verify_layer4_collision_and_fps
                master_suite.verify_layer4_collision_and_fps(tracker)

                passed = tracker.criteria["AC-9"]["passed"]
                telemetry = tracker.criteria["AC-9"]["telemetry"]
                print(f"\n[AUDIT AC-9] When live Chrome rAF is 30.0 FPS: passed={passed}, telemetry='{telemetry}'")
                
                # An adversarial test strictly asserts that the criterion MUST NOT pass when FPS < 50
                # Because test_e2e_acceptance currently swallows this, passed is True (BUG/FALSE POSITIVE)
                if passed:
                    print(">>> DEFECT CONFIRMED: AC-9 produces FALSE POSITIVE when live browser FPS < 50.0!")
                    print(">>> Root Cause: Line 592 'assert live_fps >= 50.0' is caught by line 599 'except Exception:', and line 617 evaluates 'live_fps >= 50.0 or calc_fps >= 50.0' where calc_fps >> 50.0.")
                
                self.assertFalse(passed, "VULNERABILITY: test_e2e_acceptance passed AC-9 even though live browser FPS was 30.0 FPS (< 50.0 SLA)!")




if __name__ == "__main__":
    unittest.main(verbosity=2)
