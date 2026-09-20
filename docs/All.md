CÁC VẤN ĐỀ VÀ HƯỚNG GIẢI QUYẾT
Doanh nghiệp chi hàng tr USD cho 1 lô hàng, về mặt pháp lý thì hàng đã thuộc sở hữu của doanh nghiệp và phải chịu hoàn toàn mọi rủi ro, hàng thì đang lênh đênh trên biển, trên không nhưng không ở kho đích và như vậy sẽ dẫn đến số lượng thực tế có thể sử dụng sai sót, ảnh hưởng đến kế hoạch sản xuất và cam kết bán lẻ nhưng ngược lại nếu trì hoãn việc ghi sổ đến khi hàng nhập kho nội địa thì sẽ bỏ sót tài sản đang đi đường thuộc quyền sở hữu, làm lệch bản cân đối kế toán -> Tiền đã xuất, tài sản đã ghi nhận nhưng sản phẩm kh ở trong kho đích mà đang di chuyển
=> Sử dụng cây kho hàng để giải quyết vấn đề trên kết hợp tính năng quản lí đơn hàng đang đi.
Hàng sẽ kh nhảy có từ kho nguồn đến kho đích, mà phải qua trung chuyển nhiều lần từ kho cảng đi, kho trên biển, kho đích -> Dẫn đến chuyện chi phí tuyến bến bãi, cước tàu, bảo hiểm tăng kh ngừng -> Hệ thống sử dụng landed cost: gom toàn bộ cước tàu, thuế nhập khẩu, … và phân bổ thẳng vào giá vốn có thể chia theo tỷ lệ giá trị lô hàng, hoặc số lượng.
Có một số trường hợp trong thực tế hàng đã nhập, tiến hành sản xuất và bán ra thị trường thì hoá đơn cước vận tải mới xuất hiện -> kế toán kh cần phải lục tung tìm những khoản phí nhỏ lẻ rồi cộng lại từ đầu để tính giá vốn, mà sử dụng tính năng tính lại giá vốn hồi tố (nghĩa là khi hoá đơn về chậm, hệ thống sẽ rà soát lại các hoá đơn mọi giao dịch xuất kho đã xảy ra xuất kho và tự động điều chỉnh giá vốn 
Vì thông số kỹ thuật từ nhà máy gửi thì toàn là từ viết tắt trong khi biểu thuế là các câu chữ đặc sệt tính pháp luật và hàng ngàn chú giải loại trừ, nên nhập nhầm 1 mã sẽ phị phạt rất nặng -> sử dụng MultiAgent để thực hiện đề xuất mã HS chính xác:
•	Agent 1: Chuyên đọc thông số
•	Agent 2: Đối chiếu luật RAG
o	Tri thức của RAG: toàn văn Thông tư 31/2022/TT-BTC, Nghị định 26/2023/NĐ-CP và bộ Chú giải chi tiết WCO (Explanatory Notes))
o	triển khai kỹ thuật phân đoạn theo phân cấp văn bản luật (Hierarchical Chunking). Mỗi đoạn trích dữ liệu được bóc tách theo đơn vị hoàn chỉnh: Phần, Chương, Nhóm 4 số, Phân nhóm 6 số và Chú giải pháp lý đi kèm các trường siêu dữ liệu định danh như mã chương, mã phân nhóm, năm ban hành và tham chiếu quy tắc GIR liên quan
o	hệ thống sử dụng mô hình embedding BGE-M3.hỗ trợ đồng thời hai cơ chế: Biểu diễn vector dày (Dense Embedding) để nắm bắt mối liên hệ ngữ nghĩa tương đồng giữa mô tả sản phẩm và nội dung quy chuẩn, và Biểu diễn vector thưa (Sparse Embedding) đóng vai trò như một bộ trọng số từ khóa tương tự BM25 mở rộng nhằm bắt chính xác các định danh kỹ thuật đặc thù, tên hóa chất, kích thước số học hoặc mã nhóm.
•	Agent 3: Phản biện logics
Vẫn human-in-loop, chủ động hỏi ngược lại con người (ví dụ như thép này làm bằng gì, độ dày bao nhiêu, dài bao nhiêu, …)
________________________________________
Cơ chế phân loại mã HS phân tầng
Mã HS được cấu trúc thành bài toán duyệt đồ thị tri thức có ràng buộc (Graph Traversal Reasoning) phỏng theo đúng trình tự tư duy của chuyên gia hải quan và cấu trúc của 6 quy tắc tổng quát GIR.
Hệ thống thực hiện suy luận qua 4 tầng phân cấp kế tiếp nhau:
•	Ở Tầng 1 (Cấp độ Chương - 2 chữ số), tác tử AI phân tích cấu tạo vật liệu nền tảng và chức năng căn bản của sản phẩm để xác định không quá 3 Chương tiềm năng nhất trong tổng số 97 chương của biểu thuế.
•	Ở Tầng 2 (Cấp độ Nhóm - 4 chữ số), tác tử vận dụng Quy tắc tổng quát 1 và 3, đối chiếu thông số sản phẩm với câu chữ của các Heading thuộc các Chương đã chọn và loại trừ các nhóm vi phạm Chú giải loại trừ của Chương.
•	Ở Tầng 3 (Cấp độ Phân nhóm - 6 chữ số), tác tử vận dụng Quy tắc tổng quát 6 để so sánh các phân nhóm cùng cấp độ của WCO dựa trên các tiêu chí chi tiết về công năng hoặc thông số vận hành.
•	Ở Tầng 4 (Cấp độ Dòng thuế AHTN - 8 chữ số), tác tử tiếp tục bóc tách các tiêu chí đặc thù của khu vực ASEAN như công suất định mức, dải tần số, điện áp làm việc hoặc kích thước hình học để chốt mã 8 chữ số sau cùng kèm mức thuế suất MFN đối ứng từ Nghị định 26/2023/NĐ-CP.
________________________________________
Landed Cost Voucher
Nó là tổng của: Giá mua + Thuế + Cước vận tải + Phí bảo hiểm + Phí bến bãi...
Cơ chế hoạt động của chứng từ LCV trong ERPNext diễn ra như sau:
1.	Bước 1 (Nhập kho gốc): Bạn làm Purchase Receipt nhập 1000 Laptop vào kho. Hệ thống ghi nhận giá tạm thời là 1.000 USD/chiếc. Tài sản kho tăng lên.
2.	Bước 2 (Gom chi phí): Các hóa đơn từ Hãng tàu (Ocean Freight), từ Hải quan (Thuế), từ Cảng (THC) gửi về. Bạn đưa tất cả các chi phí này vào chứng từ Landed Cost Voucher.
3.	Bước 3 (Phân bổ - Phép màu xảy ra): Khi bạn bấm Submit LCV, hệ thống sẽ lấy tổng các chi phí dội thêm này, chia đều (theo Số lượng hoặc Giá trị) cho 1000 chiếc Laptop bạn vừa nhập kho.
4.	Bước 4 (Cập nhật giá vốn mới): Hệ thống sẽ lẳng lặng vào trong sổ kho, gạch bỏ cái giá gốc 1.000 USD đi, và tự động cộng dồn các chi phí kia vào để tính ra cái giá mới (Ví dụ: 1.060 USD/chiếc).
Kết quả: Bất cứ khi nào nhân viên kinh doanh mở phần mềm lên xem tồn kho, họ sẽ thấy chiếc Laptop đó có giá gốc là 1.060 USD, từ đó định giá bán chính xác để công ty luôn có lãi!
 
