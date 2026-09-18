import json
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

API_URL = "http://localhost:8080/api/method/logistics_wizard.api.get_workflow_chain_status"


def post_api(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed = time.perf_counter() - start
            body = resp.read().decode("utf-8")
            return {
                "status_code": resp.status,
                "elapsed": elapsed,
                "body": json.loads(body) if body else {},
                "error": None,
            }
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - start
        err_body = e.read().decode("utf-8")
        try:
            parsed_err = json.loads(err_body)
        except Exception:
            parsed_err = err_body
        return {
            "status_code": e.code,
            "elapsed": elapsed,
            "body": parsed_err,
            "error": str(e),
        }
    except Exception as e:
        elapsed = time.perf_counter() - start
        return {
            "status_code": 0,
            "elapsed": elapsed,
            "body": None,
            "error": str(e),
        }


def run_suite_1():
    print("=" * 80)
    print("TEST SUITE 1: INPUT VALIDATION & ADVERSARIAL PAYLOADS")
    print("=" * 80)

    results = []

    # 1.1 Missing arguments
    missing_cases = [
        ("Empty dict {}", {}),
        ("Missing docname", {"doctype": "Purchase Order"}),
        ("Missing doctype", {"docname": "PUR-ORD-2026-00001"}),
    ]
    for desc, payload in missing_cases:
        res = post_api(payload)
        is_500 = res["status_code"] == 500
        print(f"[{'FAIL - HTTP 500' if is_500 else 'PASS'}] {desc}: Status {res['status_code']}")
        if is_500:
            exc = res["body"].get("exception") if isinstance(res["body"], dict) else str(res["body"])
            print(f"       Exception: {exc}")
        results.append({
            "test": f"1.1 {desc}",
            "payload": payload,
            "status": res["status_code"],
            "pass": not is_500,
            "details": res["body"],
        })

    # 1.2 Empty / null values
    empty_cases = [
        ("Empty strings", {"doctype": "", "docname": ""}),
        ("Null values", {"doctype": None, "docname": None}),
        ("Whitespace strings", {"doctype": "   ", "docname": "   "}),
        ("DocType with empty docname", {"doctype": "Purchase Order", "docname": ""}),
        ("DocType with null docname", {"doctype": "Purchase Order", "docname": None}),
        ("Empty doctype with valid docname", {"doctype": "", "docname": "PUR-ORD-2026-00001"}),
    ]
    for desc, payload in empty_cases:
        res = post_api(payload)
        passed = (res["status_code"] == 200)
        print(f"[{'PASS' if passed else 'FAIL'}] {desc}: Status {res['status_code']}")
        results.append({
            "test": f"1.2 {desc}",
            "payload": payload,
            "status": res["status_code"],
            "pass": passed,
            "details": res["body"],
        })

    # 1.3 Invalid / Non-workflow DocTypes
    invalid_dt_cases = [
        ("Completely Non-existent DocType", {"doctype": "NonExistentDocType", "docname": "XYZ"}),
        ("Existing Non-workflow DocType (User)", {"doctype": "User", "docname": "Administrator"}),
        ("Existing Non-workflow DocType (Customer)", {"doctype": "Customer", "docname": "CUST-0001"}),
        ("Existing Non-workflow DocType (Item)", {"doctype": "Item", "docname": "ITEM-001"}),
    ]
    for desc, payload in invalid_dt_cases:
        res = post_api(payload)
        passed = (res["status_code"] == 200)
        print(f"[{'PASS' if passed else 'FAIL'}] {desc}: Status {res['status_code']}")
        results.append({
            "test": f"1.3 {desc}",
            "payload": payload,
            "status": res["status_code"],
            "pass": passed,
            "details": res["body"],
        })

    # 1.4 Non-existent records across all 6 DocTypes
    non_existent_cases = [
        ("Material Request", {"doctype": "Material Request", "docname": "NON-EXISTENT-MR-99999"}),
        ("Purchase Order", {"doctype": "Purchase Order", "docname": "NON-EXISTENT-PO-99999"}),
        ("Shipment Tracking", {"doctype": "Shipment Tracking", "docname": "NON-EXISTENT-ST-99999"}),
        ("Purchase Receipt", {"doctype": "Purchase Receipt", "docname": "NON-EXISTENT-PR-99999"}),
        ("Landed Cost Voucher", {"doctype": "Landed Cost Voucher", "docname": "NON-EXISTENT-LCV-99999"}),
        ("Stock Entry", {"doctype": "Stock Entry", "docname": "NON-EXISTENT-STE-99999"}),
    ]
    for desc, payload in non_existent_cases:
        res = post_api(payload)
        passed = (res["status_code"] == 200 and res["body"].get("message", {}).get("success") is True)
        steps = res["body"].get("message", {}).get("steps", [])
        any_completed = any(s.get("completed") for s in steps)
        all_uncompleted = not any_completed
        final_pass = passed and all_uncompleted
        print(f"[{'PASS' if final_pass else 'FAIL'}] Non-existent {desc}: Status {res['status_code']}, All uncompleted: {all_uncompleted}")
        results.append({
            "test": f"1.4 Non-existent {desc}",
            "payload": payload,
            "status": res["status_code"],
            "pass": final_pass,
            "details": res["body"],
        })

    # 1.5 Security / Injection / Malicious Payloads
    security_cases = [
        ("SQLi in doctype", {"doctype": "Purchase Order' OR '1'='1", "docname": "PUR-ORD-2026-00001"}),
        ("SQLi in docname", {"doctype": "Purchase Order", "docname": "' OR '1'='1"}),
        ("SQLi DROP TABLE attempt", {"doctype": "Purchase Order", "docname": "'; DROP TABLE tabItem; --"}),
        ("XSS script injection", {"doctype": "<script>alert('XSS')</script>", "docname": "<img src=x onerror=alert(1)>"}),
        ("Directory Traversal", {"doctype": "Purchase Order", "docname": "../../../../../etc/passwd"}),
        ("Oversized String (5000 chars)", {"doctype": "Purchase Order", "docname": "A" * 5000}),
    ]
    for desc, payload in security_cases:
        res = post_api(payload)
        passed = (res["status_code"] == 200)
        print(f"[{'PASS' if passed else 'FAIL'}] {desc}: Status {res['status_code']}")
        results.append({
            "test": f"1.5 {desc}",
            "payload": payload,
            "status": res["status_code"],
            "pass": passed,
            "details": res["body"],
        })

    # 1.6 Type Confusion Payloads
    type_confusion_cases = [
        ("Dict in doctype", {"doctype": {"$gt": ""}, "docname": "PUR-ORD-2026-00001"}),
        ("List in doctype", {"doctype": ["Purchase Order"], "docname": "PUR-ORD-2026-00001"}),
        ("Dict in docname", {"doctype": "Purchase Order", "docname": {"$ne": None}}),
        ("List in docname", {"doctype": "Purchase Order", "docname": ["PUR-ORD-2026-00001"]}),
        ("Integer values", {"doctype": 12345, "docname": 67890}),
    ]
    for desc, payload in type_confusion_cases:
        res = post_api(payload)
        passed = (res["status_code"] == 200)
        print(f"[{'PASS' if passed else 'FAIL - HTTP ' + str(res['status_code'])}] {desc}: Status {res['status_code']}")
        if not passed and isinstance(res.get("body"), dict):
            print(f"       Exception: {res['body'].get('exception')}")
        results.append({
            "test": f"1.6 {desc}",
            "payload": payload,
            "status": res["status_code"],
            "pass": passed,
            "details": res["body"],
        })

    return results


def run_suite_2():
    print("\n" + "=" * 80)
    print("TEST SUITE 2: TRAVERSAL INTEGRITY, BROKEN LINKS & UNLINKED DOCS")
    print("=" * 80)

    results = []

    # 2.1 Complete Chain Consistency Across All 6 Perspectives
    complete_nodes = [
        ("Step 1 Material Request", "Material Request", "MAT-MR-2026-00001"),
        ("Step 2 Purchase Order", "Purchase Order", "PUR-ORD-2026-00002"),
        ("Step 3 Shipment Tracking", "Shipment Tracking", "0j04glraep"),
        ("Step 4 Purchase Receipt", "Purchase Receipt", "MAT-PRE-2026-00002"),
        ("Step 5 Landed Cost Voucher", "Landed Cost Voucher", "MAT-LCV-2026-00002-2"),
        ("Step 6 Stock Entry", "Stock Entry", "MAT-STE-2026-00002"),
    ]

    expected_complete_docs = {
        "Material Request": "MAT-MR-2026-00001",
        "Purchase Order": "PUR-ORD-2026-00002",
        "Shipment Tracking": "0j04glraep",
        "Purchase Receipt": "MAT-PRE-2026-00002",
        "Landed Cost Voucher": "MAT-LCV-2026-00002-2",
        "Stock Entry": "MAT-STE-2026-00002",
    }

    all_perspectives_match = True
    for label, dt, dn in complete_nodes:
        res = post_api({"doctype": dt, "docname": dn})
        if res["status_code"] != 200:
            print(f"[FAIL] {label}: API failed with {res['status_code']}")
            all_perspectives_match = False
            continue

        steps = res["body"].get("message", {}).get("steps", [])
        resolved_docs = {s["doctype"]: s["docname"] for s in steps}
        completed_flags = {s["doctype"]: s["completed"] for s in steps}
        all_completed = all(completed_flags.values()) and len(completed_flags) == 6
        matches_expected = (resolved_docs == expected_complete_docs)

        passed = all_completed and matches_expected
        if not passed:
            all_perspectives_match = False
        print(f"[{'PASS' if passed else 'FAIL'}] Complete Chain from {label}:")
        print(f"       Resolved: {resolved_docs}")
        print(f"       All 6 Completed: {all_completed} (matches expected: {matches_expected})")
        results.append({
            "test": f"2.1 Complete Chain from {label}",
            "pass": passed,
            "resolved": resolved_docs,
            "all_completed": all_completed,
        })

    # 2.2 Partial Chain Verification (PUR-ORD-2026-00001)
    partial_nodes = [
        ("Step 2 Purchase Order", "Purchase Order", "PUR-ORD-2026-00001"),
        ("Step 3 Shipment Tracking", "Shipment Tracking", "qm8v9o7nc1"),
        ("Step 4 Purchase Receipt", "Purchase Receipt", "MAT-PRE-2026-00001"),
        ("Step 5 Landed Cost Voucher", "Landed Cost Voucher", "MAT-LCV-2026-00001"),
    ]
    for label, dt, dn in partial_nodes:
        res = post_api({"doctype": dt, "docname": dn})
        steps = res["body"].get("message", {}).get("steps", [])
        step_dict = {s["doctype"]: s for s in steps}

        mr_ok = (step_dict["Material Request"]["docname"] is None and step_dict["Material Request"]["completed"] is False)
        po_ok = (step_dict["Purchase Order"]["docname"] == "PUR-ORD-2026-00001" and step_dict["Purchase Order"]["completed"] is True)
        st_ok = (step_dict["Shipment Tracking"]["docname"] == "qm8v9o7nc1" and step_dict["Shipment Tracking"]["completed"] is True)
        pr_ok = (step_dict["Purchase Receipt"]["docname"] == "MAT-PRE-2026-00001" and step_dict["Purchase Receipt"]["completed"] is True)
        lcv_ok = (step_dict["Landed Cost Voucher"]["docname"] == "MAT-LCV-2026-00001" and step_dict["Landed Cost Voucher"]["completed"] is True)
        ste_ok = (step_dict["Stock Entry"]["docname"] is None and step_dict["Stock Entry"]["completed"] is False)

        passed = all([mr_ok, po_ok, st_ok, pr_ok, lcv_ok, ste_ok])
        print(f"[{'PASS' if passed else 'FAIL'}] Partial Chain from {label}: MR=None:{mr_ok}, STE=None:{ste_ok}, Steps 2-5 Completed:{po_ok and st_ok and pr_ok and lcv_ok}")
        results.append({
            "test": f"2.2 Partial Chain from {label}",
            "pass": passed,
            "step_dict": {k: {"docname": v["docname"], "completed": v["completed"]} for k, v in step_dict.items()},
        })

    # 2.3 Cancelled Document Isolation
    res_cancelled = post_api({"doctype": "Landed Cost Voucher", "docname": "MAT-LCV-2026-00002"})
    steps = res_cancelled["body"].get("message", {}).get("steps", [])
    step_dict = {s["doctype"]: s for s in steps}
    lcv_step = step_dict.get("Landed Cost Voucher", {})
    is_cancelled_isolated = (
        lcv_step.get("docstatus") == 2
        and lcv_step.get("completed") is False
        and all(s["docname"] is None for dt, s in step_dict.items() if dt != "Landed Cost Voucher")
    )
    print(f"[{'PASS' if is_cancelled_isolated else 'FAIL'}] Cancelled Doc Isolation (MAT-LCV-2026-00002 docstatus=2): completed={lcv_step.get('completed')}, other docs None={is_cancelled_isolated}")
    results.append({
        "test": "2.3 Cancelled Document Isolation",
        "pass": is_cancelled_isolated,
        "details": step_dict,
    })

    # 2.4 Unlinked / Standalone Documents
    res_unlinked = post_api({"doctype": "Shipment Tracking", "docname": "it6p8uvoc1"})
    steps = res_unlinked["body"].get("message", {}).get("steps", [])
    step_dict = {s["doctype"]: s for s in steps}
    other_unlinked = all(s["docname"] is None for dt, s in step_dict.items() if dt != "Shipment Tracking")
    print(f"[{'PASS' if other_unlinked else 'FAIL'}] Unlinked Standalone Doc (it6p8uvoc1): other steps are None: {other_unlinked}")
    results.append({
        "test": "2.4 Unlinked Standalone Document",
        "pass": other_unlinked,
        "details": step_dict,
    })

    # 2.5 Alternative Branch Resolution (MAT-STE-2026-00001)
    res_alt_ste = post_api({"doctype": "Stock Entry", "docname": "MAT-STE-2026-00001"})
    steps = res_alt_ste["body"].get("message", {}).get("steps", [])
    step_dict = {s["doctype"]: s for s in steps}
    ste_preserved = (
        step_dict.get("Stock Entry", {}).get("docname") == "MAT-STE-2026-00001"
        and step_dict.get("Stock Entry", {}).get("is_current") is True
        and step_dict.get("Purchase Receipt", {}).get("docname") == "MAT-PRE-2026-00002"
    )
    print(f"[{'PASS' if ste_preserved else 'FAIL'}] Alternative Stock Entry (MAT-STE-2026-00001 preserved): {ste_preserved}")
    results.append({
        "test": "2.5 Alternative Stock Entry Branch",
        "pass": ste_preserved,
        "details": step_dict,
    })

    return results


def run_suite_3():
    print("\n" + "=" * 80)
    print("TEST SUITE 3: PERFORMANCE, RAPID REQUESTS & CONCURRENCY")
    print("=" * 80)

    # 3.1 Sequential Performance (100 iterations)
    print("\n--- 3.1 Sequential Performance Benchmark (100 requests) ---")
    sequential_times = []
    errors = 0
    payload = {"doctype": "Purchase Order", "docname": "PUR-ORD-2026-00002"}

    t_start = time.perf_counter()
    for _ in range(100):
        res = post_api(payload)
        if res["status_code"] == 200 and res["body"].get("message", {}).get("success"):
            sequential_times.append(res["elapsed"])
        else:
            errors += 1
    total_sequential_time = time.perf_counter() - t_start

    min_t = min(sequential_times) * 1000
    max_t = max(sequential_times) * 1000
    avg_t = statistics.mean(sequential_times) * 1000
    med_t = statistics.median(sequential_times) * 1000
    p95_t = statistics.quantiles(sequential_times, n=20)[18] * 1000
    p99_t = statistics.quantiles(sequential_times, n=100)[98] * 1000
    throughput = len(sequential_times) / total_sequential_time

    print(f"  Total Requests: 100, Successful: {len(sequential_times)}, Errors: {errors}")
    print(f"  Min Latency:    {min_t:.2f} ms")
    print(f"  Avg Latency:    {avg_t:.2f} ms")
    print(f"  Median Latency: {med_t:.2f} ms")
    print(f"  p95 Latency:    {p95_t:.2f} ms")
    print(f"  p99 Latency:    {p99_t:.2f} ms")
    print(f"  Max Latency:    {max_t:.2f} ms")
    print(f"  Throughput:     {throughput:.2f} req/sec")

    # 3.2 Concurrent Requests Benchmark (20 threads, 100 requests total)
    print("\n--- 3.2 Concurrent Requests Benchmark (20 workers, 100 requests) ---")
    concurrent_times = []
    concurrent_errors = 0

    t_con_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(post_api, payload) for _ in range(100)]
        for f in as_completed(futures):
            res = f.result()
            if res["status_code"] == 200 and res["body"].get("message", {}).get("success"):
                concurrent_times.append(res["elapsed"])
            else:
                concurrent_errors += 1
    total_con_time = time.perf_counter() - t_con_start

    con_avg_t = statistics.mean(concurrent_times) * 1000 if concurrent_times else 0
    con_p95_t = statistics.quantiles(concurrent_times, n=20)[18] * 1000 if len(concurrent_times) >= 20 else 0
    con_throughput = len(concurrent_times) / total_con_time if total_con_time > 0 else 0

    print(f"  Total Requests: 100, Successful: {len(concurrent_times)}, Errors: {concurrent_errors}")
    print(f"  Avg Latency:    {con_avg_t:.2f} ms")
    print(f"  p95 Latency:    {con_p95_t:.2f} ms")
    print(f"  Throughput:     {con_throughput:.2f} req/sec")

    # 3.3 High Concurrency Mixed-Load Stress Test (50 workers, 200 mixed requests)
    print("\n--- 3.3 High-Concurrency Mixed Load (50 workers, 200 mixed requests) ---")
    mixed_payloads = [
        {"doctype": "Purchase Order", "docname": "PUR-ORD-2026-00002"},
        {"doctype": "Purchase Order", "docname": "PUR-ORD-2026-00001"},
        {"doctype": "Material Request", "docname": "MAT-MR-2026-00001"},
        {"doctype": "Purchase Receipt", "docname": "MAT-PRE-2026-00002"},
        {"doctype": "Landed Cost Voucher", "docname": "MAT-LCV-2026-00002-2"},
        {"doctype": "Stock Entry", "docname": "MAT-STE-2026-00002"},
        {"doctype": "Shipment Tracking", "docname": "0j04glraep"},
        {"doctype": "Shipment Tracking", "docname": "it6p8uvoc1"},
        {"doctype": "Purchase Order", "docname": "NON-EXISTENT-PO"},
        {"doctype": "NonExistentDocType", "docname": "TEST"},
        {"doctype": "", "docname": ""},
        {"doctype": None, "docname": None},
    ]

    import random
    stress_payloads = [random.choice(mixed_payloads) for _ in range(200)]
    mixed_success = 0
    mixed_500_errors = 0
    mixed_network_errors = 0

    t_mixed_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(post_api, p) for p in stress_payloads]
        for f in as_completed(futures):
            res = f.result()
            if res["status_code"] == 200:
                mixed_success += 1
            elif res["status_code"] == 500:
                mixed_500_errors += 1
            else:
                mixed_network_errors += 1
    total_mixed_time = time.perf_counter() - t_mixed_start

    print(f"  Mixed 200 requests - 200 OK: {mixed_success}, 500 Errors: {mixed_500_errors}, Network/Other: {mixed_network_errors}")
    print(f"  Throughput: {len(stress_payloads) / total_mixed_time:.2f} req/sec")

    return {
        "sequential": {
            "total": 100,
            "errors": errors,
            "avg_ms": avg_t,
            "median_ms": med_t,
            "p95_ms": p95_t,
            "p99_ms": p99_t,
            "throughput_rps": throughput,
        },
        "concurrent": {
            "total": 100,
            "errors": concurrent_errors,
            "avg_ms": con_avg_t,
            "p95_ms": con_p95_t,
            "throughput_rps": con_throughput,
        },
        "mixed_stress": {
            "total": 200,
            "status_200": mixed_success,
            "status_500": mixed_500_errors,
            "other_errors": mixed_network_errors,
        },
    }


