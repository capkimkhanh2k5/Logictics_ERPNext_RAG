# Chủ đề 10: Quản trị Hoạt động Xuất Nhập khẩu và Phân bổ Chi phí Mua hàng
## (Global Trade & Landed Cost Management trên ERPNext)

---

## 1. Mô tả sơ bộ đề tài

Đề tài xây dựng một giải pháp quản trị chuỗi cung ứng quốc tế trên nền tảng **ERPNext**, tập trung vào hai bài toán cốt lõi của doanh nghiệp xuất nhập khẩu:

1. **Quản lý quy trình mua sắm quốc tế (International Procurement)**: từ đặt hàng nhà cung cấp nước ngoài, theo dõi lộ trình vận chuyển (đường biển/đường hàng không), đến khi hàng về kho.
2. **Phân bổ chi phí Landed Cost**: tự động hóa việc tính toán và phân bổ các chi phí phát sinh trong quá trình nhập khẩu (thuế nhập khẩu, phí cảng, phí lưu kho, phí vận chuyển nội địa...) vào giá vốn thực tế của từng sản phẩm, thay vì hạch toán thủ công rời rạc như hiện nay ở nhiều doanh nghiệp.

Ở giai đoạn cuối kỳ, đề tài mở rộng thêm một lớp **AI hỗ trợ nghiệp vụ hải quan**: một chatbot RAG (Retrieval-Augmented Generation) giúp nhân viên khai báo hải quan tra cứu nhanh văn bản pháp luật xuất nhập khẩu và tự động đề xuất **mã HS Code** phù hợp dựa trên mô tả kỹ thuật của sản phẩm đã lưu trong ERP.

---

## 2. Mục đích đề tài

- **Giảm sai sót và thời gian xử lý thủ công** trong việc tính giá vốn hàng nhập khẩu — vốn là bài toán khó vì chi phí landed cost thường đến từ nhiều nguồn, nhiều thời điểm khác nhau (invoice nhà cung cấp, phí hãng tàu, phí hải quan, phí kho bãi).
- **Tăng tính minh bạch và chính xác của giá vốn (COGS)**, giúp doanh nghiệp định giá bán và tính lợi nhuận sát với thực tế hơn.
- **Số hóa và chuẩn hóa quy trình theo dõi vận đơn quốc tế**, giảm phụ thuộc vào email/excel rời rạc giữa các phòng ban (mua hàng, kho, kế toán, xuất nhập khẩu).
- **Hỗ trợ nghiệp vụ khai báo hải quan bằng AI**, giảm rủi ro áp sai mã HS Code (vốn có thể dẫn đến phạt thuế, chậm thông quan) và rút ngắn thời gian tra cứu văn bản pháp luật vốn rất phức tạp và hay thay đổi.
- **Minh họa năng lực tích hợp ERP truyền thống với AI hiện đại (RAG)**, thể hiện hướng đi "Intelligent ERP" — một xu hướng thực tế của các hệ thống ERP hiện nay (SAP, Oracle NetSuite, Odoo đều đang tích hợp AI tương tự).

---

## 3. Hướng triển khai chi tiết

### GIAI ĐOẠN GIỮA KỲ — Nghiên cứu & Mô phỏng trên ERPNext

#### 3.1. Thiết lập quy trình mua sắm quốc tế (International Procurement Flow)

**Cấu hình nghiệp vụ trên ERPNext:**
- Thiết lập **Supplier** nước ngoài với Currency, Payment Terms, Incoterms (FOB, CIF, EXW...) riêng.
- Cấu hình **Multi-Currency** và tỷ giá hối đoái (Exchange Rate) cho việc lập Purchase Order (PO) bằng ngoại tệ.
- Xây dựng luồng chuẩn:
  `Material Request → Request for Quotation (RFQ) → Purchase Order (PO) → Purchase Receipt (PR) → Purchase Invoice`
- Tùy biến (customize) thêm các trường (Custom Fields) cần thiết cho nghiệp vụ XNK trên PO/PR, ví dụ:
  - Số vận đơn (Bill of Lading / Airway Bill number)
  - Cảng đi / Cảng đến (Port of Loading / Port of Discharge)
  - Phương thức vận chuyển (Sea/Air)
  - Ngày dự kiến khởi hành (ETD) / Ngày dự kiến đến (ETA)
  - Số tờ khai hải quan (Customs Declaration Number)

#### 3.2. Theo dõi lộ trình vận đơn (Shipment Tracking)

- Sử dụng module có sẵn **Shipment** (Stock module) của ERPNext hoặc xây dựng DocType tùy chỉnh `Shipment Tracking` liên kết với Purchase Order.
- Định nghĩa các trạng thái lộ trình theo vòng đời thực tế:
  `Booked → Departed Origin Port → In Transit → Arrived Destination Port → Customs Clearance → Delivered to Warehouse`