Trong thực tế, tàu chở hàng có thực sự chạy vòng cung qua Bắc Thái Bình Dương và ghé nhiều cảng trung gian không? (Hình 5)
CÂU TRẢ LỜI LÀ: HOÀN TOÀN ĐÚNG 100% TRONG THỰC TẾ HÀNG HẢI QUỐC TẾ.
Có 2 lý do khoa học và kinh tế cốt lõi lý giải điều này:
1. Đường cong "Đại hải trình" (Great Circle Sailing) qua sát Alaska
•	Trên bản đồ phẳng 2D (phép chiếu Mercator), bạn thấy con tàu chạy vồng lên rất cao về phía Bắc sát quần đảo Aleutian (gần Alaska/Bắc Cực) rồi mới chúc xuống Nhật Bản và Việt Nam. Trông có vẻ như con tàu đang "đi đường vòng".
•	Nhưng thực tế, Trái Đất là một khối cầu. Khoảng cách ngắn nhất giữa hai điểm trên bề mặt hình cầu không phải là đường thẳng trên bản đồ giấy, mà là một Đường tròn lớn (Great Circle).
•	Khi chiếu đường tròn lớn này lên bản đồ phẳng 2D, nó sẽ tạo thành một đường cong vồng lên phía các cực.
•	Tuyến đường vòng cung phía bắc này thực chất ngắn hơn từ 1.000 đến 1.500 hải lý (~2.500 km) so với việc tàu chạy thẳng ngang qua xích đạo! Với một con tàu container khổng lồ, việc rút ngắn 2.500 km giúp các hãng tàu (như Maersk, MSC, COSCO) tiết kiệm hàng trăm tấn dầu (hàng triệu USD) và rút ngắn từ 3 đến 5 ngày chạy biển. Tất cả tàu hàng xuyên Thái Bình Dương đều đi theo luồng này.
2. Mô hình "Trục - Nan hoa" (Hub-and-Spoke) và Chuyển tải (Transshipment)
•	Trong thực tế logistics toàn cầu, gần như không bao giờ có chuyện một siêu tàu container (chở 15.000 – 24.000 container) chạy thẳng từ Mỹ về riêng một cảng Việt Nam rồi quay đầu.
•	Ngành hàng hải vận hành theo mô hình trung chuyển quốc tế:
o	Tàu mẹ (Mother Vessel): Chở hàng chục nghìn container xuất phát từ Bờ Tây nước Mỹ chạy xuyên Thái Bình Dương đến các Siêu cảng trung chuyển Đông Á (Transshipment Hubs) lớn nhất thế giới như: Cảng Busan (Hàn Quốc), Thượng Hải / Ninh Ba (Trung Quốc), Cao Hùng (Đài Loan).
o	Dỡ hàng & Gom hàng: Tại mỗi cảng trung gian này, tàu mẹ cập bến để bốc dỡ các container đích và nhận thêm container xuất khẩu mới.
o	Tàu gom (Feeder Vessel): Các container về Việt Nam (Hải Phòng, Đà Nẵng, Cát Lái) sẽ được dỡ xuống bãi cảng trung chuyển, sau đó xếp lên các tàu feeder nhỏ hơn (1.000 – 3.000 TEU) để chạy men theo bờ biển Đông Á về cập cảng Việt Nam.
•	Do đó, lộ trình mà thư viện searoute tạo ra chạy dọc theo các eo biển quốc tế (eo biển Tsushima, eo biển Đài Loan, eo biển Luzon) chính là các Luồng phân luồng hàng hải quốc tế (TSS - Traffic Separation Schemes) mà tàu thuyền thực tế bắt buộc phải tuân theo để đảm bảo an toàn hàng hải và tránh bãi cạn.
 
