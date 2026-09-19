# KỊCH BẢN DEMO SIÊU CHI TIẾT (STEP-BY-STEP): QUẢN TRỊ MUA HÀNG & LANDED COST

Kịch bản này được thiết kế theo dạng "Cầm tay chỉ việc", hướng dẫn bạn click vào đâu, gõ cái gì, và chọn nút nào. Rất phù hợp nếu bạn chưa quen thao tác trên ERPNext.

---

## PHẦN 1: KHỞI TẠO ĐƠN MUA HÀNG QUỐC TẾ (PROCUREMENT FLOW)

**1. Tạo Yêu cầu mua hàng (Material Request)**
- Đưa chuột lên thanh tìm kiếm trên cùng (Awesomebar), gõ chữ `Material Request` -> Click vào dòng **Material Request List**.
- Nhìn góc trên cùng bên phải, click nút màu xanh **Add Material Request**.
- Giao diện mới hiện ra:
  - Ô `Date`: Cứ để mặc định là ngày hôm nay.
  - Ô `Type`: Bấm vào, chọn **Purchase**.
- Cuộn chuột xuống một chút tìm bảng có tên **Items**, click vào nút **Add Row**:
  - Ở cột `Item Code`: Nhập chữ `Laptop XPS-15` và chọn nó.
  - Ở cột `Quantity`: Gõ số `1000`.
- Cuộn chuột ngược lên trên cùng, bấm nút **Save** ở góc phải.
- Đợi 1 giây, nút Save sẽ biến thành nút **Submit** màu xanh, click **Submit** -> Hệ thống hỏi xác nhận, click **Yes**.

**2. Tạo Yêu cầu báo giá (Request for Quotation - RFQ)**
- Ngay tại màn hình Material Request mà bạn vừa Submit xong.
- Nhìn lên góc trên bên phải, click vào nút **Create** (nút màu xám) -> Chọn **Request for Quotation**.
- Màn hình RFQ hiện ra, cuộn xuống tìm bảng **Suppliers**, click nút **Add Row**:
  - Tại ô `Supplier`: Gõ chữ `Dell US` và click chọn nó.
- Cuộn lên trên cùng, bấm nút **Save** -> Bấm tiếp nút **Submit** màu xanh -> Click **Yes**.

**3. Tạo Đơn đặt hàng (Purchase Order)**
- Ngay tại màn hình RFQ mà bạn vừa Submit xong.
- Nhìn lên góc trên bên phải, click vào nút **Create** -> Chọn **Purchase Order**.
- Màn hình Purchase Order (PO) hiện ra. Chúng ta cần điền thông tin XNK:
  - Cuộn xuống tìm trường `ETD` (Ngày khởi hành dự kiến): Click vào biểu tượng lịch, chọn một ngày trong tuần sau.
  - Tìm trường `Customs Declaration Number` (Số tờ khai hải quan): Click vào và gõ mã số ví dụ: `HQ-2026-112233`.
- Cuộn xuống bảng **Items**, tìm cột `Rate` (Đơn giá): Nhập số `1000` (giả sử 1000 USD/máy).
- Cuộn lên đầu trang, bấm **Save** -> Bấm nút **Submit** màu xanh -> Click **Yes**.

🎙️ **Thuyết trình phần này:**
> *"Thưa thầy cô, thay vì tạo đơn hàng theo form thông thường, nhóm em đã lập trình tùy biến thêm các trường (Custom Fields) chuyên biệt cho ngành Xuất nhập khẩu như: Ngày khởi hành (ETD) hay Số tờ khai Hải quan. Điều này giúp hệ thống ERP khớp 100% với bộ chứng từ giấy thực tế ở các doanh nghiệp Logistics."*

---

## PHẦN 2: THEO DÕI LỘ TRÌNH VẬN CHUYỂN (SHIPMENT TRACKING)

**Hành động:**
- Đưa chuột lên thanh tìm kiếm trên cùng, gõ chữ `Shipment Tracking` -> Click vào dòng **Shipment Tracking List**.
- Bấm nút màu xanh **Add Shipment Tracking** ở góc phải.
- Giao diện hiện ra:
  - Ô `Purchase Order`: Bấm vào và chọn mã Đơn hàng (PO) bạn vừa tạo ở Phần 1 (thường nó sẽ nằm ngay dòng đầu tiên trong danh sách xổ xuống).
- Cuộn xuống tìm bảng **Transit Route** (Lộ trình vận chuyển):
  - Click nút **Add Row**: Tại cột `Activity` chọn **Booked**.
  - (Cứ mỗi khi bạn muốn trình bày hàng đã đi đến đâu, bạn lại click **Add Row** để thêm trạng thái, ví dụ thêm dòng 2 chọn **Export Customs Cleared**, dòng 3 chọn **Departed Origin Port**).
- Cuộn lên trên cùng, bấm nút **Save**.

⚠️ **LƯU Ý CỰC KỲ QUAN TRỌNG TẠI BƯỚC NÀY:** 
**TUYỆT ĐỐI CHỈ BẤM "SAVE". KHÔNG ĐƯỢC BẤM "SUBMIT".** 
*(Nếu bạn lỡ bấm Submit, chứng từ sẽ bị khóa cứng màu xanh và bạn không thể Add Row thêm lộ trình khi tàu cập bến được nữa!)*

