#!/usr/bin/env python3
"""
test_verify_coords_adversarial.py — Empirical Stress & Adversarial Test Suite
=============================================================================
Conducts thorough, adversarial empirical verification of `verify_coords.py`:
1. Mathematical Edge Cases:
   - Identical points (0 km geodesic distance)
   - Antipodal points (~20,015.11 km, domain guard against floating-point errors)
   - Antimeridian crossing (-180° / +180° boundary behavior)
   - Micro-discrepancy resolution (1-meter separation)
2. Mutation / Negative Testing:
   - 5 km node shifts (e.g. apple_park_cupertino, luzon_strait)
   - Coordinate boundary violations (lat > 90, lon > 180)
   - Missing fields and malformed structures
   - Strict tolerance limits (--tolerance 0.001 -> 1 meter)
   - CLI execution return codes (strict verification of exit code 1 on failures)
3. Independent Geodetic Oracle Comparison
"""

import os
import sys
import json
import math
import tempfile
import subprocess
from typing import Dict, Any, Tuple

# Import implementation from verify_coords
import verify_coords

EARTH_RADIUS_KM = 6371.0088


def oracle_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Independent ground-truth implementation of Haversine formula."""
    r_lat1, r_lon1 = math.radians(lat1), math.radians(lon1)
    r_lat2, r_lon2 = math.radians(lat2), math.radians(lon2)
    dlat = r_lat2 - r_lat1
    dlon = r_lon2 - r_lon1
    a = (math.sin(dlat / 2.0) ** 2) + math.cos(r_lat1) * math.cos(r_lat2) * (math.sin(dlon / 2.0) ** 2)
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


class AdversarialTestRunner:
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.results = []
        self.locations_path = verify_coords.resolve_default_locations_file()

    def record_result(self, name: str, passed: bool, details: str):
        if passed:
            self.passed_tests += 1
            status = "PASS"
        else:
            self.failed_tests += 1
            status = "FAIL"
        self.results.append({"name": name, "status": status, "details": details})
        print(f"[{status}] {name}: {details}")

    def run_cli(self, args: list) -> Tuple[int, str, str]:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_coords.py")
        cmd = [sys.executable, script_path] + args
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return proc.returncode, proc.stdout, proc.stderr

    # -------------------------------------------------------------
    # Suite 1: Mathematical Edge Cases
    # -------------------------------------------------------------
    def test_mathematical_edge_cases(self):
        print("\n=== SUITE 1: MATHEMATICAL EDGE CASES ===")

        # 1.1 Identical points
        cases_zero = [
            ("Equator zero", 0.0, 0.0, 0.0, 0.0),
            ("North Pole", 90.0, 0.0, 90.0, 0.0),
            ("South Pole", -90.0, 0.0, -90.0, 0.0),
            ("Apple Park", 37.3346, -122.0090, 37.3346, -122.0090),
            ("Date Line", 45.0, 180.0, 45.0, 180.0),
        ]
        for name, lat1, lon1, lat2, lon2 in cases_zero:
            d = verify_coords.haversine_distance_km(lat1, lon1, lat2, lon2)
            passed = (d == 0.0)
            self.record_result(f"Identical Points - {name}", passed, f"Distance = {d} km")

        # 1.2 Antipodal points
        cases_antipodal = [
            ("Poles", 90.0, 0.0, -90.0, 0.0),
            ("Equatorial 0 vs 180", 0.0, 0.0, 0.0, 180.0),
            ("Equatorial 90 vs -90", 0.0, 90.0, 0.0, -90.0),
            ("Mid-latitude 45°", 45.0, 45.0, -45.0, -135.0),
        ]
        expected_antipodal = math.pi * EARTH_RADIUS_KM  # ~20015.114442 km
        for name, lat1, lon1, lat2, lon2 in cases_antipodal:
            d = verify_coords.haversine_distance_km(lat1, lon1, lat2, lon2)
            passed = abs(d - expected_antipodal) < 1e-6
            self.record_result(f"Antipodal Points - {name}", passed, f"Distance = {d:.6f} km (expected {expected_antipodal:.6f})")

        # 1.3 Floating-point clamping guard against math domain error in sqrt(1 - a)
        # Construct scenario where numerical imprecision could produce a = 1.0000000000000002
        try:
            d_clamped = verify_coords.haversine_distance_km(90.0, 0.0, -90.0, 0.0000000000000001)
            passed = not math.isnan(d_clamped) and abs(d_clamped - expected_antipodal) < 1e-3
            self.record_result("Antipodal Clamping Guard", passed, f"No math domain error, d = {d_clamped:.6f} km")
        except Exception as e:
            self.record_result("Antipodal Clamping Guard", False, f"Threw exception: {e}")

        # 1.4 Antimeridian crossing
        # Equatorial: 179.999° to -179.999° -> separation is 0.002°
        expected_meridian = (0.002 / 360.0) * (2.0 * math.pi * EARTH_RADIUS_KM)
        d_meridian = verify_coords.haversine_distance_km(0.0, 179.999, 0.0, -179.999)
        passed = abs(d_meridian - expected_meridian) < 1e-6
        self.record_result("Antimeridian Equator Crossing", passed, f"Distance = {d_meridian:.6f} km (expected {expected_meridian:.6f} km)")

        # High latitude: 52°N, 179.9° to -179.9° (0.2° separation across dateline)
        oracle_52 = oracle_haversine(52.0, 179.9, 52.0, -179.9)
        d_52 = verify_coords.haversine_distance_km(52.0, 179.9, 52.0, -179.9)
        passed = abs(d_52 - oracle_52) < 1e-9
        self.record_result("Antimeridian 52°N Crossing", passed, f"Distance = {d_52:.6f} km (oracle {oracle_52:.6f} km)")

        # Same point on antimeridian with opposite sign (+180° vs -180°)
        d_dateline_same = verify_coords.haversine_distance_km(48.0, 180.0, 48.0, -180.0)
        passed = abs(d_dateline_same) < 1e-9
        self.record_result("Antimeridian +180° vs -180°", passed, f"Distance = {d_dateline_same:.6f} km")

        # 1.5 Sub-meter geodesic precision
        # 1 meter delta in latitude is ~ 1.0 / (EARTH_RADIUS_KM * 1000 * pi / 180) degrees
        deg_1m = (1.0 / (EARTH_RADIUS_KM * 1000.0)) * (180.0 / math.pi)
        d_1m = verify_coords.haversine_distance_km(10.0, 106.0, 10.0 + deg_1m, 106.0) * 1000.0
        passed = abs(d_1m - 1.0) < 1e-4
        self.record_result("Geodesic Sub-meter Precision", passed, f"Distance = {d_1m:.4f} m (expected 1.0000 m)")

    # -------------------------------------------------------------
    # Suite 2: Negative & Mutation Testing (verify_coords.py CLI)
    # -------------------------------------------------------------
    def test_negative_and_mutations(self):
        print("\n=== SUITE 2: NEGATIVE & MUTATION TESTING ===")

        # Load baseline data
        with open(self.locations_path, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)

        # 2.1 Baseline run must pass with code 0
        code, stdout, stderr = self.run_cli([])
        passed = (code == 0 and "Verdict: ALL LOCATIONS FULLY COMPLIANT" in stdout)
        self.record_result("Baseline locations.json verification", passed, f"Exit code {code}")

        # 2.2 Strict tolerance (--tolerance 0.001 km = 1 meter) must FAIL with code 1
        code, stdout, stderr = self.run_cli(["--tolerance", "0.001"])
        passed = (code == 1 and "[FAIL]" in stdout and "VERIFICATION FAILED" in stderr)
        self.record_result("Strict Tolerance 1 meter (--tolerance 0.001)", passed, f"Exit code {code}, detected failures")

        # 2.3 Tolerance boundary test: noi_bai_airport has discrepancy ~20.8 m (0.0208 km)
        # Tolerance 0.01 km (10 m) must FAIL with code 1
        code, stdout, stderr = self.run_cli(["--tolerance", "0.01"])
        passed = (code == 1 and "noi_bai_airport" in stdout and "[FAIL]" in stdout)
        self.record_result("Tolerance 10m boundary (--tolerance 0.01)", passed, f"Exit code {code}, Noi Bai failed as expected")

        # Tolerance 0.03 km (30 m) must PASS with code 0
        code, stdout, stderr = self.run_cli(["--tolerance", "0.03"])
        passed = (code == 0 and "ALL LOCATIONS FULLY COMPLIANT" in stdout)
        self.record_result("Tolerance 30m boundary (--tolerance 0.03)", passed, f"Exit code {code}, all passed")

        # Helper to run with mutated temporary JSON
        def test_mutation(test_name: str, modifier_fn, expected_code: int, expected_substring: str):
            mutated = json.loads(json.dumps(baseline_data))
            modifier_fn(mutated)
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
                json.dump(mutated, tf, indent=2)
                temp_path = tf.name

            try:
                c, out, err = self.run_cli(["--file", temp_path])
                matched = (expected_substring in out) or (expected_substring in err)
                p = (c == expected_code and matched)
                self.record_result(test_name, p, f"Exit code {c} (expected {expected_code}), substring '{expected_substring}' found: {matched}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        # 2.4 Mutate Apple Park by 5 km (~0.045 deg latitude shift)
        def mutate_apple_park_5km(data):
            # Apple park lat = 37.3346 -> + 0.045 deg ~ 5.003 km shift
            data["locations"]["apple_park_cupertino"]["coordinates"]["latitude"] += 0.045

        test_mutation("Mutated Node 5km Shift (apple_park_cupertino)", mutate_apple_park_5km, 1, "[FAIL]")

        # 2.5 Mutate Maritime Waypoint by 5 km (luzon_strait)
        def mutate_luzon_5km(data):
            # Luzon strait lon = 121.0 -> + 0.05 deg ~ 5.19 km shift at 21°N
            data["locations"]["luzon_strait"]["coordinates"]["longitude"] += 0.05

        test_mutation("Mutated Waypoint 5km Shift (luzon_strait)", mutate_luzon_5km, 1, "[FAIL]")

        # 2.6 Mutate Hai Phong Port by 10 km
        def mutate_haiphong_10km(data):
            data["locations"]["hai_phong_port"]["coordinates"]["latitude"] += 0.09

        test_mutation("Mutated Seaport 10km Shift (hai_phong_port)", mutate_haiphong_10km, 1, "[FAIL]")

        # 2.7 Out-of-bounds Latitude (> 90°)
        def mutate_oob_lat(data):
            data["locations"]["cat_lai_port"]["coordinates"]["latitude"] = 92.5

        test_mutation("Out-of-bounds Latitude (92.5°)", mutate_oob_lat, 1, "COORDINATES OUT OF WGS84 RANGE")

        # 2.8 Out-of-bounds Longitude (> 180°)
        def mutate_oob_lon(data):
            data["locations"]["cat_lai_port"]["coordinates"]["longitude"] = -185.0

        test_mutation("Out-of-bounds Longitude (-185.0°)", mutate_oob_lon, 1, "COORDINATES OUT OF WGS84 RANGE")

        # 2.9 Missing benchmark coordinates
        def mutate_missing_benchmark(data):
            data["locations"]["san_francisco_airport"]["reference"]["benchmark_coordinates"] = []

        test_mutation("Missing Benchmark Coordinates", mutate_missing_benchmark, 1, "MISSING COORDS OR BENCHMARK")

        # 2.10 Null coordinates
        def mutate_null_coords(data):
            data["locations"]["tan_son_nhat_airport"]["coordinates"]["latitude"] = None

        test_mutation("Null Coordinates", mutate_null_coords, 1, "MISSING COORDS OR BENCHMARK")

        # 2.11 Empty locations dict
        def mutate_empty_locations(data):
            data["locations"] = {}

        test_mutation("Empty Locations Object", mutate_empty_locations, 1, "No locations found in JSON")

        # 2.12 Non-existent file
        code, stdout, stderr = self.run_cli(["--file", "non_existent_fake_path_12345.json"])
        passed = (code == 1 and "File not found" in stderr)
        self.record_result("Non-existent File Handling", passed, f"Exit code {code}, stderr reported 'File not found'")

        # 2.13 Malformed JSON syntax
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            tf.write('{"locations": {"unclosed": ')
            malformed_path = tf.name
        try:
            code, stdout, stderr = self.run_cli(["--file", malformed_path])
            passed = (code == 1 and "Error parsing JSON file" in stderr)
            self.record_result("Malformed JSON Handling", passed, f"Exit code {code}, stderr reported 'Error parsing JSON file'")
        finally:
            if os.path.exists(malformed_path):
                os.remove(malformed_path)

    # -------------------------------------------------------------
    # Suite 3: Authoritative Geodetic Benchmark Audit
    # -------------------------------------------------------------
    def test_authoritative_benchmarks(self):
        print("\n=== SUITE 3: AUTHORITATIVE BENCHMARK AUDIT ===")
        with open(self.locations_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        locations = data["locations"]

        # Audit each node against oracle
        for loc_id, loc in locations.items():
            cand = loc["coordinates"]
            bench = loc["reference"]["benchmark_coordinates"]
            dist_impl = verify_coords.haversine_distance_km(cand["latitude"], cand["longitude"], bench[0], bench[1])
            dist_oracle = oracle_haversine(cand["latitude"], cand["longitude"], bench[0], bench[1])

            oracle_diff_mm = abs(dist_impl - dist_oracle) * 1e6
            within_tolerance = dist_impl < 2.0
            oracle_matches = (oracle_diff_mm < 0.01)  # < 0.01 millimeter difference

            passed = within_tolerance and oracle_matches
            self.record_result(
                f"Benchmark Audit - {loc_id}",
                passed,
                f"Dist = {dist_impl*1000:.2f} m (<2000m), Oracle diff = {oracle_diff_mm:.4f} mm"
            )

    def print_summary(self) -> bool:
        total = self.passed_tests + self.failed_tests
        print("\n" + "=" * 80)
        print(f"ADVERSARIAL STRESS TEST SUMMARY: {self.passed_tests}/{total} PASSED")
        print("=" * 80)
        return self.failed_tests == 0


if __name__ == "__main__":
    runner = AdversarialTestRunner()
    runner.test_mathematical_edge_cases()
    runner.test_negative_and_mutations()
    runner.test_authoritative_benchmarks()
    all_passed = runner.print_summary()
    sys.exit(0 if all_passed else 1)
