import os
import frappe
from frappe.utils import today, add_days

def ensure_master_setup():
    print(">>> 1. Kiểm tra và thiết lập Company, DocTypes, Kho bãi...")
    company = "Cap Khanh Logistics"

    # 1. Setup Wizard
    if not frappe.db.get_single_value("System Settings", "setup_complete") or not frappe.db.exists("Company", company):
        from erpnext.setup.setup_wizard.setup_wizard import setup_complete
        setup_data = frappe._dict({
            "language": "vi",
            "country": "Vietnam",
            "timezone": "Asia/Ho_Chi_Minh",
            "currency": "VND",
            "full_name": "Cap Kim Khanh",
            "email": "capkimkhanh@gmail.com",
            "company_name": company,
            "company_abbr": "CK",
            "chart_of_accounts": "Standard",
            "fy_start_date": "2026-01-01",
            "fy_end_date": "2026-12-31",
            "bank_account": "Vietcombank",
        })
        setup_complete(setup_data)
        frappe.db.set_single_value("System Settings", "setup_complete", 1)
        frappe.db.set_default("desktop:home_page", "workspace")
        frappe.db.commit()
        print("   ✓ Đã hoàn tất Setup Wizard cho Cap Khanh Logistics")
    for app in frappe.get_all("Installed Application"):
        frappe.db.set_value("Installed Application", app.name, "is_setup_complete", 1)
    frappe.db.set_single_value("System Settings", "setup_complete", 1)
    frappe.db.set_single_value("System Settings", "allow_login_using_user_name", 1)
    frappe.db.set_default("desktop:home_page", "workspace")

    from frappe.utils.password import update_password

    # Configure Administrator username 'admin' and password 'admin'
    admin = frappe.get_doc("User", "Administrator")
    admin.username = "admin"
    admin.save(ignore_permissions=True)
    update_password("Administrator", "admin")

    # Configure user capkimkhanh@gmail.com
    user_email = "capkimkhanh@gmail.com"
    if not frappe.db.exists("User", user_email):
        user = frappe.get_doc({
            "doctype": "User",
            "email": user_email,
            "first_name": "Cap Kim Khanh",
            "enabled": 1,
            "send_welcome_email": 0,
            "user_type": "System User"
        })
        user.insert(ignore_permissions=True)
    else:
        user = frappe.get_doc("User", user_email)
        user.enabled = 1
        user.save(ignore_permissions=True)

    user.add_roles(
        "System Manager",
        "Purchase Manager",
        "Purchase User",
        "Stock Manager",
        "Stock User",
        "Accounts Manager",
        "Accounts User"
    )
    update_password(user_email, "admin")
    frappe.db.commit()

    # 2. Module Def
    if not frappe.db.exists("Module Def", "Logistics Wizard"):
        frappe.get_doc({
            "doctype": "Module Def",
            "module_name": "Logistics Wizard",
            "app_name": "logistics_wizard",
            "custom": 0
        }).insert(ignore_permissions=True)
        frappe.db.commit()

    # 3. Child DocType Transit Route
    if not frappe.db.exists("DocType", "Transit Route"):
        dt_tr = frappe.get_doc({
            "doctype": "DocType",
            "name": "Transit Route",
            "module": "Logistics Wizard",
            "custom": 1,
            "istable": 1,
            "editable_grid": 1,
            "fields": [
                {"fieldname": "activity", "fieldtype": "Data", "label": "Activity / Trạng thái", "in_list_view": 1, "reqd": 1},
                {"fieldname": "location", "fieldtype": "Data", "label": "Location / Địa điểm", "in_list_view": 1, "reqd": 1},
                {"fieldname": "date", "fieldtype": "Date", "label": "Date / Ngày", "in_list_view": 1},
                {"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes / Ghi chú"}
            ]
        })
        dt_tr.insert(ignore_permissions=True)
        frappe.db.commit()

    # 4. Master DocType Shipment Tracking
    if not frappe.db.exists("DocType", "Shipment Tracking"):
        dt_st = frappe.get_doc({
            "doctype": "DocType",
            "name": "Shipment Tracking",
            "module": "Logistics Wizard",
            "custom": 1,
            "is_submittable": 0,
            "track_changes": 1,
            "autoname": "Prompt",
            "naming_rule": "Set by user",
            "permissions": [
                {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
                {"role": "Stock User", "read": 1, "write": 1, "create": 1},
                {"role": "Purchase User", "read": 1, "write": 1, "create": 1}
            ],
            "fields": [
                {"fieldname": "section_details", "fieldtype": "Section Break", "label": "Thông tin Vận đơn (Shipment Details)"},
                {"fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "label": "Purchase Order / Đơn mua hàng", "in_list_view": 1, "reqd": 1},
                {"fieldname": "purchase_receipt", "fieldtype": "Link", "options": "Purchase Receipt", "label": "Purchase Receipt / Phiếu nhận hàng"},
                {"fieldname": "shipping_method", "fieldtype": "Select", "options": "Air\nOcean\nRoad", "label": "Phương thức vận chuyển (Method)", "in_list_view": 1, "default": "Ocean", "reqd": 1},
                {"fieldname": "carrier", "fieldtype": "Data", "label": "Hãng vận chuyển (Carrier)", "in_list_view": 1},
                {"fieldname": "col_break_1", "fieldtype": "Column Break"},
                {"fieldname": "tracking_number", "fieldtype": "Data", "label": "Mã vận đơn (Tracking Number)", "in_list_view": 1},
                {"fieldname": "status", "fieldtype": "Select", "options": "Draft\nIn Transit\nCustoms Clearance\nCompleted\nCancelled", "label": "Trạng thái vận đơn", "default": "Draft", "in_list_view": 1},
                {"fieldname": "etd", "fieldtype": "Date", "label": "Ngày khởi hành dự kiến (ETD)"},
                {"fieldname": "eta", "fieldtype": "Date", "label": "Ngày đến dự kiến (ETA)"},
                {"fieldname": "section_route", "fieldtype": "Section Break", "label": "Hành trình vận chuyển (Transit Route)"},
                {"fieldname": "origin_port", "fieldtype": "Data", "label": "Cảng/Sân bay xuất phát (Origin)"},
                {"fieldname": "col_break_2", "fieldtype": "Column Break"},
                {"fieldname": "destination_port", "fieldtype": "Data", "label": "Cảng/Sân bay đến (Destination)"},
                {"fieldname": "section_checkpoints", "fieldtype": "Section Break", "label": "Các trạm lộ trình (Checkpoints)"},
                {"fieldname": "transit_route", "fieldtype": "Table", "options": "Transit Route", "label": "Lộ trình chi tiết"}
            ]
        })
        dt_st.insert(ignore_permissions=True)
        frappe.db.commit()

    # 5. Custom Fields on Purchase Order
    po_custom_fields = [
        {"dt": "Purchase Order", "fieldname": "etd", "label": "Ngày khởi hành dự kiến (ETD)", "fieldtype": "Date", "insert_after": "schedule_date"},
        {"dt": "Purchase Order", "fieldname": "customs_declaration_number", "label": "Số tờ khai hải quan", "fieldtype": "Data", "insert_after": "etd"},
        {"dt": "Purchase Order", "fieldname": "shipping_method", "label": "Phương thức vận chuyển", "fieldtype": "Select", "options": "Air\nOcean\nRoad", "insert_after": "customs_declaration_number"}
    ]
    for cf_data in po_custom_fields:
        cf_name = f"{cf_data['dt']}-{cf_data['fieldname']}"
        if not frappe.db.exists("Custom Field", cf_name):
            frappe.get_doc({"doctype": "Custom Field", **cf_data}).insert(ignore_permissions=True)

    # 6. Warehouses
    all_wh = frappe.db.get_value("Warehouse", {"warehouse_name": "All Warehouses", "company": company}, "name")
    warehouses_to_create = ["Cat Lai Port", "Hai Phong Port", "Tan Son Nhat Airport"]
    for wh_name in warehouses_to_create:
        full_wh = f"{wh_name} - CK"
        if not frappe.db.exists("Warehouse", full_wh):
            frappe.get_doc({
                "doctype": "Warehouse",
                "warehouse_name": wh_name,
                "company": company,
                "parent_warehouse": all_wh,
                "is_group": 0
            }).insert(ignore_permissions=True)

    # 7. Currency & Exchange Rate
    if frappe.db.exists("Currency", "USD"):
        frappe.db.set_value("Currency", "USD", "enabled", 1)
    if not frappe.db.exists("Currency Exchange", {"from_currency": "USD", "to_currency": "VND", "date": "2026-09-19"}):
        frappe.get_doc({
            "doctype": "Currency Exchange",
            "date": "2026-09-19",
            "from_currency": "USD",
            "to_currency": "VND",
            "exchange_rate": 25400.0,
            "for_buying": 1,
            "for_selling": 1
        }).insert(ignore_permissions=True)

    # 8. Accounts
    current_liabilities = frappe.db.get_value("Account", {"account_name": "Current Liabilities", "company": company}, "name")
    bank_accounts = frappe.db.get_value("Account", {"account_name": "Bank Accounts", "company": company}, "name")
    if not frappe.db.exists("Account", "Creditors USD - CK"):
        frappe.get_doc({
            "doctype": "Account",
            "account_name": "Creditors USD",
            "company": company,
            "parent_account": current_liabilities,
            "account_type": "Payable",
            "account_currency": "USD"
        }).insert(ignore_permissions=True)
    if not frappe.db.exists("Account", "USD Bank Account - CK"):
        frappe.get_doc({
            "doctype": "Account",
            "account_name": "USD Bank Account",
            "company": company,
            "parent_account": bank_accounts,
            "account_type": "Bank",
            "account_currency": "USD"
        }).insert(ignore_permissions=True)

    # 9. Opening Balance
    temp_opening = frappe.db.get_value("Account", {"account_name": "Temporary Opening", "company": company}, "name")
    if not frappe.db.exists("Journal Entry", {"voucher_type": "Opening Entry", "company": company}):
        jv = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Opening Entry",
            "company": company,
            "posting_date": "2026-01-01",
            "multi_currency": 1,
            "accounts": [
                {"account": "USD Bank Account - CK", "account_currency": "USD", "debit_in_account_currency": 5000000.0, "exchange_rate": 25400.0, "cost_center": "Main - CK"},
                {"account": temp_opening, "account_currency": "VND", "credit_in_account_currency": 5000000.0 * 25400.0, "exchange_rate": 1.0, "cost_center": "Main - CK"}
            ]
        })
        jv.insert(ignore_permissions=True)
        jv.submit()

    # 10. Supplier Apple Inc.
    supplier = "Apple Inc."
    if not frappe.db.exists("Supplier", supplier):
        frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": supplier,
            "supplier_group": "All Supplier Groups",
            "default_currency": "USD",
            "country": "United States",
            "accounts": [{"company": company, "account": "Creditors USD - CK"}]
        }).insert(ignore_permissions=True)

    # 11. Addresses
    if not frappe.db.exists("Address", "Apple Park Headquarters-Billing"):
        frappe.get_doc({
            "doctype": "Address",
            "address_title": "Apple Park Headquarters",
            "address_type": "Billing",
            "address_line1": "1 Apple Park Way",
            "city": "Cupertino",
            "state": "California",
            "country": "United States",
            "pincode": "95014",
            "is_primary_address": 1,
            "links": [{"link_doctype": "Supplier", "link_name": supplier}]
        }).insert(ignore_permissions=True)

    if not frappe.db.exists("Address", "Cap Khanh Logistics Warehouse-Shipping"):
        frappe.get_doc({
            "doctype": "Address",
            "address_title": "Cap Khanh Logistics Warehouse",
            "address_type": "Shipping",
            "address_line1": "Khu Cong Nghe Cao, Duong D1, Quan 9",
            "city": "Ho Chi Minh City",
            "country": "Vietnam",
            "pincode": "700000",
            "is_primary_address": 1,
            "is_your_company_address": 1,
            "is_shipping_address": 1,
            "links": [{"link_doctype": "Company", "link_name": company}]
        }).insert(ignore_permissions=True)

    # 12. Items
    items_data = [
        {"item_code": "IPHONE-16-PROMAX", "item_name": "Apple iPhone 16 Pro Max 256GB Desert Titanium", "item_group": "Products", "stock_uom": "Nos", "standard_rate": 34990000.0, "description": "Flagship iPhone 16 Pro Max 256GB Titan sa mac"},
        {"item_code": "MACBOOK-PRO-M3", "item_name": "Apple MacBook Pro 14\" M3 Pro 18GB/512GB Space Black", "item_group": "Products", "stock_uom": "Nos", "standard_rate": 49990000.0, "description": "Laptop Apple MacBook Pro 14 inch chip M3 Pro"},
        {"item_code": "IPAD-PRO-M4", "item_name": "Apple iPad Pro 11\" M4 Ultra Retina Tandem OLED 256GB", "item_group": "Products", "stock_uom": "Nos", "standard_rate": 28990000.0, "description": "May tinh bang Apple iPad Pro 11 inch chip M4"},
        {"item_code": "AIRPODS-PRO-2", "item_name": "Apple AirPods Pro 2 MagSafe USB-C (2nd Gen)", "item_group": "Products", "stock_uom": "Nos", "standard_rate": 6190000.0, "description": "Tai nghe True Wireless Apple AirPods Pro 2 USB-C"}
    ]
    for itm in items_data:
        if not frappe.db.exists("Item", itm["item_code"]):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": itm["item_code"],
                "item_name": itm["item_name"],
                "item_group": itm["item_group"],
                "stock_uom": itm["stock_uom"],
                "is_stock_item": 1,
                "valuation_method": "FIFO",
                "standard_rate": itm["standard_rate"],
                "description": itm["description"],
                "default_warehouse": "Stores - CK"
            }).insert(ignore_permissions=True)

    frappe.db.commit()
    print("   ✓ Master Data & System Setup hoàn tất 100%!")