🤖 **Applying knowledge of `@[orchestrator]`...**

Chào bạn, đây là phần giải thích chuyên sâu và toàn diện về hai vấn đề bạn quan tâm: **bản chất thuật toán của OSRM** và **toàn cảnh luồng vận chuyển Door-to-Door thực tế từ Mỹ về Việt Nam**.

---

# PHẦN 1: BẢN CHẤT CỦA ĐỊNH TUYẾN ĐƯỜNG BỘ OSRM

### 1. OSRM là gì?
**OSRM (Open Source Routing Machine)** là một động cơ định tuyến đường bộ mã nguồn mở hiệu năng cao viết bằng C++, được phát triển trên nền tảng dữ liệu bản đồ toàn cầu **OpenStreetMap (OSM)**. Đây là công nghệ cốt lõi đứng sau các nền tảng điều phối giao thông và logistics lớn trên thế giới (như Mapbox, Grab, Delivery Hero...).

### 2. Có phải OSRM "tự biết tìm các con đường lớn như QL1A, cao tốc để đi" không?
**Câu trả lời là: ĐÚNG, nhưng không phải do "học vẹt", mà là nhờ cơ chế TOÁN HỌC & ĐỒ THỊ MẠNG LƯỚI GIAO THÔNG:**

```
                  ┌────────────────────────────────────────┐
                  │ Dữ liệu OpenStreetMap (OSM Toàn cầu)   │
                  │ (Phân loại tag: motorway, trunk, local) │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
         ┌────────────────────────────────────────────────────────┐
         │ Hệ số Chi phí & Tốc độ (Speed & Cost Profile)          │
         │ - Cao tốc (motorway/CT01): Trọng số 100 - 120 km/h     │
         │ - Quốc lộ chính (trunk/QL1A): Trọng số 70 - 90 km/h    │
         │ - Đường liên xã/hẻm nhỏ: Trọng số 20 - 30 km/h         │
         └──────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
         ┌────────────────────────────────────────────────────────┐
         │ Thuật toán Rút gọn Đồ thị (Contraction Hierarchies)    │
         │ Tự động tạo "đường tắt" (shortcuts) qua các trục xương  │
         │ sống quốc gia (QL1A, CT01, Interstate...)              │
         └──────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
         ┌────────────────────────────────────────────────────────┐
         │ Lộ trình tối ưu: Xuất phát ➔ Đường nhánh ➔ QUỐC LỘ/    │
         │ CAO TỐC ➔ Đường nhánh ➔ Cửa Kho bãi đích               │
         └────────────────────────────────────────────────────────┘
```

#### Chi tiết 3 cơ chế vận hành của OSRM:
1. **Phân cấp đường bộ theo nhãn dữ liệu (Tag Classification):**
   * Trong OpenStreetMap, mọi đoạn đường trên thế giới đều được gán nhãn:
     * `highway=motorway`: Đường cao tốc (như CT01 Bắc - Nam, Interstate I-5, I-280 ở Mỹ).
     * `highway=trunk`: Quốc lộ huyết mạch (như Quốc lộ 1A, US-101).
     * `highway=primary` / `secondary`: Tỉnh lộ, đường trục đô thị.
     * `highway=residential` / `service`: Đường nội bộ, đường khu công nghiệp.
