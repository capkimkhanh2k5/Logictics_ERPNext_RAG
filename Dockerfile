FROM frappe/erpnext:v15

USER root

# Copy the site-creation script and demo data generator
COPY create-site.sh /home/frappe/frappe-bench/create-site.sh
COPY generate_procurement_data.py /home/frappe/frappe-bench/generate_procurement_data.py
RUN chmod +x /home/frappe/frappe-bench/create-site.sh && \
    chown frappe:frappe /home/frappe/frappe-bench/create-site.sh /home/frappe/frappe-bench/generate_procurement_data.py

USER frappe

# Copy the custom app source code into the image
COPY --chown=frappe:frappe apps/logistics_wizard /home/frappe/frappe-bench/apps/logistics_wizard

# Install the app into the Python virtual environment
RUN cd /home/frappe/frappe-bench && \
    ./env/bin/pip install -q -U -e ./apps/logistics_wizard

# Register app in apps.txt (use printf to ensure a newline before appending)
RUN printf "\nlogistics_wizard\n" >> /home/frappe/frappe-bench/sites/apps.txt

# ─── Build assets and bake into image ──────────────────────────────────────
# NOTE: bench build cannot update assets.json during docker build because
# there is no Redis available. We run bench build to compile the CSS/JS files,
# then manually scan the output dist/ folder and write the hashes into
# assets.json ourselves using Python.
RUN cd /home/frappe/frappe-bench && \
    bench build --app logistics_wizard || true && \
    BAKED=/home/frappe/frappe-bench/assets && \
    APP_PUBLIC=/home/frappe/frappe-bench/apps/logistics_wizard/logistics_wizard/public && \
    mkdir -p $BAKED/logistics_wizard && \
    cp -rf $APP_PUBLIC/. $BAKED/logistics_wizard/ && \
    python3 - << 'PYEOF'
import json, os, glob, shutil

baked = "/home/frappe/frappe-bench/assets"
assets_json_path = baked + "/assets.json"
assets_rtl_json_path = baked + "/assets-rtl.json"

# Scan the built dist directories for hashed files
dist_base = baked + "/logistics_wizard/dist"

new_entries = {}
new_rtl_entries = {}

for subdir in ["js", "css", "css-rtl"]:
    path = os.path.join(dist_base, subdir)
    if not os.path.isdir(path):
        continue
    for f in os.listdir(path):
        if f.endswith(".map"):
            continue
        parts = f.rsplit(".", 2)
        if len(parts) == 3:
            base_name = parts[0] + "." + parts[2]
            url_path = f"/assets/logistics_wizard/dist/{subdir}/{f}"
            if subdir == "css-rtl":
                new_rtl_entries["rtl_" + base_name] = url_path
            else:
                new_entries[base_name] = url_path
            
            # Create unhashed fallback copy in dist/subdir
            unhashed_file = os.path.join(path, base_name)
            if not os.path.exists(unhashed_file):
                try:
                    shutil.copyfile(os.path.join(path, f), unhashed_file)
                except Exception:
                    pass
            print(f"  {base_name} -> {url_path}")

# Load existing assets.json and merge
if os.path.exists(assets_json_path):
    with open(assets_json_path) as f:
        data = json.load(f)
    data.update(new_entries)
    with open(assets_json_path, "w") as f:
        json.dump(data, f, indent=4)

if os.path.exists(assets_rtl_json_path):
    with open(assets_rtl_json_path) as f:
        rtl_data = json.load(f)
    rtl_data.update(new_rtl_entries)
    with open(assets_rtl_json_path, "w") as f:
        json.dump(rtl_data, f, indent=4)

print(f"Updated assets.json with {len(new_entries)} entries and unhashed fallbacks")
PYEOF
