# BÁO CÁO KIẾN TRÚC VÀ TÍNH NĂNG: CỜ TƯỚNG ENGINE (XIANGQI ENGINE)

## 1. Mô tả bài toán
Dự án "Xiangqi Engine" hướng đến việc giải quyết bài toán cốt lõi trong lĩnh vực Trí tuệ Nhân tạo đối với các trò chơi chiến thuật có tổng bằng không (Zero-sum games): xây dựng một hệ thống có khả năng tự động tính toán, đánh giá và lựa chọn nước đi tối ưu trong không gian trạng thái khổng lồ của Cờ Tướng. 

Bài toán đặt ra yêu cầu hệ thống không chỉ phải mô phỏng chính xác tuyệt đối bộ quy tắc phức tạp của Cờ Tướng (như luật cản chân Mã, chặn mắt Tượng, không được lộ mặt Tướng), mà còn phải xử lý bài toán tối ưu hóa tài nguyên phần cứng. Hệ thống cần có năng lực duyệt qua hàng chục ngàn đến hàng trăm ngàn thế cờ tiềm năng trong một khoảng thời gian giới hạn nghiêm ngặt (Time Limit), từ đó ra quyết định chiến thuật để đối đầu trực tiếp với con người hoặc thi đấu độc lập với các hệ thống AI khác.

## 2. Bố cục dự án (Project Structure)
Mã nguồn của hệ thống được chia thành 4 phân hệ (module) chính, hoạt động độc lập và giao tiếp thông qua các interface rõ ràng:

```text
src/
├── main.py               [1. Phân hệ Giao diện người dùng (Entry Point)]
├── core/                 [2. Phân hệ Động cơ Luật (Rules Engine)]
├── bots/                 [3. Phân hệ Trí tuệ Nhân tạo (Algorithms)]
└── arena/                [4. Phân hệ Đấu trường & Giám sát (Arena)]
```

### Phân hệ 1: `core/` (Động cơ Luật và Biểu diễn dữ liệu)
Đây là phân hệ nền tảng của toàn bộ hệ thống, chịu trách nhiệm quản lý cấu trúc dữ liệu và đảm bảo tính đúng đắn của luật cờ tướng. Phân hệ này hoạt động độc lập, không phụ thuộc vào logic của AI hay giao diện:
- **`board.py`:** Quản lý trạng thái bàn cờ thông qua mảng một chiều (90 phần tử) nhằm tối ưu bộ nhớ và tốc độ truy xuất. Lớp `Board` cung cấp các phương thức cốt lõi như thực thi (make_move) và hoàn tác (undo_move) nước đi, đồng thời hỗ trợ nạp và xuất cấu hình bàn cờ dưới định dạng FEN (Forsyth-Edwards Notation).
- **`move.py` & `pieces.py`:** Biểu diễn các quân cờ và mã hóa/giải mã các nước đi (từ tọa độ mảng sang chuỗi UCI chuẩn quốc tế và ngược lại).
- **`move_generator.py`:** Bộ sinh nước đi hợp lệ. Đảm nhiệm việc tính toán và trả về toàn bộ nước đi có thể thực hiện trên bàn cờ cho tất cả các loại quân, tuân thủ các ràng buộc vật lý của cờ tướng (như Sĩ/Tướng không rời khỏi cung, Mã bị cản chân, Tượng không qua sông).
- **`rules.py`:** Bộ quy tắc kiểm tra tình trạng ván cờ. Đánh giá tính hợp lệ cuối cùng của nước đi, phát hiện các trạng thái chiếu tướng (check), chiếu bí (checkmate), hết nước đi (stalemate), và xác định các điều kiện hòa cờ (lặp nước, luật 60 nước). Phân hệ này cũng tích hợp cơ chế ngăn chặn nước đi vi phạm quy tắc "lộ mặt Tướng" (Flying General).
- **`zobrist.py`:** Triển khai thuật toán Zobrist Hashing, tạo ra mã định danh 64-bit duy nhất cho từng trạng thái bàn cờ. Cơ chế này hỗ trợ kiểm tra lặp nước và tối ưu hóa bộ nhớ đệm ở phân hệ trí tuệ nhân tạo.

### Phân hệ 2: `bots/` (Trí tuệ Nhân tạo)
Phân hệ đảm nhiệm vai trò ra quyết định chiến thuật. Thiết kế tuân theo mẫu Chiến lược (Strategy Pattern), nhận đầu vào là đối tượng `Board` và trả về nước đi tối ưu. Hệ thống bao gồm 2 thành phần chính:

1. **Lớp Giao tiếp (Wrapper - `bot.py`):** 
   - Định nghĩa lớp cơ sở `Bot` với phương thức trừu tượng `get_move(board)`.
   - Cài đặt đa dạng các loại AI để so sánh và kiểm thử: `RandomBot` (chọn nước ngẫu nhiên hợp lệ), `GreedyBot` (ưu tiên tuyệt đối việc thu thập quân có giá trị cao nhất), và `NegamaxBot` (AI phân tích sâu).
   - Lớp `BotManager` đóng vai trò Factory giúp khởi tạo động các thực thể Bot dựa trên cấu hình môi trường.

