#!/bin/bash
# create-site.sh
# This script is run by the "create-site" service container on first boot.
#
# ROOT CAUSE OF CSS 404:
#   bench build creates SYMLINKS in sites/assets/<app> -> apps/<app>/../public
#   These symlinks are stored IN THE VOLUME but point to the CONTAINER's
#   local filesystem paths. So the frontend container follows its OWN symlink
#   to ITS OWN copy of apps/ in its own image layer - not where bench build ran.
#   Result: bench build's built dist/ files are invisible to other containers.
#
# FIX: After bench build, copy dist/ files as REAL FILES into the volume at
#   sites/assets/logistics_wizard/dist/ (by removing the symlink first).
#   Also merge assets.json properly in the volume.
#
# IDEMPOTENT: skips site creation if site already exists.

set -e

SITE_NAME="${FRAPPE_SITE_NAME:-logistics.local}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
MARIADB_ROOT_PASSWORD="${MARIADB_ROOT_PASSWORD:-admin}"
BENCH_DIR="/home/frappe/frappe-bench"

echo ">>> Checking if site '$SITE_NAME' already exists..."

if bench --site "$SITE_NAME" list-apps > /dev/null 2>&1; then
    echo ">>> Site '$SITE_NAME' already exists. Skipping site creation."
else
    echo ">>> Creating site '$SITE_NAME'..."
    bench new-site "$SITE_NAME" \
        --mariadb-root-password "$MARIADB_ROOT_PASSWORD" \
        --admin-password "$ADMIN_PASSWORD" \
        --no-mariadb-socket

    echo ">>> Installing ERPNext..."
    bench --site "$SITE_NAME" install-app erpnext

    echo ">>> Installing logistics_wizard..."
    bench --site "$SITE_NAME" install-app logistics_wizard

    BACKUP_SQL="$BENCH_DIR/backups/latest/database.sql.gz"
    BACKUP_PUB="$BENCH_DIR/backups/latest/files.tar"
    BACKUP_PRIV="$BENCH_DIR/backups/latest/private-files.tar"

    if [ -f "$BACKUP_SQL" ]; then
        echo ">>> Found database snapshot in backups/latest/. Restoring snapshot..."
        RESTORE_ARGS="--mariadb-root-password $MARIADB_ROOT_PASSWORD --force"
        [ -f "$BACKUP_PUB" ] && RESTORE_ARGS="$RESTORE_ARGS --with-public-files $BACKUP_PUB"
        [ -f "$BACKUP_PRIV" ] && RESTORE_ARGS="$RESTORE_ARGS --with-private-files $BACKUP_PRIV"
        bench --site "$SITE_NAME" restore "$BACKUP_SQL" $RESTORE_ARGS
        bench --site "$SITE_NAME" migrate
    else
        echo ">>> Seeding initial procurement data (Apple Inc. Air/Ocean, Landed Cost)..."
        $BENCH_DIR/env/bin/python3 "$BENCH_DIR/generate_procurement_data.py" || true
    fi
fi

# Ensure demo data exists if site was already created but empty
$BENCH_DIR/env/bin/python3 -c "
import os, sys
sites_dir = '$BENCH_DIR/sites'
if os.path.exists(sites_dir): os.chdir(sites_dir)
import frappe
try:
    frappe.init(site='$SITE_NAME')
    frappe.connect()
    count = frappe.db.count('Purchase Order')
    if count == 0:
        print('EMPTY')
    else:
        print('FOUND_' + str(count))
except Exception as e:
    print('ERROR: ' + str(e))
" > /tmp/po_status.txt 2>/dev/null || true

PO_STATUS=$(cat /tmp/po_status.txt 2>/dev/null || echo "ERROR")
if [ "$PO_STATUS" = "EMPTY" ]; then
    echo ">>> No purchase orders found. Seeding initial procurement data..."
    $BENCH_DIR/env/bin/python3 "$BENCH_DIR/generate_procurement_data.py" || true
else
    echo ">>> Purchase orders status: $PO_STATUS."
