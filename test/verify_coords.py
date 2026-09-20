#!/usr/bin/env python3
"""
verify_coords.py — Coordinate Data Verification Script
======================================================
Verifies that coordinates defined in locations.json strictly comply with
authoritative international standards (NGA World Port Index, UN/LOCODE,
OurAirports IATA/ICAO, and USGS/OSM benchmarks).

Acceptance Criteria:
- Max geodesic discrepancy < 2.0 km for all logistics nodes.
- Earth Model: WGS-84 mean volumetric radius R = 6,371.0088 km (IUGG).
- Return exit code 0 when all stations pass.
"""

import sys
import os
import json
import math
import argparse

# Earth mean radius in kilometers (IUGG recommended value for geodesic calculations)
EARTH_RADIUS_KM = 6371.0088
DEFAULT_TOLERANCE_KM = 2.0


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes the Great-Circle distance between two points on a spherical Earth
    using the numerically stable Haversine formula.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    # Guard against floating-point inaccuracies pushing a outside [0, 1]
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def resolve_default_locations_file() -> str:
    """
    Finds the default locations.json path whether invoked from bench root
    or another directory.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bench_dir = os.path.dirname(script_dir) if os.path.basename(script_dir) == "test" else script_dir
    candidates = [
        os.path.join(bench_dir, "apps", "logistics_wizard", "logistics_wizard", "data", "locations.json"),
        os.path.join(os.getcwd(), "apps", "logistics_wizard", "logistics_wizard", "data", "locations.json"),
        os.path.join(script_dir, "apps", "logistics_wizard", "logistics_wizard", "data", "locations.json"),
        os.path.join(os.getcwd(), "data", "locations.json"),
        os.path.join(script_dir, "data", "locations.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return os.path.join(bench_dir, "apps", "logistics_wizard", "logistics_wizard", "data", "locations.json")


def verify_locations(file_path: str, tolerance_km: float = DEFAULT_TOLERANCE_KM) -> bool:
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error parsing JSON file {file_path}: {e}", file=sys.stderr)
            return False

    locations = data.get("locations", {})
    if not locations:
        print("Error: No locations found in JSON.", file=sys.stderr)
        return False

    print("=" * 96)
    print(f" LOGISTICS WIZARD — COORDINATE VERIFICATION REPORT (Tolerance < {tolerance_km:.1f} km)")
    print(f" Source File: {file_path}")
    print("=" * 96)
    header = f"{'ID':<24} | {'Type':<8} | {'Standard Code':<12} | {'Discrepancy':<14} | {'Tolerance':<10} | {'Status'}"
    print(header)
    print("-" * 96)

    all_passed = True
    results = []

    for loc_id, item in locations.items():
        coords = item.get("coordinates", {})
        cand_lat = coords.get("latitude")
        cand_lon = coords.get("longitude")

        ref = item.get("reference", {})
        bench = ref.get("benchmark_coordinates", [])

        if cand_lat is None or cand_lon is None or len(bench) < 2:
            print(f"{loc_id:<24} | {'MISSING COORDS OR BENCHMARK':<65} | [FAIL]")
            all_passed = False
            continue

        if not (-90.0 <= cand_lat <= 90.0 and -180.0 <= cand_lon <= 180.0):
            print(f"{loc_id:<24} | {'COORDINATES OUT OF WGS84 RANGE':<65} | [FAIL]")
            all_passed = False
            continue

        bench_lat, bench_lon = bench[0], bench[1]
        dist_km = haversine_distance_km(cand_lat, cand_lon, bench_lat, bench_lon)
        dist_m = dist_km * 1000.0

        is_passed = dist_km <= tolerance_km
        if not is_passed:
            all_passed = False

        status_str = "PASS" if is_passed else "FAIL"
        
        codes = item.get("codes", {})
        code_display = codes.get("un_locode") or codes.get("iata") or (f"WPI:{codes.get('wpi_id')}" if codes.get("wpi_id") else "-")

        loc_type = item.get("type", "node")
        print(f"{loc_id:<24} | {loc_type:<8} | {code_display:<12} | {dist_m:>9.1f} m    | < {tolerance_km*1000:.0f} m    | [{status_str}]")

        results.append({
            "id": loc_id,
            "name": item.get("name"),
            "discrepancy_m": dist_m,
            "discrepancy_km": dist_km,
            "passed": is_passed,
            "authority": ref.get("authority")
        })

    print("-" * 96)
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    print(f"Summary: {passed_count}/{total} locations verified within {tolerance_km} km tolerance.")
    
    if all_passed and total > 0:
        print("Verdict: ALL LOCATIONS FULLY COMPLIANT WITH INTERNATIONAL STANDARDS.")
    else:
        print("Verdict: VERIFICATION FAILED. Some coordinates exceed tolerance threshold.", file=sys.stderr)

    print("=" * 96)
    return all_passed and total > 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify location coordinates against authoritative benchmarks.")
    parser.add_argument("--file", "-f", default=None, help="Path to locations.json (defaults to apps/logistics_wizard/logistics_wizard/data/locations.json)")
    parser.add_argument("--tolerance", "-t", type=float, default=DEFAULT_TOLERANCE_KM, help="Tolerance in km (default: 2.0 km)")
    args = parser.parse_args()

    target_file = args.file if args.file else resolve_default_locations_file()
    success = verify_locations(target_file, args.tolerance)
    sys.exit(0 if success else 1)