2. **Khối Engine Lõi (`bots/engine/`):** Thành phần xử lý tính toán chuyên sâu của `NegamaxBot`, bao gồm các module tối ưu hóa chuyên biệt:
   - **`algorithm.py`:** Triển khai thuật toán Negamax kết hợp Cắt tỉa Alpha-Beta. Đây là module định tuyến chính để duyệt không gian trạng thái. Thuật toán được tối ưu thời gian chạy bằng các kỹ thuật *Null Move Pruning*, *Late Move Reductions (LMR)* và *Futility Pruning*.
   - **`linear_evaluator.py`:** Hàm đánh giá trạng thái tĩnh (Static Evaluator). Thay vì duyệt sâu thêm, module này trả về điểm số của một thế cờ cụ thể dựa trên: chênh lệch lực lượng, cấu trúc Tốt, độ cơ động (mobility) của các quân chủ lực, và phân tích cấu trúc an toàn quanh khu vực cung Tướng (tropism, số quân phòng ngự).
   - **`iterative_deepening.py`:** Kỹ thuật tìm kiếm lặp sâu dần (Iterative Deepening Search). Thay vì tìm kiếm trực tiếp tại độ sâu `D`, thuật toán duyệt qua các độ sâu từ `1` đến `D`. Cơ chế này giải quyết bài toán thi đấu thời gian thực: đảm bảo thuật toán có thể trả về một nước đi hợp lệ và tối ưu nhất có thể bất cứ khi nào giới hạn thời gian (Time Limit) bị vượt qua.
   - **`move_ordering.py`:** Kỹ thuật sắp xếp nước đi. Trước khi các nhánh được duyệt bởi Alpha-Beta, các nước đi được sắp xếp giảm dần độ ưu tiên: Nước đi ăn quân (MVV-LVA), nước đi sát thủ (Killer Moves) và các nước có độ hiệu quả cao trong lịch sử (History Heuristic). Phân bố tốt giúp tỷ lệ cắt tỉa của Alpha-Beta tăng lên đáng kể.
   - **`transposition_table.py`:** Quản lý bảng hoán vị (Transposition Table) hay còn gọi là Cache bộ nhớ. Sử dụng hàm Zobrist hash từ phân hệ `core/` để lưu trữ và truy xuất kết quả (điểm số, loại cận) của các trạng thái đã được tính toán, loại bỏ hoàn toàn sự lãng phí tài nguyên do tính lại các nhánh đồ thị trùng lặp.
   - **`quiescence_search.py`:** Tìm kiếm tĩnh. Module khắc phục "hiệu ứng chân trời" (Horizon Effect) bằng cách mở rộng thêm cây tìm kiếm vượt qua giới hạn độ sâu ban đầu đối với những nhánh đang xảy ra biến động lực lượng (có thao tác ăn quân), giúp tránh các sai lầm chiến thuật do việc đánh giá bị ngắt quãng giữa chừng.
   - **`opening_book.py`:** Cơ sở dữ liệu khai cuộc, cung cấp các chuỗi nước đi tiêu chuẩn đầu ván với thời gian phản hồi tức thời.

### Phân hệ 3: `arena/` (Đấu trường và Giám sát thi đấu)
Phân hệ quản lý toàn bộ vòng đời của một ván đấu giữa hai thực thể độc lập:
- **`game.py` (Lớp Game):** Đóng vai trò là hệ thống điều phối vòng lặp trò chơi (game loop). Nó khởi tạo với hai đối tượng giao diện `Bot` hoặc `Player`, yêu cầu luân phiên các hành động `get_move()`. 
- **Cơ chế xử lý lỗi và tính toàn vẹn:** `Game` thực hiện kiểm định nghiêm ngặt kết quả đầu ra của Bot. Các ngoại lệ (runtime exceptions), vượt thời gian suy nghĩ (timeout) hoặc sinh nước đi bất hợp pháp (illegal move) đều sẽ kích hoạt cơ chế chấm dứt ván đấu lập tức với kết quả xử thua cho bên vi phạm.
- **`logger.py` và Trích xuất PGN:** Module ghi nhận dữ liệu hệ thống chuyên sâu. Toàn bộ diễn biến ván cờ, thời gian phản hồi, trạng thái kết thúc đều được ghi log phục vụ quá trình debug. Lớp `Game` tự động chuyển đổi định dạng và xuất lịch sử ván cờ theo tiêu chuẩn PGN (Portable Game Notation).

### Phân hệ 4: `main.py` (Giao diện người dùng)
Điểm neo khởi động của ứng dụng, chịu trách nhiệm xử lý luồng tương tác người dùng:
- Hiển thị giao diện dòng lệnh trực quan trên nền Terminal với hỗ trợ màu sắc (thông qua thư viện `colorama`), ánh xạ lưới tọa độ bàn cờ với hệ ký tự đặc trưng.
- Tiếp nhận tham số cấu hình (chế độ Bot đấu Bot, Người đấu Bot, lựa chọn phe Đỏ/Đen) và liên kết ba phân hệ `core/`, `bots/` và `arena/` với nhau.
- Cung cấp tính năng trợ giúp hiển thị danh sách các nước đi hợp lệ theo định dạng UCI, đưa ra cảnh báo hệ thống (như Tướng đang bị chiếu) để hỗ trợ quá trình quyết định của người dùng.