fi

echo ">>> Building JS/CSS assets for logistics_wizard..."
bench build --app logistics_wizard

# ─── KEY FIX: Copy built dist/ as REAL files into volume ──────────────────
# bench build output: apps/logistics_wizard/logistics_wizard/public/dist/
# bench also creates a SYMLINK in the volume: sites/assets/logistics_wizard -> apps/.../public
# We remove that symlink and replace it with a real directory containing the built files.
DIST_SRC="$BENCH_DIR/apps/logistics_wizard/logistics_wizard/public"
DIST_DEST="$BENCH_DIR/sites/assets/logistics_wizard"

echo ">>> Replacing symlink with real dir in volume at $DIST_DEST ..."
# Remove the symlink that bench build created in the volume
if [ -L "$DIST_DEST" ]; then
    rm "$DIST_DEST"
    echo "    Symlink removed."
fi

# Create the real directory and copy ALL public files (css, js, images, dist/)
mkdir -p "$DIST_DEST"
cp -rf "$DIST_SRC/." "$DIST_DEST/"
echo "    Copied all public/ files to $DIST_DEST/"

# ─── Merge assets.json into volume ────────────────────────────────────────
echo ">>> Merging assets.json into volume..."
python3 - << 'PYEOF'
import json, os, shutil

bench_dir = "/home/frappe/frappe-bench"
dest_json  = f"{bench_dir}/sites/assets/assets.json"
dest_rtlj  = f"{bench_dir}/sites/assets/assets-rtl.json"
src_json   = f"{bench_dir}/assets/assets.json"

dest = {}
if os.path.exists(dest_json):
    with open(dest_json) as f:
        dest = json.load(f)

if os.path.exists(src_json):
    with open(src_json) as f:
        src = json.load(f)
    dest.update(src)

dest_rtl = {}
if os.path.exists(dest_rtlj):
    with open(dest_rtlj) as f:
        dest_rtl = json.load(f)
    for k in list(dest_rtl.keys()):
        if "logistics_wizard" in dest_rtl[k]:
            del dest_rtl[k]
    with open(dest_rtlj, "w") as f:
        json.dump(dest_rtl, f, indent=4)

# Dynamic scan of newly built dist folder
dist_dir = f"{bench_dir}/sites/assets/logistics_wizard/dist"
for subdir in ["js", "css"]:
    subpath = os.path.join(dist_dir, subdir)
    if not os.path.isdir(subpath):
        continue
    for f in os.listdir(subpath):
        if f.endswith(".map"):
            continue
        parts = f.rsplit(".", 2)
        if len(parts) == 3:
            base_name = parts[0] + "." + parts[2]
            url_path = f"/assets/logistics_wizard/dist/{subdir}/{f}"
            dest[base_name] = url_path
            # Also create an unhashed copy as fallback
            unhashed_file = os.path.join(subpath, base_name)
            if not os.path.exists(unhashed_file):
                try:
                    shutil.copyfile(os.path.join(subpath, f), unhashed_file)
                except Exception:
                    pass

with open(dest_json, "w") as f:
    json.dump(dest, f, indent=4)

lw = [(k,v) for k,v in dest.items() if "logistics_wizard" in v]
for k,v in lw:
    print(f"  {k} -> {v}")
PYEOF

echo ">>> Clearing cache (including shared assets_json)..."
bench --site "$SITE_NAME" clear-cache
$BENCH_DIR/env/bin/python3 -c "
import os
sites_dir = '$BENCH_DIR/sites'
if os.path.exists(sites_dir): os.chdir(sites_dir)
import frappe
try:
    frappe.init(site='$SITE_NAME')
    frappe.connect()
    frappe.cache.delete_value('assets_json', shared=True)
except Exception:
    pass
" || true

echo ""
echo ">>> ✅ Setup complete! Site '$SITE_NAME' is ready."
echo ">>> Access at: http://localhost:2828 | Login: Administrator / $ADMIN_PASSWORD"
