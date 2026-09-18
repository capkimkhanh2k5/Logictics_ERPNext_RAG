import time
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8080"


def run_adversarial_challenges():
    print("==================================================================")
    print("STARTING ADVERSARIAL CHALLENGER SUITE FOR LOGISTICS WIZARD WIDGET")
    print("==================================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Step 0: Authentication
        print("\n--- Pre-flight: Authentication ---")
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        page.fill("#login_email", "Administrator")
        page.fill("#login_password", "admin")
        page.click("button.btn-login")
        page.wait_for_url("**/app**", timeout=20000)
        page.wait_for_load_state("networkidle")
        print("Logged in successfully as Administrator.")

        # ================================================================
        # CHALLENGE 1: Route Transitions (Form -> List -> Non-workflow -> Form)
        # ================================================================
        print("\n--- Challenge 1: Route Transitions & State Integrity ---")
        
        # 1.1 Form view of Complete Chain (PUR-ORD-2026-00002)
        print("1.1 Navigating to Form view: PUR-ORD-2026-00002")
        page.goto(f"{BASE_URL}/app/purchase-order/PUR-ORD-2026-00002", wait_until="networkidle")
        page.wait_for_selector("#wiz-Material-Request.wiz-step-completed", timeout=10000)
        
        # Verify complete chain has 6 completed steps and 6 checkmarks
        completed_count = page.locator("#logistics-wizard-content .wiz-step-completed").count()
        check_count = page.locator("#logistics-wizard-content .wiz-check-badge").count()
        print(f"  Complete chain - Completed steps count: {completed_count}/6, Checkmarks: {check_count}/6")
        assert completed_count == 6, f"Expected 6 completed steps, found {completed_count}"
        assert check_count == 6, f"Expected 6 checkmarks, found {check_count}"

        # 1.2 Route transition: Form view -> List view of Purchase Order
        print("1.2 Transitioning to List view: /app/purchase-order")
        page.goto(f"{BASE_URL}/app/purchase-order", wait_until="networkidle")
        page.wait_for_timeout(1000) # allow route change and DOM update

        # In List view:
        # All completed classes MUST be removed
        # All checkmark badges MUST be removed
        # Only wiz-Purchase-Order should have wiz-step-current (blue)
        list_completed = page.locator("#logistics-wizard-content .wiz-step-completed").count()
        list_checks = page.locator("#logistics-wizard-content .wiz-check-badge").count()
        po_classes = page.locator("#wiz-Purchase-Order").get_attribute("class") or ""
        po_color = page.locator("#wiz-Purchase-Order").evaluate("el => getComputedStyle(el).color")
        mr_href = page.locator("#wiz-Material-Request a").get_attribute("href") or ""

        print(f"  List view - Completed classes remaining: {list_completed} (expected 0)")
        print(f"  List view - Checkmarks remaining: {list_checks} (expected 0)")
        print(f"  List view - Purchase Order class: '{po_classes}', Color: {po_color}")
        print(f"  List view - Material Request href reset to: '{mr_href}' (expected '/app/material-request')")

        assert list_completed == 0, f"Stale completed classes found in List view! Count: {list_completed}"
        assert list_checks == 0, f"Stale checkmark badges found in List view! Count: {list_checks}"
        assert "wiz-step-current" in po_classes, f"Purchase Order should be current step in List view"
        assert mr_href == "/app/material-request", f"Href was not reset, got '{mr_href}'"
        print("  >> 1.2 Form -> List transition PASSED.")

        # 1.3 Route transition: Non-workflow DocType List (Item)
        print("1.3 Transitioning to non-workflow DocType List: /app/item")
        page.goto(f"{BASE_URL}/app/item", wait_until="networkidle")
        page.wait_for_timeout(1000)

        item_completed = page.locator("#logistics-wizard-content .wiz-step-completed").count()
        item_current = page.locator("#logistics-wizard-content .wiz-step-current").count()
        item_checks = page.locator("#logistics-wizard-content .wiz-check-badge").count()
        print(f"  Item List - Completed: {item_completed}, Current: {item_current}, Checks: {item_checks}")

        assert item_completed == 0, "No step should be completed in non-workflow List view"
        assert item_current == 0, "No step should be current in non-workflow List view"
        assert item_checks == 0, "No checkmarks should exist in non-workflow List view"
        print("  >> 1.3 Transition to non-workflow DocType List PASSED.")

        # 1.4 Route transition: Non-workflow DocType Form (User / Administrator)
        print("1.4 Transitioning to non-workflow DocType Form: /app/user/Administrator")
        page.goto(f"{BASE_URL}/app/user/Administrator", wait_until="networkidle")
        page.wait_for_timeout(1000)

        user_completed = page.locator("#logistics-wizard-content .wiz-step-completed").count()
        user_current = page.locator("#logistics-wizard-content .wiz-step-current").count()
        user_checks = page.locator("#logistics-wizard-content .wiz-check-badge").count()
        print(f"  User Form - Completed: {user_completed}, Current: {user_current}, Checks: {user_checks}")

        assert user_completed == 0, "No step should be completed in User Form view"
        assert user_current == 0, "No step should be current in User Form view"
        assert user_checks == 0, "No checkmarks should exist in User Form view"
        print("  >> 1.4 Transition to non-workflow DocType Form PASSED.")

        # 1.5 Route transition: Back to Partial Workflow Form (PUR-ORD-2026-00001)
        print("1.5 Transitioning to Partial Chain Form: /app/purchase-order/PUR-ORD-2026-00001")
        page.goto(f"{BASE_URL}/app/purchase-order/PUR-ORD-2026-00001", wait_until="networkidle")
        page.wait_for_selector("#wiz-Purchase-Order.wiz-step-completed", timeout=10000)

        partial_completed = page.locator("#logistics-wizard-content .wiz-step-completed").count()
        partial_pending = page.locator("#logistics-wizard-content .wiz-step-pending").count()
        partial_checks = page.locator("#logistics-wizard-content .wiz-check-badge").count()
        print(f"  Partial Form - Completed: {partial_completed}/4, Pending: {partial_pending}/2, Checks: {partial_checks}/4")

        assert partial_completed == 4, f"Expected 4 completed steps, got {partial_completed}"
        assert partial_pending == 2, f"Expected 2 pending steps (MR and Stock Entry), got {partial_pending}"
        assert partial_checks == 4, f"Expected 4 checkmarks, got {partial_checks}"
        print("  >> 1.5 Transition to Partial Chain Form PASSED.")

        # 1.6 Route transition: Non-workflow DocType Customer
        print("1.6 Transitioning to another non-workflow DocType: /app/customer")
        page.goto(f"{BASE_URL}/app/customer", wait_until="networkidle")
        page.wait_for_timeout(1000)

        cust_completed = page.locator("#logistics-wizard-content .wiz-step-completed").count()
        cust_current = page.locator("#logistics-wizard-content .wiz-step-current").count()
        cust_checks = page.locator("#logistics-wizard-content .wiz-check-badge").count()
        print(f"  Customer List - Completed: {cust_completed}, Current: {cust_current}, Checks: {cust_checks}")

        assert cust_completed == 0, "Customer view must be clean of completed steps"
        assert cust_current == 0, "Customer view must be clean of current step"
        assert cust_checks == 0, "Customer view must be clean of checkmarks"
        print("  >> 1.6 Transition to Customer PASSED.")

        # ================================================================
        # CHALLENGE 2: Expand/Collapse slideToggle Behavior
        # ================================================================
        print("\n--- Challenge 2: Expand/Collapse slideToggle Behavior ---")
        header = page.locator("#logistics-wizard-bubble div:has-text('Import-Export Wizard')")
        content = page.locator("#logistics-wizard-content")

        # 2.1 Verify initial state is visible
        assert content.is_visible(), "Content section should initially be visible"
        print("2.1 Content is initially visible.")

        # 2.2 Click to collapse
        print("2.2 Clicking header to collapse...")
        header.click()
        page.wait_for_timeout(600)  # wait for slideToggle animation (default 400ms)
        is_visible_after_1 = content.is_visible()
        print(f"  Content visibility after 1st click: {is_visible_after_1}")
        assert not is_visible_after_1, "Content section should be hidden after 1st click"

        # 2.3 Click to re-expand
        print("2.3 Clicking header to expand...")
        header.click()
        page.wait_for_timeout(600)  # wait for slideToggle animation
        is_visible_after_2 = content.is_visible()
        print(f"  Content visibility after 2nd click: {is_visible_after_2}")
        assert is_visible_after_2, "Content section should be visible after 2nd click"

        # 2.4 Rapid clicks stress test (5 rapid clicks)
        print("2.4 Rapid clicks stress test (5 consecutive clicks)...")
        for i in range(5):
            header.click()
            time.sleep(0.05)
        # Wait for jQuery animation queue to drain
        page.wait_for_timeout(1500)
        is_visible_after_rapid = content.is_visible()
        print(f"  Content visibility after 5 rapid clicks (odd number of toggles): {is_visible_after_rapid}")
        # An odd number of toggles from visible should result in hidden
        assert not is_visible_after_rapid, "Content should be hidden after 5 rapid clicks"

        # Restore to expanded state
        header.click()
        page.wait_for_timeout(600)
        assert content.is_visible(), "Content restored to visible"
        print("  >> Challenge 2: slideToggle behavior PASSED.")

        # ================================================================
        # CHALLENGE 3: Viewport & Responsiveness
        # ================================================================
        print("\n--- Challenge 3: Viewport & Responsiveness ---")
        bubble = page.locator("#logistics-wizard-bubble")

        # 3.1 Standard Desktop (1920x1080)
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.wait_for_timeout(300)
        box_desktop = bubble.bounding_box()
        print(f"  Desktop 1920x1080 bounding box: {box_desktop}")
        assert box_desktop is not None, "Bubble bounding box should not be null"
        assert box_desktop["x"] >= 0 and box_desktop["y"] >= 0, "Bubble should be within viewport bounds"
        assert bubble.is_visible(), "Bubble should remain visible on 1920x1080"

        # 3.2 Scroll resilience: does fixed positioning hold?
        page.evaluate("window.scrollBy(0, 800)")
        page.wait_for_timeout(300)
        box_scrolled = bubble.bounding_box()
        print(f"  After scrollBy(0, 800) bounding box: {box_scrolled}")
        assert abs(box_desktop["y"] - box_scrolled["y"]) < 5, "Bubble Y-coordinate should remain fixed during scroll"

        # 3.3 Tablet Viewport (768x1024)
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(300)
        box_tablet = bubble.bounding_box()
        print(f"  Tablet 768x1024 bounding box: {box_tablet}")
        assert bubble.is_visible(), "Bubble should remain visible on tablet viewport"
        assert box_tablet["x"] >= 0 and box_tablet["y"] >= 0, "Bubble within tablet viewport"

        # 3.4 Mobile Viewport (375x667)
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(300)
        box_mobile = bubble.bounding_box()
        print(f"  Mobile 375x667 bounding box: {box_mobile}")
        assert bubble.is_visible(), "Bubble should remain visible on mobile viewport"
        # 320px width + 2*1px border on 375px screen leaves 53px margin -> fits within viewport
        assert box_mobile["width"] in [320, 322], f"Expected ~320px width, got {box_mobile['width']}"
        print("  >> Challenge 3: Viewport & Responsiveness PASSED.")

        # ================================================================
        # CHALLENGE 4: Client-Side SPA In-App Link Navigation
        # ================================================================
        print("\n--- Challenge 4: In-App Direct Link Navigation via Bubble ---")
        # Reset to standard desktop viewport
        page.set_viewport_size({"width": 1280, "height": 800})
        page.goto(f"{BASE_URL}/app/purchase-order/PUR-ORD-2026-00002", wait_until="networkidle")
        page.wait_for_selector("#wiz-Material-Request.wiz-step-completed", timeout=10000)

        # Click on the Material Request link inside the bubble
        mr_link = page.locator("#wiz-Material-Request a")
        mr_target_href = mr_link.get_attribute("href")
        print(f"  Clicking Material Request link in bubble: {mr_target_href}")
        mr_link.click()

        # Check that page navigates to /app/material-request/MAT-MR-2026-00001
        page.wait_for_url("**/app/material-request/MAT-MR-2026-00001**", timeout=10000)
        print(f"  Current URL after click: {page.url}")
        assert "/app/material-request/MAT-MR-2026-00001" in page.url, "Navigated to Material Request via bubble link"

        # In Material Request form, wait for widget to update with MR as current
        page.wait_for_selector("#wiz-Material-Request.wiz-step-current", timeout=10000)
        mr_is_current = "wiz-step-current" in (page.locator("#wiz-Material-Request").get_attribute("class") or "")
        print(f"  Material Request is current step in new view: {mr_is_current}")
        assert mr_is_current, "Material Request should be marked as current step after link click"
        print("  >> Challenge 4: In-App Direct Link Navigation PASSED.")

        browser.close()

    print("\n==================================================================")
    print("ALL 4 ADVERSARIAL CHALLENGES COMPLETED AND PASSED EMPIRICALLY!")
    print("==================================================================")


if __name__ == "__main__":
    run_adversarial_challenges()
