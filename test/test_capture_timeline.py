#!/usr/bin/env python3
import os
import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:2828"
ARTIFACT_DIR = "/Users/capkimkhanh/.gemini/antigravity/brain/85706d3d-4e4d-4185-ad85-5148c88d3db7"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 1366, "height": 900})
        page = context.new_page()

        print("1. Logging into Frappe Desk...")
        page.goto(f"{BASE_URL}/login")
        page.fill("#login_email", "Administrator")
        page.fill("#login_password", "admin")
        page.click(".btn-login")
        page.wait_for_url("**/app**", timeout=15000)
        print("  Logged in successfully.")

        print("2. Opening FAB & Shipment Modal...")
        page.wait_for_selector("#lw-fab-main", timeout=10000)
        page.click("#lw-fab-main")
        time.sleep(0.5)
        page.click("#lw-fab-shipment")
        time.sleep(1.0)

        print("3. Locating PUR-ORD-2026-00003...")
        page.wait_for_selector(".lw-shipment-item", timeout=10000)
        items = page.query_selector_all(".lw-shipment-item")
        found = False
        for item in items:
            name = item.get_attribute("data-name") or ""
            text = item.inner_text()
            print(f"  Found shipment item: {name}")
            if "00003" in name or "00003" in text:
                print(f"  Clicking {name}...")
                item.click()
                found = True
                break
        
        if not found and items:
            print("  Item 00003 not matched directly, clicking first item...")
            items[0].click()

        time.sleep(3.0)

        print("4. Checking Timeline elements...")
        timeline_info = page.evaluate("""() => {
            const items = document.querySelectorAll('.lw-timeline-item');
            const results = [];
            items.forEach(el => {
                const dateEl = el.querySelector('.lw-timeline-date');
                const actEl = el.querySelector('.lw-timeline-activity');
                const badgeEl = el.querySelector('.lw-timeline-current-badge');
                const nodeEl = el.querySelector('.lw-timeline-node');
                results.push({
                    activity: actEl ? actEl.innerText : '',
                    date: dateEl ? dateEl.innerText : '',
                    isCurrent: !!badgeEl,
                    hasNode: !!nodeEl,
                    nodeClasses: nodeEl ? nodeEl.className : '',
                    itemClasses: el.className
                });
            });
            return results;
        }""")
        for t in timeline_info:
            d = t.get('date')
            act = t.get('activity')
            curr = t.get('isCurrent')
            nc = t.get('nodeClasses')
            print(f"  - [{d}] {act} | current={curr} | classes={nc}")

        print("5. Scrolling #lw-shipment-content down to reveal timeline...")
        page.evaluate("""() => {
            const scroller = document.querySelector('#lw-shipment-content');
            if (scroller) {
                scroller.scrollTop = scroller.scrollHeight;
            }
        }""")
        time.sleep(1.0)

        screenshot_path = os.path.join(ARTIFACT_DIR, "timeline_impeccable_verified.png")
        page.screenshot(path=screenshot_path)
        print(f"6. Full modal screenshot saved: {screenshot_path}")

        timeline_el = page.query_selector(".lw-timeline")
        if timeline_el:
            timeline_screenshot = os.path.join(ARTIFACT_DIR, "timeline_zoomed_verified.png")
            timeline_el.screenshot(path=timeline_screenshot)
            print(f"7. Zoomed timeline screenshot saved: {timeline_screenshot}")

        browser.close()

if __name__ == "__main__":
    main()