2. **Hàm chi phí thời gian (Time-Cost Weighting):**
   * Khi tính toán cho phương tiện xe tải/ô tô (`driving profile`), OSRM không chỉ tính "khoảng cách ngắn nhất" mà tính **"thời gian nhanh nhất"** ($Time = \frac{Distance}{Speed}$).
   * Mặc dù đi một đường cắt thẳng qua đường làng hay bờ biển có thể ngắn hơn vài kilomet, nhưng tốc độ chỉ đạt $20 - 30\text{ km/h}$ và có khúc cua gắt, trong khi đi trên Quốc lộ 1A và Cao tốc đạt $80 - 100\text{ km/h}$. Vì vậy, thuật toán luôn ưu tiên kéo lộ trình vào các trục xương sống quốc gia.
3. **Giải thuật Contraction Hierarchies (CH) — Phản hồi trong vài mili-giây:**
   * Mạng lưới đường bộ Việt Nam hay Mỹ có hàng chục triệu nút giao. Nếu dùng thuật toán Dijkstra truyền thống thì tìm đường từ Hải Phòng đến Đà Nẵng sẽ mất vài chục giây.
   * OSRM sử dụng kỹ thuật **Contraction Hierarchies (Phân tầng rút gọn)**: Nó tiền xử lý trước toàn bộ đồ thị, gom các con đường huyết mạch (QL1A, Cao tốc) thành các tầng cao nhất. Khi bạn yêu cầu lộ trình từ Hải Phòng đến Đà Nẵng, OSRM chỉ cần:
     1. Đi từ Cảng Hải Phòng ra đường lớn gần nhất (Cao tốc Hà Nội - Hải Phòng / QL10).
     2. Nhập vào trục huyết mạch Quốc lộ 1A / Cao tốc Bắc - Nam chạy một mạch xuyên miền Trung.
     3. Tách khỏi QL1A khi tới Đà Nẵng, đi vào đường nội bộ KCN Hòa Khánh (Đường số 2) để tới kho của bạn.
   * Nhờ đó, OSRM trả về kết quả chuẩn xác từng góc cua chỉ trong **chưa đầy 1 giây**!

---

# PHẦN 2: TOÀN CẢNH LUỒNG ĐI THỰC TẾ TỪ MỸ VỀ VIỆT NAM (DOOR-TO-DOOR)

Một đơn hàng quốc tế từ trụ sở Apple (Mỹ) về Kho bãi Cáp Kim Khánh (Đà Nẵng) trải qua **3 giai đoạn lớn** tạo thành một chuỗi vận tải đa phương thức hoàn chỉnh:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 1: FIRST-MILE (Đường bộ Mỹ 🚚)                                              │
│ Kho Apple Park (Cupertino) ────────(Cao tốc I-880/I-5)────────▶ Cảng Oakland / LA      │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ (Cẩu container lên tàu mẹ)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 2: MAIN-HAUL (Đại hải trình Quốc tế 🚢)                                      │
│ Cảng Bờ Tây Mỹ ──(Cung vòng lớn Alaska)──▶ Trung chuyển Đông Á ──▶ Cảng Hải Phòng      │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ (Thông quan hải quan & gắp lên xe tải)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 3: LAST-MILE (Đường bộ Việt Nam 🚚)                                         │
│ Cảng Hải Phòng ────────(Quốc lộ 1A & Cao tốc Bắc Nam)────────▶ Kho Cáp Kim Khánh ĐN    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 📍 GIAI ĐOẠN 1: Vận chuyển Chặng đầu tại Mỹ (First-mile Road Freight)
* **Điểm xuất phát:** Kho trung tâm / Tổng hành dinh Apple Park (1 Apple Park Way, Cupertino, CA 95014, Thung lũng Silicon).
* **Nghiệp vụ thực tế:**
  1. **Đóng hàng & Niêm phong Seal:** Hàng hoá (iPhone, chip vi xử lý, phụ kiện) được đóng gói vào các thùng carton tiêu chuẩn, xếp lên pallet và đưa vào trong container $40\text{ feet}$. Nhân viên kho bấm khoá chì niêm phong (Container Bolt Seal) có mã số độc nhất.
  2. **Vận tải Drayage:** Xe đầu kéo container (Truck) nhận container từ kho Cupertino, chạy theo tuyến cao tốc liên bang **I-280 North và I-880 North** hướng về vịnh San Francisco để vào **Cảng biển Quốc tế Oakland** (hoặc theo trục **Interstate 5 South** xuống Cảng Los Angeles / Long Beach).
  3. **Hạ bãi cảng (Gate-in):** Đến cổng cảng biển, xe qua trạm cân tự động (Weigh Station), tài xế xuất trình Lệnh hạ hàng (Dock Receipt / Shipping Order), hạ container xuống bãi chứa container (Container Yard - CY).

---

