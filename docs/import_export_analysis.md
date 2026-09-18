# Phân tích Quy trình Mua hàng Nhập khẩu & Tích hợp ERPNext

Tài liệu này mô tả chi tiết quy trình mua hàng nhập khẩu 6 bước và cách ánh xạ (mapping) chuẩn xác vào các DocType của hệ thống ERPNext, phục vụ cho việc theo dõi lộ trình và phân bổ chi phí (Landed Cost).

## 1. Yêu cầu mua hàng (Material Request)
- **Nghiệp vụ:** Phòng kinh doanh / kho bãi phát sinh nhu cầu cần nhập khẩu hàng hóa (ví dụ: Laptop XPS-15 từ Dell US).
- **ERPNext DocType:** `Material Request`.
- **Hành động:** Tạo yêu cầu mua hàng với số lượng và mặt hàng cụ thể. Sau khi Submit, trạng thái chuyển sang Pending.

## 2. Tạo Đơn đặt hàng (Purchase Order)
- **Nghiệp vụ:** Dựa trên yêu cầu mua hàng và báo giá (RFQ/Supplier Quotation) đã chốt với nhà cung cấp nước ngoài, phòng Mua hàng tạo hợp đồng / Đơn đặt hàng.
- **ERPNext DocType:** `Purchase Order`.
- **Hành động:** Chọn nhà cung cấp (Dell US), loại tiền tệ (USD), điều khoản thanh toán. Submit PO để chuyển trạng thái sang `To Receive and Bill`.

## 3. Theo dõi Lộ trình Vận chuyển (Shipment Tracking)
- **Nghiệp vụ:** Lô hàng bắt đầu được vận chuyển từ nước ngoài về Việt Nam. Nhân viên Logistics cần theo dõi liên tục trạng thái lô hàng qua các chặng (Booked -> Departed -> Customs Cleared -> Arrived).
- **ERPNext DocType:** `Shipment Tracking`. (Sử dụng child table `Transit Route` để ghi nhận các điểm neo - checkpoints).
- **Điểm nhấn Tích hợp (AfterShip API):** Thay vì nhân viên phải tự nhập tay từng dòng trạng thái, hệ thống sẽ sử dụng API của AfterShip. Dựa trên số Tracking Number của hãng tàu/chuyển phát, hệ thống tự gọi API kéo danh sách checkpoints mới nhất và tự động điền vào bảng `Transit Route`.

## 4. Ghi nhận Hàng đi đường / Nhập kho tạm (Purchase Receipt)
- **Nghiệp vụ:** Ghi nhận quyền sở hữu hàng hóa khi hàng bắt đầu đi trên biển (FOB) hoặc khi hàng vừa cập cảng, đưa vào một kho trung gian (Kho Ảo / Goods In Transit).
- **ERPNext DocType:** `Purchase Receipt`.
- **Hành động:** Tạo phiếu nhận hàng từ Purchase Order. Chọn kho đích là `Goods In Transit` (để ghi nhận tài sản nhưng chưa đưa vào kho bán).

## 5. Phân bổ Chi phí Logistics (Landed Cost Voucher)
- **Nghiệp vụ:** Trong quá trình vận chuyển, phát sinh các chi phí như: Cước tàu biển, phí bảo hiểm, phí lưu kho, thuế nhập khẩu... Các chi phí này cần được cộng dội vào giá vốn của sản phẩm để tính chính xác lợi nhuận.
- **ERPNext DocType:** `Landed Cost Voucher`.
- **Hành động:** Chọn phiếu `Purchase Receipt` vừa tạo. Thêm các khoản phí (Taxes and Charges) và phân bổ theo Số lượng (Qty) hoặc Giá trị (Amount). Sau khi Submit, hệ thống tự động cập nhật lại giá vốn (Valuation Rate) của hàng hóa.

## 6. Luân chuyển Kho thực tế (Stock Entry)
- **Nghiệp vụ:** Hàng hóa sau khi làm thủ tục hải quan xong sẽ được chở từ Cảng (hoặc kho ảo) về kho thực tế của công ty.
- **ERPNext DocType:** `Stock Entry` (Purpose: Material Transfer).
- **Hành động:** Tạo phiếu chuyển hàng từ kho `Goods In Transit` sang kho `Stores`.

---
**Kết luận:** Thông qua quy trình 6 bước này, kết hợp cùng bong bóng điều hướng thông minh (Smart UI Widget) và API Tracking tự động, quy trình nhập khẩu phức tạp đã được số hóa hoàn toàn, minh bạch và chính xác tới từng chi phí nhỏ nhất.
