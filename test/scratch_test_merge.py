
import os
import json
import sys

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BENCH_DIR = os.path.dirname(TEST_DIR) if os.path.basename(TEST_DIR) == "test" else TEST_DIR
if TEST_DIR not in sys.path:
    sys.path.insert(0, TEST_DIR)

from verify_coords import haversine_distance_km, DEFAULT_TOLERANCE_KM

loc_file = os.path.join(BENCH_DIR, 'apps/logistics_wizard/logistics_wizard/data/locations.json')
with open(loc_file) as f:
    master = json.load(f)

locs = master['locations']
# Additional entries
import subprocess