### 🌊 GIAI ĐOẠN 2: Vận chuyển Quốc tế Vượt Thái Bình Dương (Main-haul Ocean Transit)
* **Phương tiện:** Siêu tàu chở container viễn dương (Ultra Large Container Vessel - ULCV) có chiều dài gần $400\text{ m}$, sức chở $15.000 - 24.000\text{ TEU}$ của các hãng tàu lớn (Maersk, MSC, COSCO, ONE, Evergreen).
* **Nghiệp vụ thực tế:**
  1. **Bốc hàng lên tàu (Loading):** Cẩu giàn bờ khổng lồ (Ship-to-Shore Gantry Crane) nhấc container từ bãi bốc lên boong tàu mẹ theo sơ đồ xếp tải (Stowage Plan) đã tính toán cân bằng trọng tâm tàu. Hãng tàu phát hành Vận đơn đường biển (**Bill of Lading - B/L**).
  2. **Hải trình theo Cung vòng lớn (Great Circle Sailing):**
     * Tàu nhổ neo rời Bờ Tây nước Mỹ, chạy vòng cung lên phía Bắc sát quần đảo Aleutian (Alaska). Đây là cung đường ngắn nhất trên mặt cầu Trái Đất (tiết kiệm hơn $2.500\text{ km}$ so với chạy ngang xích đạo).
     * Tàu chạy qua vùng biển quốc tế Bắc Thái Bình Dương trong khoảng $10 - 14\text{ ngày}$.
  3. **Chuyển tải tại Siêu cảng Đông Á (Transshipment Hub):**
     * Tàu mẹ cập cảng trung chuyển quốc tế lớn ở Đông Á (như Cảng Busan - Hàn Quốc hoặc Cảng Cao Hùng - Đài Loan).
     * Tại đây, container của bạn được dỡ xuống bãi trung chuyển và chuyển tiếp lên một **tàu Feeder** (tàu gom hàng nội Á có sức chở nhỏ hơn, khoảng $2.000 - 4.000\text{ TEU}$) để tiếp tục chạy qua eo biển Đài Loan và tiến vào Biển Đông.
  4. **Cập cảng Việt Nam:** Tàu Feeder theo luồng hàng hải vào luồng Lạch Huyện, cập cầu cảng nước sâu **Cảng Hải Phòng** (hoặc Cảng Cát Lái TP.HCM / Cảng Tiên Sa Đà Nẵng).

---

### 🇻🇳 GIAI ĐOẠN 3: Thông quan Hải quan & Vận chuyển Chặng cuối (Last-mile Road Delivery)
* **Điểm tiếp nhận:** Cảng biển Hải Phòng (Cảng Lạch Huyện / Đình Vũ).
* **Nghiệp vụ thông quan (Customs Clearance):**
  1. **Mở Tờ khai Hải quan điện tử:** Doanh nghiệp mở tờ khai hải quan nhập khẩu trên hệ thống VNACCS/VCIS, đính kèm Hóa đơn thương mại (Commercial Invoice), Bảng kê đóng gói (Packing List) và Vận đơn B/L.
  2. **Phân luồng:** Hệ thống phân luồng (Xanh: thông quan ngay; Vàng: kiểm tra chứng từ; Đỏ: kiểm tra thực tế hàng hoá). Sau khi hoàn thành nghĩa vụ thuế VAT và thuế nhập khẩu, hàng được cấp phép thông quan và phát hành Phiếu giao nhận hàng (EIR giao hàng).
* **Vận tải nội địa bám sát Quốc lộ 1A (do OSRM dẫn đường):**
  1. Xe đầu kéo container Việt Nam vào cảng nhận container lên rơ-moóc.
  2. Xe xuất phát từ Cảng Hải Phòng, theo đường nối cao tốc Hà Nội - Hải Phòng, nhập vào **Quốc lộ 1A / Cao tốc Bắc - Nam (CT01)**.
  3. **Lộ trình xuyên dải đất miền Trung (khoảng $810\text{ km}$):**
     * Chạy qua Ninh Bình, Thanh Hóa, Vinh (Nghệ An), Hà Tĩnh, qua Đèo Ngang vào Quảng Bình, Quảng Trị, TP. Huế.
     * Qua Hầm Hải Vân (hoặc vượt Đèo Hải Vân) để tiến vào địa phận TP. Đà Nẵng.
* **Giao nhận tại Kho đích:**
  * Xe từ cửa ngõ phía Bắc Đà Nẵng rẽ vào **Khu công nghiệp Hòa Khánh (Quận Liên Chiểu)**, đi vào đúng **Đường số 2** (ngay gần khuôn viên Trường Đại học Bách Khoa - ĐH Đà Nẵng DUT).
  * Xe lùi vào cửa dock của **Kho bãi Logistics Cáp Kim Khánh**.
  * Thủ tục kết thúc: Nhân viên kho kiểm tra mã số kẹp chì seal còn nguyên vẹn, cắt chì, dỡ hàng vào pallet trong kho bãi và ký Biên bản giao nhận hàng (Proof of Delivery - POD).
  * Trạng thái trên hệ thống ERPNext chuyển thành **"Đã giao hàng thành công" (Delivered / Stock Entry 100%)**.

---

### 🎯 TỔNG KẾT