def main():
    print("STARTING EMPIRICAL ADVERSARIAL VERIFICATION HARNESS")
    print(f"Target URL: {API_URL}")
    t0 = time.perf_counter()

    s1 = run_suite_1()
    s2 = run_suite_2()
    s3 = run_suite_3()

    total_time = time.perf_counter() - t0
    print("\n" + "=" * 80)
    print(f"VERIFICATION COMPLETED IN {total_time:.2f}s")
    print("=" * 80)

    # Summary
    s1_fails = [t for t in s1 if not t["pass"]]
    s2_fails = [t for t in s2 if not t["pass"]]

    print(f"\nSuite 1 Summary: {len(s1) - len(s1_fails)}/{len(s1)} passed. {len(s1_fails)} failures.")
    for f in s1_fails:
        print(f"  - {f['test']} -> Status {f['status']}")

    print(f"\nSuite 2 Summary: {len(s2) - len(s2_fails)}/{len(s2)} passed. {len(s2_fails)} failures.")
    for f in s2_fails:
        print(f"  - {f['test']}")

    print(f"\nSuite 3 Summary:")
    print(f"  Sequential p95: {s3['sequential']['p95_ms']:.2f} ms, Throughput: {s3['sequential']['throughput_rps']:.2f} req/s")
    print(f"  Concurrent p95: {s3['concurrent']['p95_ms']:.2f} ms, Throughput: {s3['concurrent']['throughput_rps']:.2f} req/s")
    print(f"  Mixed Stress: 200 OK: {s3['mixed_stress']['status_200']}, 500 Errors: {s3['mixed_stress']['status_500']}")

    report_data = {
        "suite_1": s1,
        "suite_2": s2,
        "suite_3": s3,
    }
    with open("adversarial_test_results.json", "w") as f:
        json.dump(report_data, f, indent=2)
    print("\nDetailed results saved to adversarial_test_results.json")


if __name__ == "__main__":
    main()