---

## 3. Luồng dữ liệu (Data Flow) và Cơ chế liên kết phân hệ

Tính gắn kết và độc lập của kiến trúc được thể hiện rõ qua luồng thực thi chuẩn khi người dùng khởi tạo một ván cờ từ `main.py`:

1. **Giai đoạn Khởi tạo (Initialization Phase):**
   - Người dùng khởi động `main.py` và lựa chọn chế độ chơi.
   - Ứng dụng khởi tạo lớp trạng thái `Board` (từ `core/`).
   - Khởi tạo thực thể AI (`NegamaxBot` từ `bots/`) và thực thể quản lý đầu vào bàn phím cho Người chơi.
   - Đưa cả 3 thành phần này vào module quản lý luồng `Game` (từ `arena/`) để bắt đầu quá trình giám sát.

2. **Giai đoạn Vòng lặp ván cờ (Game Loop Phase):**
   - Tại mỗi lượt (ply), vòng lặp kiểm tra quy tắc kết thúc (như chiếu bí, lặp nước) thông qua `rules.py`.
   - Lệnh lấy nước đi được kích hoạt (`get_move()`). Đối với `NegamaxBot`, tiến trình này bao gồm việc khởi chạy hàm `algorithm.py`.
   - Trong quá trình đánh giá các nhánh quyết định, AI liên tục sử dụng `move_generator.py` để mô phỏng tương lai và `linear_evaluator.py` để xác định mức độ tối ưu của lá đồ thị (leaf node).

3. **Giai đoạn Cập nhật và Lưu trữ (State Update & Logging Phase):**
   - Trạng thái `Board` được cập nhật qua thao tác `make_move()`. Khóa Zobrist mới được thiết lập.
   - Giao diện cập nhật hiển thị, hệ thống `arena/` nhận nước đi mới, ghi nhận qua `logger.py` và tính toán lại giới hạn thời gian.
   - Vòng lặp tiếp tục cho tới khi điều kiện kết thúc được kích hoạt. Trình quản lý xuất dữ liệu `.pgn` để lưu trữ.

## 4. Kiểm định Chất lượng (Quality Assurance & Testing)
Độ tin cậy của ứng dụng được duy trì bởi hệ thống Unit Tests toàn diện (sử dụng framework `pytest`):
- Sở hữu 118 bộ test (test cases) chạy tự động, tập trung vào tính nguyên vẹn của từng phân hệ.
- **Mô phỏng biệt lập (Isolated Component Testing):** Phân hệ `core/` được đánh giá bằng công cụ đếm nút đồ thị đệ quy (Perft tests), đối chiếu trực tiếp với kết quả chuẩn của các hệ thống cờ tướng quốc tế để khẳng định không có sai sót trong sinh nước đi. Phân hệ `bots/` được kiểm tra thông qua việc giả lập các thế cờ đặc biệt, đòi hỏi AI phải bắt buộc tìm ra các trình tự chiếu bí cục bộ (forced mate).

## 5. Kết quả đạt được
Dự án "Xiangqi Engine" đã hoàn thiện và đáp ứng xuất sắc các tiêu chí về cả mặt thuật toán lẫn Kỹ thuật Phần mềm (Software Engineering). Cụ thể, các kết quả nổi bật bao gồm:

1. **Xây dựng thành công Động cơ Luật (Rules Engine) độc lập:** Xử lý chính xác 100% các tình huống phức tạp của Cờ Tướng mà không phụ thuộc vào bất kỳ thư viện bên thứ ba nào.
2. **Triển khai AI thi đấu mạnh mẽ:** Hoàn thiện Bot Negamax với tốc độ tìm kiếm ổn định nhờ sự kết hợp tối ưu giữa Cắt tỉa Alpha-Beta, Tìm kiếm lặp sâu dần (IDS), và Bảng băm bộ nhớ (Transposition Table). AI đã chứng minh được khả năng ngăn chặn sai lầm nhờ tích hợp Tìm kiếm tĩnh (Quiescence Search).
3. **Phát triển môi trường thi đấu (Arena) tiêu chuẩn:** Hệ thống có khả năng tự động giám sát ván cờ, bắt lỗi ngoại lệ, xử lý quá giờ và xuất biên bản thi đấu chuẩn quốc tế PGN, sẵn sàng để tích hợp với các phần mềm đồ họa bên ngoài.
4. **Đạt độ tin cậy cao:** Vượt qua toàn bộ 118 bộ kiểm thử (test cases), đặc biệt là các bài kiểm tra đếm nút (Perft tests) nghiêm ngặt để đảm bảo tính toàn vẹn của hệ thống.