| Tiêu chí | Chặng 1: First-Mile 🚚 | Chặng 2: Main-Haul 🚢 | Chặng 3: Last-Mile 🚚 |
| :--- | :--- | :--- | :--- |
| **Không gian** | Nội địa Bờ Tây Hoa Kỳ | Xuyên Thái Bình Dương & Biển Đông | Duyên hải Miền Trung Việt Nam |
| **Cự ly** | $\approx 75 - 600\text{ km}$ | $\approx 12.000 - 13.500\text{ km}$ | $\approx 810\text{ km}$ |
| **Công nghệ định tuyến** | **OSRM** (Mạng lưới Interstate I-5/I-880) | **searoute** (Luồng hàng hải & eo biển quốc tế) | **OSRM** (Quốc lộ 1A & Cao tốc Bắc - Nam) |
| **Chứng từ chính** | Phiếu xuất kho, Dock Receipt | Vận đơn đường biển (Bill of Lading - B/L) | Tờ khai Hải quan, Lệnh giao hàng (D/O), Phiếu kho |

Sự kết hợp giữa **searoute (đường biển)** và **OSRM (đường bộ)** chính là chìa khoá giúp hệ thống của bạn mô phỏng đường đi chuẩn xác đến từng góc cua trên đất liền và từng hải trình trên biển, không còn bất kỳ đoạn nào bị cắt chéo vô lý!



Error: API error (attempt 1): RESOURCE_EXHAUSTED (code 429): Resource has been exhausted (e.g. check quota). (Error ID: 880ea3c7-a1b9-41fd-8027-b7f5830652a6-4444-2008)

Error: API error (attempt 2): RESOURCE_EXHAUSTED (code 429): Resource has been exhausted (e.g. check quota). (Error ID: 880ea3c7-a1b9-41fd-8027-b7f5830652a6-4445-2008)

Error: API error (attempt 3): RESOURCE_EXHAUSTED (code 429): Resource has been exhausted (e.g. check quota). (Error ID: 880ea3c7-a1b9-41fd-8027-b7f5830652a6-4446-2008)

Error: API error (attempt 4): RESOURCE_EXHAUSTED (code 429): Resource has been exhausted (e.g. check quota). (Error ID: 880ea3c7-a1b9-41fd-8027-b7f5830652a6-4447-2008)

Error: API error (attempt 5): RESOURCE_EXHAUSTED (code 429): Resource has been exhausted (e.g. check quota). (Error ID: 880ea3c7-a1b9-41fd-8027-b7f5830652a6-4448-2008)

Error: API error (attempt 6): RESOURCE_EXHAUSTED (code 429): Resource has been exhausted (e.g. check quota). (Error ID: 880ea3c7-a1b9-41fd-8027-b7f5830652a6-4449-2008)

Searched for "Shipment Tracking"
Viewed shipment_tracking.js:1-20
Viewed aftership.py:1-49

🤖 **Applying knowledge of `@[orchestrator]`...**

Chào bạn, đây là câu hỏi rất thực tế và chạm đúng vào "trái tim" vận hành của một hệ thống quản lý chuỗi cung ứng (Supply Chain / ERP). Dưới đây là câu trả lời chi tiết, phân định rõ **toàn bộ 6 bước** và **ai là người cập nhật trạng thái ở bước Theo dõi hành trình, cùng cách thức thực hiện ra sao**:

---

# 1. XÁC NHẬN CHUỖI 6 BƯỚC HOÀN CHỈNH CỦA MỘT ĐƠN HÀNG

Hệ thống **Logistics Wizard** trên nền tảng **ERPNext v15** được thiết kế chuẩn hoá theo mô hình chuỗi cung ứng mua hàng nhập khẩu quốc tế (Procurement & Import-Export Chain) gồm đúng 6 bước liên kết chặt chẽ:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. Material Request  ➔ 2. Purchase Order  ➔ 3. Shipment Tracking                       │
│    (Yêu cầu mua hàng)    (Đơn đặt hàng PO)     (Theo dõi hành trình Door-to-Door)      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. Purchase Receipt  ➔ 5. Landed Cost     ➔ 6. Stock Entry                             │
│    (Biên bản nhận hàng)  (Phân bổ giá vốn)     (Nhập kho tăng tồn)                     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Step 1: Yêu cầu mua hàng (Material Request):** Phòng sản xuất / Kho tạo đề xuất cần mua linh kiện, nguyên vật liệu.
2. **Step 2: Đơn đặt hàng (Purchase Order - PO):** Phòng Mua hàng phát hành đơn PO, ký hợp đồng ngoại thương với nhà cung cấp (ví dụ: Apple Inc. tại Mỹ).
3. **Step 3: Theo dõi hành trình (Shipment Tracking):** Quản lý toàn bộ hành trình vận tải đa phương thức từ kho nước ngoài vượt biển/đường bay về tới Việt Nam.
4. **Step 4: Biên bản nhận hàng (Purchase Receipt - PR):** Hàng về tới kho đích, thủ kho kiểm đếm thực tế, đối chiếu số lượng và kẹp chì container.
5. **Step 5: Phân bổ giá vốn (Landed Cost Voucher - LCV):** Kế toán tập hợp toàn bộ chi phí phụ trợ (cước tàu biển, bảo hiểm quốc tế, thuế nhập khẩu, phí nâng hạ THC, phí kéo xe container) để cộng đều vào giá vốn từng sản phẩm.
6. **Step 6: Nhập kho chính thức (Stock Entry):** Xác nhận tăng số lượng tồn kho khả dụng để đưa vào sản xuất hoặc kinh doanh.

