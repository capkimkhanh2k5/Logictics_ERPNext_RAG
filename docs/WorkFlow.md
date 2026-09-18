### GIAI ĐOẠN 1: THIẾT LẬP DỮ LIỆU NỀN (MASTER DATA)

1. **Tạo Sản phẩm (Item):** Tạo mã hàng `Laptop XPS-15`. (Bật tính năng `Maintain Stock` để cho phép lưu kho).
2. **Tạo Nhà cung cấp (Supplier):** Tạo `Dell US`. Chọn Default Currency là `USD`.
3. **Kiểm tra Kho bãi (Warehouse):** Đảm bảo 3 kho đã sẵn sàng: `Goods In Transit` (Kho ảo), `Cat Lai Port` (Kho cảng), `Stores` (Kho công ty).

### GIAI ĐOẠN 2: CHẠY LUỒNG NGHIỆP VỤ (TRANSACTION FLOW)
5. **Nhu cầu mua sắm:** `Material Request` (Phòng kinh doanh yêu cầu mua 1000 Laptop) -> `Request for Quotation` (Hỏi giá).
6. **Chốt Đơn hàng (Purchase Order):** Chốt đơn với `Dell US` bằng ngoại tệ (USD). Nhập các thông tin đặc thù XNK (ETD, Số tờ khai Hải quan...).
7. **Theo dõi Lộ trình (Shipment Tracking):** Lần lượt cập nhật 8 trạng thái lộ trình (Từ *Booked* cho đến khi *Arrived Destination Port*).
8. **Ghi nhận Hàng đi đường (Purchase Receipt):** Nhập hàng vào kho ảo `Goods In Transit` (Lúc này tàu vừa rời cảng Mỹ).
9. **Phân bổ Giá vốn (Landed Cost Voucher - LCV):** Tạo thủ công LCV từ Purchase Receipt, nhập các chi phí thực tế (Cước biển, phí lưu kho,...) và Submit để hệ thống tự động cộng dội vào giá vốn của Laptop.
10. **Luân chuyển kho vật lý (Stock Entry - Material Transfer):** 
    - Lần 1: Chuyển hàng từ `Goods In Transit` -> `Cat Lai Port`.
    - Lần 2: Chuyển từ `Cat Lai Port` -> Kho `Stores` của công ty.
11. **Báo cáo phân tích (Reporting):** Mở báo cáo SQL `Landed Cost Valuation Analysis` để chứng minh giá vốn đã thay đổi.
12. **Thanh toán (Purchase Invoice -> Payment):** Lên hóa đơn thanh toán bằng tài khoản ngoại tệ (Creditors USD) để hoàn tất vòng đời.