def run():
    frappe.set_user("Administrator")
    ensure_master_setup()

    from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt, make_purchase_invoice

    company = "Cap Khanh Logistics"
    supplier = "Apple Inc."
    exchange_rate = 25400.0

    print("\n=== BẮT ĐẦU TẠO DỮ LIỆU ĐƠN HÀNG XUẤT NHẬP KHẨU THỰC TẾ ===")

    # Dọn dẹp giao dịch cũ nếu đã có để chạy lại mượt mà
    for dt in ["Payment Entry", "Purchase Invoice", "Stock Entry", "Landed Cost Voucher", "Purchase Receipt", "Shipment Tracking", "Purchase Order", "Material Request"]:
        records = frappe.get_all(dt, filters={"docstatus": ["in", [0, 1]]}, fields=["name", "docstatus"])
        for r in records:
            try:
                doc = frappe.get_doc(dt, r.name)
                if doc.docstatus == 1:
                    doc.cancel()
                doc.delete()
            except Exception as e:
                pass
    frappe.db.commit()

    # -------------------------------------------------------------
    # KỊCH BẢN 1: ĐƠN HÀNG ĐƯỜNG BIỂN (OCEAN) - HOÀN THÀNH & TẤT TOÁN 100%
    # -------------------------------------------------------------
    print("\n1. Tạo Đơn hàng 1 (OCEAN) - Hoàn thành, Landed Cost đầy đủ, Đã Nhập kho, Đã Thanh toán:")
    
    mr1 = frappe.get_doc({
        "doctype": "Material Request",
        "material_request_type": "Purchase",
        "company": company,
        "transaction_date": "2026-08-10",
        "schedule_date": "2026-09-15",
        "items": [
            {"item_code": "IPHONE-16-PROMAX", "qty": 500, "schedule_date": "2026-09-15", "warehouse": "Goods In Transit - CK", "description": "Apple iPhone 16 Pro Max 256GB (Lô hàng đường biển)"},
            {"item_code": "MACBOOK-PRO-M3", "qty": 200, "schedule_date": "2026-09-15", "warehouse": "Goods In Transit - CK", "description": "Apple MacBook Pro 14 inch M3 Pro (Lô hàng đường biển)"}
        ]
    })
    mr1.insert(ignore_permissions=True)
    mr1.submit()
    print(f"   ✓ Material Request: {mr1.name}")

    po1 = frappe.get_doc({
        "doctype": "Purchase Order",
        "company": company,
        "supplier": supplier,
        "currency": "USD",
        "conversion_rate": exchange_rate,
        "buying_price_list": "Standard Buying",
        "transaction_date": "2026-08-12",
        "schedule_date": "2026-09-15",
        "shipping_method": "Ocean",
        "etd": "2026-08-15",
        "customs_declaration_number": "HQ-2026-APL-SEA01",
        "supplier_address": "Apple Park Headquarters-Billing",
        "shipping_address": "Cap Khanh Logistics Warehouse-Shipping",
        "items": [
            {"item_code": "IPHONE-16-PROMAX", "qty": 500, "rate": 1100.0, "material_request": mr1.name, "material_request_item": mr1.items[0].name, "schedule_date": "2026-09-15", "warehouse": "Goods In Transit - CK"},
            {"item_code": "MACBOOK-PRO-M3", "qty": 200, "rate": 1800.0, "material_request": mr1.name, "material_request_item": mr1.items[1].name, "schedule_date": "2026-09-15", "warehouse": "Goods In Transit - CK"}
        ]
    })
    po1.insert(ignore_permissions=True)
    po1.submit()
    print(f"   ✓ Purchase Order: {po1.name} (Tổng: ${po1.grand_total:,.2f} USD)")

    st1 = frappe.get_doc({
        "doctype": "Shipment Tracking",
        "name": "ST-2026-00001",
        "purchase_order": po1.name,
        "shipping_method": "Ocean",
        "carrier": "Maersk Line (Vessel: Maersk Mc-Kinney Moller)",
        "tracking_number": "MSK-USVN-882201",
        "origin_port": "Port of Long Beach",
        "destination_port": "Cat Lai Port, Ho Chi Minh",
        "etd": "2026-08-15",
        "eta": "2026-09-14",
        "status": "Completed",
        "transit_route": [
            {"activity": "Booked & Container Loaded", "location": "Apple Park, Cupertino", "date": "2026-08-12", "notes": "Hàng đóng container tại nhà máy Apple California"},
            {"activity": "Export Customs Cleared & Loaded on Vessel", "location": "Port of Long Beach", "date": "2026-08-15", "notes": "Thông quan xuất khẩu Mỹ, bốc lên tàu Maersk"},
            {"activity": "Mid-Pacific Ocean Transit", "location": "Hawaii Transit Hub", "date": "2026-08-23", "notes": "Tàu hành trình qua vùng biển Hawaii"},
            {"activity": "Cruising Western Pacific Corridor", "location": "Guam Maritime Corridor", "date": "2026-09-02", "notes": "Hành trình biển Tây Thái Bình Dương"},
            {"activity": "Entering Vietnam Territorial Waters", "location": "East Sea", "date": "2026-09-10", "notes": "Tàu vào vùng biển Việt Nam"},
            {"activity": "Vessel Berthed & Discharged at Terminal", "location": "Cat Lai Port, Ho Chi Minh", "date": "2026-09-14", "notes": "Tàu cập cảng Cát Lái, dỡ container xuống bãi"},
            {"activity": "Import Customs Cleared & Final Delivery to Stores", "location": "Stores - CK", "date": "2026-09-16", "notes": "Hoàn tất thủ tục hải quan và nhập kho tổng"}
        ]
    })
    st1.insert(ignore_permissions=True)
    print(f"   ✓ Shipment Tracking: {st1.name} (7 trạm hải trình)")

    pr1 = make_purchase_receipt(po1.name)
    pr1.posting_date = "2026-09-14"
    for item in pr1.items:
        item.warehouse = "Goods In Transit - CK"
    pr1.insert(ignore_permissions=True)
    pr1.submit()
    st1.purchase_receipt = pr1.name
    st1.save(ignore_permissions=True)
    print(f"   ✓ Purchase Receipt: {pr1.name} (Nhập kho tạm 'Goods In Transit - CK')")

    lcv1 = frappe.get_doc({
        "doctype": "Landed Cost Voucher",
        "company": company,
        "distribute_charges_based_on": "Qty",
        "posting_date": "2026-09-15",
        "purchase_receipts": [{"receipt_document_type": "Purchase Receipt", "receipt_document": pr1.name}],
        "taxes": [
            {"expense_account": "Expenses Included In Valuation - CK", "description": "Cước tàu biển quốc tế (Ocean Freight: Long Beach -> Cat Lai)", "amount": 120000000.0},
            {"expense_account": "Expenses Included In Valuation - CK", "description": "Thuế nhập khẩu & Lệ phí hải quan (Customs Import Duty & Clearance)", "amount": 350000000.0},
            {"expense_account": "Expenses Included In Valuation - CK", "description": "Phí nâng hạ bốc dỡ cảng biển (Terminal Handling Charges - THC)", "amount": 45000000.0},
            {"expense_account": "Expenses Included In Valuation - CK", "description": "Phí lưu kho bãi & vận chuyển nội địa (Demurrage & Drayage)", "amount": 25000000.0}
        ]
    })
    lcv1.insert(ignore_permissions=True)
    lcv1.get_items_from_purchase_receipts()
    lcv1.submit()
    print(f"   ✓ Landed Cost Voucher: {lcv1.name} (Phân bổ tổng cộng: 540,000,000 VND vào Giá vốn)")

    ste1 = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Transfer",
        "company": company,
        "posting_date": "2026-09-15",
        "from_warehouse": "Goods In Transit - CK",
        "to_warehouse": "Cat Lai Port - CK",
        "purchase_receipt_no": pr1.name,
        "items": [
            {"item_code": "IPHONE-16-PROMAX", "qty": 500, "s_warehouse": "Goods In Transit - CK", "t_warehouse": "Cat Lai Port - CK", "reference_purchase_receipt": pr1.name},
            {"item_code": "MACBOOK-PRO-M3", "qty": 200, "s_warehouse": "Goods In Transit - CK", "t_warehouse": "Cat Lai Port - CK", "reference_purchase_receipt": pr1.name}
        ]
    })
    ste1.insert(ignore_permissions=True)
    ste1.submit()
    print(f"   ✓ Stock Entry 1: {ste1.name} (Goods In Transit -> Cat Lai Port)")

    ste2 = frappe.get_doc({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Transfer",
        "company": company,
        "posting_date": "2026-09-16",
        "from_warehouse": "Cat Lai Port - CK",
        "to_warehouse": "Stores - CK",
        "purchase_receipt_no": pr1.name,
        "items": [
            {"item_code": "IPHONE-16-PROMAX", "qty": 500, "s_warehouse": "Cat Lai Port - CK", "t_warehouse": "Stores - CK", "reference_purchase_receipt": pr1.name},
            {"item_code": "MACBOOK-PRO-M3", "qty": 200, "s_warehouse": "Cat Lai Port - CK", "t_warehouse": "Stores - CK", "reference_purchase_receipt": pr1.name}
        ]
    })
    ste2.insert(ignore_permissions=True)
    ste2.submit()
    print(f"   ✓ Stock Entry 2: {ste2.name} (Cat Lai Port -> Stores - CK)")

    pinv1 = make_purchase_invoice(po1.name)
    pinv1.posting_date = "2026-09-16"
    pinv1.bill_no = "APL-INV-2026-08891"
    pinv1.bill_date = "2026-09-14"
    pinv1.credit_to = "Creditors USD - CK"
    pinv1.insert(ignore_permissions=True)
    pinv1.submit()
    print(f"   ✓ Purchase Invoice: {pinv1.name} (Tổng hóa đơn: ${pinv1.grand_total:,.2f} USD)")

    pe1 = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Pay",
        "company": company,
        "party_type": "Supplier",
        "party": supplier,
        "paid_from": "USD Bank Account - CK",
        "paid_to": "Creditors USD - CK",
        "paid_from_account_currency": "USD",
        "paid_to_account_currency": "USD",
        "paid_amount": pinv1.grand_total,
        "received_amount": pinv1.grand_total,
        "source_exchange_rate": exchange_rate,
        "target_exchange_rate": exchange_rate,
        "reference_no": "WIRE-VCB-USD-99221",
        "reference_date": "2026-09-16",
        "posting_date": "2026-09-16",
        "references": [{"reference_doctype": "Purchase Invoice", "reference_name": pinv1.name, "total_amount": pinv1.grand_total, "outstanding_amount": pinv1.grand_total, "allocated_amount": pinv1.grand_total}]
    })
    pe1.insert(ignore_permissions=True)
    pe1.submit()
    print(f"   ✓ Payment Entry: {pe1.name} (Đã thanh toán tất toán: ${pe1.paid_amount:,.2f} USD cho Apple Inc.)")


    # -------------------------------------------------------------
    # KỊCH BẢN 2: ĐƠN HÀNG ĐƯỜNG HÀNG KHÔNG (AIR) - IN TRANSIT
    # -------------------------------------------------------------
    print("\n2. Tạo Đơn hàng 2 (AIR) - Đang bay qua Thái Bình Dương (In Transit):")

    mr2 = frappe.get_doc({
        "doctype": "Material Request",
        "material_request_type": "Purchase",
        "company": company,
        "transaction_date": "2026-09-16",
        "schedule_date": "2026-09-22",
        "items": [
            {"item_code": "IPAD-PRO-M4", "qty": 300, "schedule_date": "2026-09-22", "warehouse": "Goods In Transit - CK", "description": "Apple iPad Pro 11 inch M4 OLED (Hàng giao gấp bằng máy bay)"},
            {"item_code": "AIRPODS-PRO-2", "qty": 500, "schedule_date": "2026-09-22", "warehouse": "Goods In Transit - CK", "description": "Apple AirPods Pro 2 USB-C (Hàng giao gấp bằng máy bay)"}
        ]
    })
    mr2.insert(ignore_permissions=True)
    mr2.submit()
    print(f"   ✓ Material Request: {mr2.name}")

    po2 = frappe.get_doc({
        "doctype": "Purchase Order",
        "company": company,
        "supplier": supplier,
        "currency": "USD",
        "conversion_rate": exchange_rate,
        "buying_price_list": "Standard Buying",
        "transaction_date": "2026-09-17",
        "schedule_date": "2026-09-22",
        "shipping_method": "Air",
        "etd": "2026-09-18",
        "customs_declaration_number": "HQ-2026-APL-AIR02",
        "supplier_address": "Apple Park Headquarters-Billing",
        "shipping_address": "Cap Khanh Logistics Warehouse-Shipping",
        "items": [
            {"item_code": "IPAD-PRO-M4", "qty": 300, "rate": 950.0, "material_request": mr2.name, "material_request_item": mr2.items[0].name, "schedule_date": "2026-09-22", "warehouse": "Goods In Transit - CK"},
            {"item_code": "AIRPODS-PRO-2", "qty": 500, "rate": 220.0, "material_request": mr2.name, "material_request_item": mr2.items[1].name, "schedule_date": "2026-09-22", "warehouse": "Goods In Transit - CK"}
        ]
    })
    po2.insert(ignore_permissions=True)
    po2.submit()
    print(f"   ✓ Purchase Order: {po2.name} (Tổng: ${po2.grand_total:,.2f} USD - Status: {po2.status})")

    st2 = frappe.get_doc({
        "doctype": "Shipment Tracking",
        "name": "ST-2026-00002",
        "purchase_order": po2.name,
        "shipping_method": "Air",
        "carrier": "Vietnam Airlines Cargo (Flight: VN-CARGO-991)",
        "tracking_number": "VN-AIR-774402",
        "origin_port": "San Francisco Airport",
        "destination_port": "Tan Son Nhat Airport",
        "etd": "2026-09-18",
        "eta": "2026-09-21",
        "status": "In Transit",
        "transit_route": [
            {"activity": "Picked up from Apple Logistics Facility", "location": "Apple Park, Cupertino", "date": "2026-09-17", "notes": "Hàng xuất từ trung tâm phân phối Apple"},
            {"activity": "Air Cargo Screened & Customs Export Cleared", "location": "San Francisco Airport", "date": "2026-09-18", "notes": "An ninh soi chiếu hàng không và thông quan tại SFO"},
            {"activity": "Flight Departed SFO Corridor", "location": "Pacific Flight Corridor", "date": "2026-09-18", "notes": "Chuyến bay cất cánh bay vào hành lang Thái Bình Dương"},
            {"activity": "In-Flight Trans-Pacific Airspace (Current Position)", "location": "Tokyo Narita Airspace", "date": "2026-09-19", "notes": "Máy bay đang trên không phận quốc tế hướng về Việt Nam"}
        ]
    })
    st2.insert(ignore_permissions=True)
    print(f"   ✓ Shipment Tracking: {st2.name} (Đang bay qua Tokyo Narita Airspace về SGN)")


    # -------------------------------------------------------------
    # KỊCH BẢN 3: ĐƠN HÀNG ĐƯỜNG BIỂN (OCEAN) - IN TRANSIT VỀ HẢI PHÒNG
    # -------------------------------------------------------------
    print("\n3. Tạo Đơn hàng 3 (OCEAN) - Đang trên biển về Cảng Hải Phòng (In Transit):")

    po3 = frappe.get_doc({
        "doctype": "Purchase Order",
        "company": company,
        "supplier": supplier,
        "currency": "USD",
        "conversion_rate": exchange_rate,
        "buying_price_list": "Standard Buying",
        "transaction_date": "2026-09-08",
        "schedule_date": "2026-09-28",
        "shipping_method": "Ocean",
        "etd": "2026-09-10",
        "customs_declaration_number": "HQ-2026-APL-SEA03",
        "supplier_address": "Apple Park Headquarters-Billing",
        "shipping_address": "Cap Khanh Logistics Warehouse-Shipping",
        "items": [
            {"item_code": "IPHONE-16-PROMAX", "qty": 400, "rate": 1100.0, "schedule_date": "2026-09-28", "warehouse": "Goods In Transit - CK"}
        ]
    })
    po3.insert(ignore_permissions=True)
    po3.submit()
    print(f"   ✓ Purchase Order: {po3.name} (Tổng: ${po3.grand_total:,.2f} USD)")

    st3 = frappe.get_doc({
        "doctype": "Shipment Tracking",
        "name": "ST-2026-00003",
        "purchase_order": po3.name,
        "shipping_method": "Ocean",
        "carrier": "ONE Line (Ocean Network Express)",
        "tracking_number": "ONE-USVN-339901",
        "origin_port": "Port of Oakland",
        "destination_port": "Hai Phong Port",
        "etd": "2026-09-10",
        "eta": "2026-09-28",
        "status": "In Transit",
        "transit_route": [
            {"activity": "Container Loaded & Sealed", "location": "Apple Warehouse, Cupertino", "date": "2026-09-08", "notes": "Đóng seal container 40ft"},
            {"activity": "Vessel Departed Port of Oakland", "location": "Port of Oakland", "date": "2026-09-10", "notes": "Tàu ONE xuất phát từ cảng Oakland, California"},
            {"activity": "Mid-Pacific Sea Lane Navigation", "location": "Hawaii Transit Hub", "date": "2026-09-15", "notes": "Vượt Thái Bình Dương"},
            {"activity": "Cruising Western Pacific Sea Lane (Current Position)", "location": "Guam Maritime Corridor", "date": "2026-09-19", "notes": "Vị trí tàu hiện tại: Hành lang hàng hải Guam"}
        ]
    })
    st3.insert(ignore_permissions=True)
    print(f"   ✓ Shipment Tracking: {st3.name} (Tàu đang tại Guam Maritime Corridor về Hải Phòng)")


    # -------------------------------------------------------------
    # KỊCH BẢN 4: ĐƠN HÀNG NHÁP (DRAFT) - ĐANG SOẠN THẢO / CHỜ DUYỆT
    # -------------------------------------------------------------
    print("\n4. Tạo Đơn hàng 4 (AIR) - Bản nháp (Draft) để kiểm thử thao tác phê duyệt:")

    mr4 = frappe.get_doc({
        "doctype": "Material Request",
        "material_request_type": "Purchase",
        "company": company,
        "transaction_date": today(),
        "schedule_date": add_days(today(), 10),
        "items": [
            {"item_code": "MACBOOK-PRO-M3", "qty": 100, "schedule_date": add_days(today(), 10), "warehouse": "Stores - CK", "description": "Dự thảo yêu cầu mua thêm 100 MacBook Pro M3 cho quý IV"}
        ]
    })
    mr4.insert(ignore_permissions=True)
    print(f"   ✓ Material Request (Draft): {mr4.name}")

    po4 = frappe.get_doc({
        "doctype": "Purchase Order",
        "company": company,
        "supplier": supplier,
        "currency": "USD",
        "conversion_rate": exchange_rate,
        "buying_price_list": "Standard Buying",
        "transaction_date": today(),
        "schedule_date": add_days(today(), 10),
        "shipping_method": "Air",
        "etd": add_days(today(), 3),
        "customs_declaration_number": "HQ-2026-APL-DRAFT04",
        "supplier_address": "Apple Park Headquarters-Billing",
        "shipping_address": "Cap Khanh Logistics Warehouse-Shipping",
        "items": [
            {"item_code": "MACBOOK-PRO-M3", "qty": 100, "rate": 1800.0, "material_request": mr4.name, "material_request_item": mr4.items[0].name, "schedule_date": add_days(today(), 10), "warehouse": "Goods In Transit - CK"}
        ]
    })
    po4.insert(ignore_permissions=True)
    print(f"   ✓ Purchase Order (Draft): {po4.name} (Chưa submit, dùng để demo thao tác duyệt)")

    frappe.db.commit()
    print("\n🎉 HOÀN THÀNH TẠO 4 BỘ ĐƠN HÀNG XUẤT NHẬP KHẨU VÀ LUỒNG PROCUREMENT ĐẦY ĐỦ!")

if __name__ == "__main__":
    import os, sys
    sites_dir = "/home/frappe/frappe-bench/sites"
    if os.path.exists(sites_dir):
        os.chdir(sites_dir)
    elif os.path.exists("sites"):
        os.chdir("sites")
    frappe.init(site="logistics.local")
    frappe.connect()
    run()