🎙️ **Thuyết trình phần này:**
> *"Để theo dõi lô hàng đang nằm ở đâu trên toàn cầu, nhóm em đã xây dựng module Shipment Tracking. Nhân viên Logistics sẽ sử dụng bảng Transit Route để cập nhật chi tiết hành trình lô hàng theo đúng chuẩn 8 bước SCM Quốc tế (Từ Booked, Khởi hành, Đang đi đường, đến Cập cảng...). Khác với Đơn hàng chốt 1 lần, Phiếu Tracking này sẽ luôn ở trạng thái Mở (Draft) để nhân viên liên tục cập nhật hành trình cho đến khi hàng thực sự về kho mới được đóng lại."*

---

## PHẦN 3: NHẬN HÀNG VÀ PHÂN BỔ GIÁ VỐN (LANDED COST VOUCHER)

**1. Ghi nhận hàng đang đi đường (Purchase Receipt)**
- Lên thanh tìm kiếm, gõ `Purchase Order` -> Chọn **Purchase Order List** -> Click vào Đơn hàng của Dell US mà bạn tạo ở phần 1.
- Góc trên cùng bên phải, click nút **Create** -> Chọn **Purchase Receipt**.
- Cuộn xuống bảng **Items**, nhìn sang cột `Accepted Warehouse`: Xóa tên kho hiện tại, gõ chữ `Goods In Transit - CK` và click chọn nó.
- Cuộn lên đầu trang, bấm **Save** -> Bấm nút **Submit** màu xanh -> Click **Yes**.

**2. Phân bổ Giá vốn (Landed Cost Voucher - Wow Moment)**
- Ngay tại màn hình Purchase Receipt vừa Submit xong, click nút **Create** -> Chọn **Landed Cost Voucher**.
- Màn hình mới hiện ra. Cột `Distribute Charges Based On`: Bấm vào và chọn **Qty** (Phân bổ theo số lượng).
- Cuộn xuống tìm bảng **Taxes and Charges** (các khoản phí Logistics phát sinh):
  - Click **Add Row** (dòng 1): 
    - Ô `Expense Account`: Chọn `Expenses Included In Valuation - CK`.
    - Ô `Description`: Gõ `Cước tàu biển`.
    - Ô `Amount`: Gõ `30000000` (30 triệu).
  - Click **Add Row** (dòng 2): 
    - Ô `Expense Account`: Chọn `Expenses Included In Valuation - CK`.
    - Ô `Description`: Gõ `Phí lưu bãi`.
    - Ô `Amount`: Gõ `5000000` (5 triệu).
- Cuộn lên đầu trang, bấm **Save** -> Bấm nút **Submit** màu xanh -> Click **Yes**.

🎙️ **Thuyết trình phần này:**
> *"Khi hàng hóa vừa rời cảng, nhân viên làm phiếu Purchase Receipt để ghi nhận tài sản vào kho ảo 'Goods In Transit'. Nhưng trong quá trình vận chuyển thực tế, doanh nghiệp sẽ phải trả các chi phí biến động liên tục như Cước tàu, Phí lưu bãi... Bằng công cụ Landed Cost Voucher, kế toán chỉ cần nhập hóa đơn thực tế phát sinh. Hệ thống sẽ tự động phân bổ đều số tiền 35 triệu này cộng dội vào Giá vốn hàng tồn kho của từng chiếc Laptop, đảm bảo định giá chính xác tuyệt đối."*

---

## PHẦN 4: LUÂN CHUYỂN KHO THỰC TẾ & XEM BÁO CÁO

**1. Chuyển kho lần 1 (Hàng cập cảng)**
- Trên thanh tìm kiếm, gõ `Stock Entry` -> Chọn **Stock Entry List** -> Bấm **Add Stock Entry**.
- Ô `Stock Entry Type`: Bấm chọn **Material Transfer**.
- Ô `Default Source Warehouse` (Kho xuất): Chọn `Goods In Transit - CK`.
- Ô `Default Target Warehouse` (Kho nhập): Chọn `Cat Lai Port`.
- Cuộn xuống bảng **Items**, click **Add Row**: Chọn Item là `Laptop XPS-15`, cột `Qty` gõ `1000`.
- Bấm **Save** -> **Submit** -> **Yes**.

**2. Chuyển kho lần 2 (Hàng về công ty)**
- Vẫn ở màn hình Stock Entry vừa xong, góc trên bên trái có nút mũi tên quay lại danh sách, hoặc bấm nút **+ Add Stock Entry** để tạo mới.
- Ô `Stock Entry Type`: Chọn **Material Transfer**.
- Ô `Default Source Warehouse`: Chọn `Cat Lai Port`.
- Ô `Default Target Warehouse`: Chọn `Stores - CK`.
- Bảng Items, click **Add Row**: Chọn Item là `Laptop XPS-15`, cột Qty gõ `1000`.
- Bấm **Save** -> **Submit** -> **Yes**.

**3. Mở Báo cáo phân tích**
- Trên thanh tìm kiếm, gõ chữ `Landed Cost Valuation Analysis` -> Bấm vào kết quả để mở báo cáo.
- Báo cáo bằng SQL hiện ra, chỉ vào các cột để giải thích.

🎙️ **Thuyết trình phần này:**
> *"Sau khi hàng đi qua các kho vật lý và về đến công ty, Ban giám đốc có thể mở báo cáo tự động Landed Cost Valuation Analysis. Nhìn vào đây có thể thấy rõ:
> - Giá mua gốc (Original Price)
> - Tổng chi phí Logistics dội lên trên từng sản phẩm (Landed Cost Added)
> - Và Giá vốn thực tế cuối cùng (Final Valuation Rate).
> Báo cáo này là vũ khí để doanh nghiệp luôn định giá bán chính xác và chặn đứng tình trạng lỗ ẩn do chi phí ngầm trong Logistics!"*

---
*(Kết thúc Kịch bản)*
