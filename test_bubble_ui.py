import sys
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8080"

def test_bubble_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        page.fill("#login_email", "Administrator")
        page.fill("#login_password", "admin")
        page.click("button.btn-login")

        page.wait_for_url("**/app**", timeout=20000)
        page.wait_for_load_state("networkidle")

        page.goto(f"{BASE_URL}/app/purchase-order/PUR-ORD-2026-00002", wait_until="networkidle")

        page.wait_for_selector("#lw-fab-main", timeout=15000)
        page.click("#lw-fab-main")
        time.sleep(1)
        
        page.click("#lw-fab-workflow")
        time.sleep(1)
        page.screenshot(path="fab_workflow.png")
        page.click("#lw-modal-workflow .lw-modal-close")
        time.sleep(1)
        
        page.click("#lw-fab-shipment")
        time.sleep(1)
        page.screenshot(path="fab_shipment.png")
        page.click("#lw-modal-shipment .lw-modal-close")
        time.sleep(1)
        
        page.click("#lw-fab-ai")
        time.sleep(1)
        page.screenshot(path="fab_ai.png")
        page.click("#lw-modal-ai .lw-modal-close")
        
        browser.close()

if __name__ == "__main__":
    test_bubble_ui()