- (Mở rộng nếu có thời gian) Thử nghiệm tích hợp API tra cứu container/vận đơn công khai (ví dụ MarineTraffic, hoặc mô phỏng dữ liệu do nhóm tự tạo nếu API thật yêu cầu phí) để tự động cập nhật trạng thái.
- Thiết lập cảnh báo/thông báo (Notification) khi lô hàng chuyển trạng thái, hoặc khi ETA trễ so với kế hoạch.

#### 3.3. Cấu hình tự động Landed Cost Voucher

Đây là phần trọng tâm kỹ thuật của giai đoạn giữa kỳ:

- Nghiên cứu và sử dụng DocType **Landed Cost Voucher (LCV)** có sẵn trong ERPNext, liên kết với một hoặc nhiều Purchase Receipt.
- Khai báo các khoản mục chi phí cần phân bổ:
  - Thuế nhập khẩu (Import Duty)
  - Phí cảng, phí bốc dỡ (Terminal Handling Charges)
  - Phí lưu kho, lưu bãi (Demurrage/Storage Fee)
  - Phí vận chuyển nội địa từ cảng về kho
  - Phí bảo hiểm hàng hóa (nếu có)
- Thiết lập **phương pháp phân bổ (Distribution Basis)**: theo số lượng (Qty), theo giá trị (Amount), hoặc theo trọng lượng/thể tích tùy loại chi phí — cần phân tích rõ chi phí nào nên phân bổ theo tiêu chí nào (ví dụ phí lưu kho theo thể tích sẽ hợp lý hơn theo giá trị).
- Kiểm tra kết quả: sau khi submit LCV, giá vốn (Valuation Rate) của từng mặt hàng trong Purchase Receipt liên quan phải được cập nhật lại tự động, phản ánh đúng chi phí thực tế "về đến kho" (landed cost).
- Xây dựng **báo cáo so sánh giá vốn trước/sau phân bổ landed cost** để minh chứng giá trị của giải pháp (ví dụ dùng Report Builder hoặc Query Report trên ERPNext).
- (Nâng cao) Viết Server Script/Client Script để **tự động tạo Landed Cost Voucher** khi Purchase Receipt được submit và có gắn kèm thông tin chi phí ước tính, giảm thao tác thủ công.

#### 3.4. Kết quả kỳ vọng giữa kỳ

- Một quy trình mua hàng quốc tế hoàn chỉnh, có thể demo từ lúc tạo PO đến khi nhận hàng và ghi nhận giá vốn cuối cùng.
- Báo cáo phân tích cho thấy sự khác biệt giữa giá vốn "trên hóa đơn nhà cung cấp" và giá vốn "sau phân bổ landed cost".
- Tài liệu mô tả kiến trúc dữ liệu (DocType, quan hệ, custom fields) đã thiết lập.

---

### GIAI ĐOẠN CUỐI KỲ — Tích hợp ERP + AI

#### 3.5. Chatbot RAG tra cứu văn bản pháp luật xuất nhập khẩu

**Mục tiêu:** hỗ trợ nhân viên khai báo hải quan đặt câu hỏi bằng ngôn ngữ tự nhiên và nhận câu trả lời có trích dẫn nguồn pháp lý, thay vì phải tự tra cứu qua nhiều văn bản (Luật Hải quan, Biểu thuế xuất nhập khẩu, Thông tư của Bộ Tài chính/Tổng cục Hải quan...).

**Kiến trúc đề xuất:**

| Thành phần | Công nghệ/Cách làm |
|---|---|
| Nguồn dữ liệu | Thu thập văn bản pháp luật XNK công khai (Luật Hải quan, Nghị định, Thông tư, Biểu thuế XNK) dạng PDF/HTML |
| Xử lý & Chunking | Trích xuất text, chia nhỏ theo điều/khoản để giữ ngữ nghĩa pháp lý |
| Embedding | Model embedding tiếng Việt (ví dụ các model đa ngôn ngữ hỗ trợ tiếng Việt) |
| Vector Store | pgvector (PostgreSQL) — có thể tận dụng kinh nghiệm đã có với pgvector, hoặc Chroma/FAISS nếu tách service riêng |
| Retrieval | Truy vấn top-k đoạn văn bản liên quan nhất đến câu hỏi |
| LLM sinh câu trả lời | Gọi API LLM (qua Function/Tool Calling) kết hợp ngữ cảnh truy xuất được, trả lời kèm trích dẫn điều khoản/nguồn |
| Giao diện | Widget chat nhúng trong ERPNext (Frappe UI) hoặc trang riêng gọi qua REST API của ERPNext |

**Luồng xử lý:**
`Câu hỏi của nhân viên → Embedding câu hỏi → Truy vấn Vector Store → Lấy đoạn văn bản liên quan → Ghép ngữ cảnh + câu hỏi → Gửi LLM → Trả lời kèm trích dẫn nguồn`

#### 3.6. Tự động đề xuất mã HS Code

**Mục tiêu:** dựa trên mô tả thành phần kỹ thuật của sản phẩm đã lưu trong Item (ERPNext), hệ thống tự động gợi ý mã HS Code phù hợp nhất.