---

# 2. Ở STEP THEO DÕI HÀNH TRÌNH: AI LÀ NGƯỜI CẬP NHẬT TRẠNG THÁI?

Trong nghiệp vụ Logistics quốc tế và trên phần mềm ERP, việc cập nhật trạng thái đơn hàng được thực hiện bởi **3 đối tượng chính** (kết hợp giữa con người và công nghệ tự động):

```
                     NGUỒN DỮ LIỆU THỰC TẾ
   ┌────────────────────────────────────────────────────────┐
   │ Hãng tàu / Hãng bay (Maersk, ONE, COSCO, Cathay Cargo) │
   │ Thiết bị định vị GPS / AIS trên Tàu biển & Container   │
   └───────────────────────────┬────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   【 CÁCH 1: TỰ ĐỘNG 】                 【 CÁCH 2: THỦ CÔNG 】
  API / Webhook / AfterShip             Nhân viên Logistics / Đại lý
  (Hệ thống tự động đồng bộ)            (Kiểm tra chứng từ & cập nhật)
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
            ┌─────────────────────────────────────┐
            │       ERPNext: SHIPMENT TRACKING    │
            │   (Tự động tính toán tiến trình &   │
            │    hiển thị trực quan trên bản đồ)  │
            └─────────────────────────────────────┘
```

### 1. Nhân viên Điều phối Logistics nội bộ (Logistics Coordinator / Import Specialist)
* **Họ là ai:** Nhân viên thuộc phòng Mua hàng / Xuất nhập khẩu của công ty bạn (người phụ trách đơn hàng này).
* **Trách nhiệm:** Trực tiếp theo dõi tiến độ với nhà cung cấp (Apple), đơn vị giao nhận quốc tế (**Freight Forwarder / 3PL**) và đại lý hải quan.

### 2. Đơn vị Vận tải & Hãng tàu (Carrier / Freight Forwarder / 3PL)
* **Họ là ai:** Các hãng vận tải lớn như Maersk, MSC, DHL, FedEx, hoặc các công ty Forwarder dịch vụ.
* **Trách nhiệm:** Khi hàng qua các mốc quan trọng (đã bốc lên tàu, tàu đã nhổ neo, tàu cập cảng trung chuyển), hệ thống của họ phát hành các thông báo điện tử (EDI Status Message).

### 3. Hệ thống Kết nối Tự động (API & Dịch vụ Tracking Toàn cầu: AfterShip / MarineTraffic)
* **Họ là ai:** Nền tảng công nghệ trung gian kết nối trực tiếp với hơn 1.000 hãng tàu biển, hãng hàng không và định vị AIS hàng hải.
* **Trách nhiệm:** Tự động bắt tín hiệu vệ tinh và đẩy dữ liệu về ERPNext mà không cần bất kỳ ai phải gõ tay.

---

# 3. HỌ THỰC HIỆN CẬP NHẬT NHƯ THẾ NÀO? (CƠ CHẾ HOẠT ĐỘNG)

Hệ thống hỗ trợ song song **2 phương thức thực hiện**:

---

### 🔹 PHƯƠNG THỨC 1: TỰ ĐỘNG HOÀN TOÀN QUA API & WEBHOOK (Chuẩn 4.0)

Đây là cách các doanh nghiệp Logistics hiện đại vận hành để giải phóng sức lao động:

1. **Gắn Mã Vận đơn (Tracking Number / Bill of Lading):**
   * Khi nhà cung cấp tại Mỹ giao hàng cho hãng tàu, hãng tàu cấp một mã vận đơn (ví dụ: Số vận đơn đường biển `B/L: MAEU123456789` hoặc mã Air Waybill `AWB: 160-12345678`).
   * Nhân sự chỉ cần nhập mã này vào phiếu `Shipment Tracking` 1 lần duy nhất lúc tạo đơn.