**Cách tiếp cận đề xuất:**
1. **Chuẩn hóa dữ liệu Item**: bổ sung Custom Field mô tả kỹ thuật chi tiết (chất liệu, công dụng, thành phần cấu tạo) trong DocType Item nếu chưa đầy đủ.
2. **Xây dựng cơ sở tri thức HS Code**: số hóa Danh mục hàng hóa xuất nhập khẩu Việt Nam (HS Code + mô tả + chú giải) thành một tập dữ liệu có thể truy vấn (kết hợp trong cùng Vector Store với văn bản pháp luật, hoặc tách riêng theo namespace).
3. **Kỹ thuật đề xuất mã HS**:
   - Bước 1 — Retrieval: tìm các mã HS có mô tả gần nghĩa nhất với mô tả sản phẩm (semantic search).
   - Bước 2 — LLM re-ranking/reasoning: dùng LLM để so sánh mô tả sản phẩm với chú giải chi tiết của các mã HS ứng viên, chọn ra mã phù hợp nhất kèm giải thích lý do (ví dụ: dựa vào chất liệu chính, công dụng chính theo nguyên tắc phân loại HS).
   - Bước 3 — Trả về kết quả có **độ tin cậy (confidence)** và **cảnh báo cần nhân viên xác nhận thủ công** đối với các trường hợp mơ hồ, vì áp sai mã HS có rủi ro pháp lý cao — AI chỉ đóng vai trò **gợi ý hỗ trợ**, không tự động khai báo.
4. **Tích hợp vào ERPNext**: thêm nút "Đề xuất HS Code" ngay trên form Item hoặc Purchase Order, gọi API RAG, hiển thị kết quả kèm nguồn trích dẫn quy tắc phân loại.

#### 3.7. Kết quả kỳ vọng cuối kỳ

- Chatbot RAG hoạt động, trả lời được câu hỏi nghiệp vụ hải quan có trích dẫn văn bản pháp luật.
- Chức năng đề xuất HS Code tích hợp trực tiếp trong ERPNext, có test với ít nhất một bộ sản phẩm mẫu đa dạng ngành hàng.
- Demo end-to-end: từ Item mới → đề xuất HS Code → tạo PO quốc tế → theo dõi vận đơn → phân bổ Landed Cost → giá vốn cuối cùng, có hỏi đáp AI hỗ trợ xuyên suốt quy trình.

---

## 4. Đề xuất kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────┐
│                        ERPNext (Frappe)                  │
│  ┌───────────┐   ┌────────────────┐   ┌───────────────┐  │
│  │ Purchase  │   │ Shipment       │   │ Landed Cost   │  │
│  │ Order/PR  │──▶│ Tracking       │──▶│ Voucher       │  │
│  └───────────┘   └────────────────┘   └───────────────┘  │
│         │                                    │            │
│         ▼                                    ▼            │
│  ┌───────────────────────────────────────────────────┐   │
│  │           Custom Fields / Server Scripts           │   │
│  └───────────────────────────────────────────────────┘   │
└───────────────────────────┬───────────────────────────────┘
                             │ REST API
                             ▼
                ┌─────────────────────────┐
                │   RAG Service (backend)  │
                │  - Embedding + Retrieval │
                │  - LLM (Function Calling)│
                └────────────┬─────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
    ┌───────────────────┐        ┌─────────────────────┐
    │ Vector Store        │        │ LLM API (chat/       │
    │ (pgvector)           │        │ tool calling)         │
    │ - Văn bản pháp luật  │        └─────────────────────┘
    │ - Danh mục HS Code   │
    └───────────────────┘
```

---

## 5. Gợi ý phân chia công việc (nếu làm nhóm)

| Mảng | Nội dung |
|---|---|
| ERP Core | Cấu hình Procurement, Shipment Tracking, Landed Cost Voucher, Custom Fields/Scripts |
| Data & RAG | Thu thập/xử lý văn bản pháp luật, xây dựng Vector Store, pipeline embedding |
| AI Integration | Xây dựng service RAG, logic đề xuất HS Code, API tích hợp với ERPNext |
| Frontend/UX | Widget chatbot, giao diện đề xuất HS Code trên form Item/PO |
| Testing & Báo cáo | Kịch bản test end-to-end, báo cáo so sánh giá vốn, đánh giá độ chính xác đề xuất HS Code |

---

## 6. Rủi ro và lưu ý

- **Độ chính xác của đề xuất HS Code** phụ thuộc nhiều vào chất lượng dữ liệu mô tả kỹ thuật sản phẩm và độ đầy đủ của cơ sở tri thức HS — cần nhấn mạnh AI là công cụ **hỗ trợ**, quyết định cuối cùng vẫn thuộc về nhân viên khai báo.
- **Phương pháp phân bổ Landed Cost** cần được lựa chọn phù hợp với từng loại chi phí, nên có phần phân tích/lập luận rõ ràng trong báo cáo thay vì chỉ dùng mặc định "theo giá trị".
- Nếu không có quyền truy cập API tracking vận đơn thật, có thể **mô phỏng dữ liệu** (mock data) nhưng cần mô tả rõ trong báo cáo đây là mô phỏng cho mục đích demo.