2. **Hệ thống tự động kéo dữ liệu (Auto-sync):**
   * Trong module [`aftership.py`](file:///Users/capkimkhanh/Documents/DUT4_1/CSHTTT_Project/frappe-bench/apps/logistics_wizard/logistics_wizard/aftership.py), hệ thống có sẵn hàm kết nối API `sync_aftership`.
   * **Định kỳ (Cronjob nền):** Cứ mỗi 2 - 4 tiếng, máy chủ ERP tự động gửi mã vận đơn lên vệ tinh/hãng tàu để kiểm tra:
     * *Vệ tinh báo:* "Tàu vừa rời Cảng Long Beach vượt Thái Bình Dương" $\rightarrow$ Hệ thống tự động ghi nhận trạm `Pacific Ocean` và đổi trạng thái sang `In Transit`.
     * *Hải quan báo:* "Hàng đã dỡ tại Cảng Hải Phòng" $\rightarrow$ Hệ thống tự đổi trạng thái sang `Customs Clearance`.
   * **Nút bấm thủ công:** Trên giao diện phiếu `Shipment Tracking`, nhân viên có thể bấm nút **"Sync AfterShip"** bất kỳ lúc nào để cập nhật dữ liệu mới nhất tức thì.

---

### 🔹 PHƯƠNG THỨC 2: CẬP NHẬT BẰNG TAY TRÊN PHẦN MỀM ERP (Theo từng Mốc Chứng từ)

Trong trường hợp đi tàu rời, hàng chuyển tiếp nhiều chặng hoặc doanh nghiệp tự quản lý chuỗi cung ứng, nhân sự Logistics sẽ cập nhật theo các mốc chứng từ thực tế:

| Mốc thực tế ngoài đời | Chứng từ nhận được | Thao tác trên phần mềm ERPNext | Trạng thái hệ thống & Hiệu ứng Bản đồ |
| :--- | :--- | :--- | :--- |
| **1. Hàng xuất khỏi kho Mỹ** | Phiếu xuất kho / Dock Receipt | Mở `Shipment Tracking` $\rightarrow$ Chọn trạng thái **`Draft`** | **Tiến trình 0%:** Xe tải 🚚 màu cam đỗ tại Điểm **O** (Kho Apple Cupertino). |
| **2. Đã bốc lên Tàu/Máy bay** | Vận đơn B/L hoặc AWB chính thức | Chuyển trạng thái sang **`In Transit`** | **Tiến trình 55%:** Tự động đổi thành **Tàu biển 🚢** (hoặc Máy bay ✈️) di chuyển giữa biển Thái Bình Dương. |
| **3. Cập cảng VN & Làm hải quan** | Giấy báo hàng đến (Arrival Notice) + Tờ khai hải quan | Chuyển trạng thái sang **`Customs Clearance`** | **Tiến trình 85%:** Phương tiện chuyển thành **Xe tải 🚚** đứng tại Cảng Hải Phòng / Sân bay. |
| **4. Giao tới Kho Đà Nẵng** | Biên bản giao nhận hàng (POD) có chữ ký thủ kho | Chuyển trạng thái sang **`Delivered`** (hoặc tạo phiếu nhận hàng Purchase Receipt) | **Tiến trình 100%:** Xe tải container chạy tới Điểm **D** (Kho Cáp Kim Khánh), cờ đích hoàn thành! |

#### Cách nhân viên thao tác trực tiếp trên giao diện:
1. **Cách 1 (Qua Form nghiệp vụ):**
   * Vào thanh tìm kiếm gõ **Shipment Tracking** $\rightarrow$ Chọn mã vận đơn cần sửa $\rightarrow$ Bấm chọn dropdown trường **Status** $\rightarrow$ Bấm **Lưu (Save)**.
   * Nhân viên cũng có thể nhập thêm các dòng trạm vào bảng con **Transit Route** (ví dụ: ngày nào tàu ghé qua Cảng Busan, ngày nào qua eo biển Đài Loan) để biểu đồ hiển thị chi tiết hơn.
2. **Cách 2 (Thao tác nhanh ngay trên Widget Logistics Wizard):**
   * Ở bất kỳ màn hình nào trên ERPNext, nhân viên chỉ cần nhấp vào biểu tượng phao cứu sinh/xe tải ở góc phải dưới màn hình.
   * Danh sách đơn hàng sẽ hiện ra kèm nút chuyển trạng thái nhanh và hiển thị ngay lộ trình bản đồ vệ tinh tương ứng.

---

### 💡 Tóm lại:
Hệ thống được thiết kế theo nguyên lý **"Đơn giản cho người dùng, thông minh ở phía sau"**:
* Bạn có thể để hệ thống **tự động đồng bộ qua API** theo thời gian thực từ hãng tàu.
* Hoặc nhân viên xuất nhập khẩu chỉ cần làm một thao tác cực kỳ đơn giản là **chọn trạng thái tương ứng với mốc chứng từ** (`Draft` $\rightarrow$ `In Transit` $\rightarrow$ `Customs Clearance` $\rightarrow$ `Delivered`).
* Toàn bộ việc **vẽ đường bộ OSRM**, **vẽ luồng biển searoute**, **tính cự ly**, **biến đổi icon xe tải/tàu biển** và **tính phần trăm thanh tiến trình** đều do các thuật toán ngầm tự động thực hiện $100\%$, người dùng không cần phải đo vẽ thủ công!
