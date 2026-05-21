# BÁO CÁO DỰ ÁN: AI CỜ TƯỚNG (XIANGQI ENGINE)

## 1. Mô tả bài toán
Dự án này tập trung vào việc xây dựng một Trí tuệ nhân tạo (AI) có khả năng chơi Cờ Tướng (Xiangqi) ở trình độ tốt, có thể tương tác trực tiếp với con người hoặc thi đấu tự động với các AI khác.

Bài toán cốt lõi trong cờ tướng là không gian trạng thái cực kỳ khổng lồ (với hệ số phân nhánh trung bình khoảng 40 nước đi mỗi lượt). Việc duyệt toàn bộ cây trò chơi là bất khả thi. Do đó, yêu cầu đặt ra là phải xây dựng được một "Chess Engine" có khả năng:
- Lựa chọn nước đi tối ưu trong một giới hạn thời gian hoặc độ sâu (Depth) nhất định.
- Tối ưu hóa hiệu năng thuật toán tìm kiếm để duy trì tốc độ suy nghĩ.
- Có khả năng nhìn xa để tránh các bẫy chiến thuật hoặc hiện tượng "tầm nhìn hạn hẹp" (Horizon Effect).
- Sở hữu tri thức khai cuộc để chơi chuẩn xác từ những nước đầu tiên.

---

## 2. Phương pháp giải quyết
Để xây dựng một AI Cờ Tướng mạnh mẽ, dự án đã áp dụng một tổ hợp các phương pháp và thuật toán kinh điển trong lĩnh vực Game AI:

*   **Thuật toán tìm kiếm cốt lõi:**
    *   **Negamax:** Dùng để duyệt cây trò chơi, tìm ra nước cờ tối ưu hóa lợi ích của bản thân và thu hẹp lợi ích của đối thủ. Negamax là dạng tổng quát của Minimax, giúp đơn giản hóa mã nguồn bằng cách loại bỏ sự phân biệt giữa nước đi tối đa hóa và tối thiểu hóa.
    *   **Alpha-Beta Pruning (Cắt tỉa Alpha-Beta):** Kỹ thuật loại bỏ các nhánh tìm kiếm không tiềm năng, giúp tăng tốc độ tìm kiếm lên đáng kể so với Negamax thuần túy.

*   **Quản lý độ sâu và thời gian:**
    *   **Iterative Deepening Search (IDS):** AI sẽ tìm kiếm mở rộng dần từ độ sâu 1, 2, 3... cho đến khi hết thời gian cho phép. Điều này giúp AI luôn có sẵn một nước đi tốt nhất để trả về bất kể giới hạn thời gian là bao nhiêu.

*   **Tối ưu hóa Cắt tỉa (Move Ordering):**
    *   Sắp xếp các nước đi tiềm năng lên đánh giá trước để tăng xác suất cắt tỉa Alpha-Beta.
    *   Sử dụng **Killer Moves**, **History Heuristic** và kỹ thuật **MVV-LVA** (Most Valuable Victim - Least Valuable Attacker) ưu tiên các nước ăn quân có lời.

*   **Khắc phục Hiện tượng Chân trời (Horizon Effect):**
    *   Tích hợp **Quiescence Search (Tìm kiếm tĩnh)** ở các nút lá (leaf nodes). Thay vì dừng lại đột ngột ở một độ sâu cố định, AI sẽ tiếp tục đào sâu các nhánh liên quan đến "ăn quân" cho đến khi trạng thái bàn cờ trở nên tĩnh lặng (không còn các pha trao đổi quân). Điều này giúp AI không bị lừa mất quân ngớ ngẩn.

*   **Lưu trữ và tái sử dụng tính toán (Transposition Table):**
    *   Sử dụng **Zobrist Hashing** để băm (hash) trạng thái bàn cờ thành các mã định danh duy nhất (64-bit integer). Các thế cờ đã được tính toán sẽ được lưu vào Bảng băm (TT Table). Khi gặp lại thế cờ cũ ở một nhánh khác, AI chỉ cần lôi kết quả ra dùng mà không cần duyệt lại cây từ đầu.

*   **Tri thức Khai cuộc (Opening Book):**
    *   Lập trình sẵn các thế cờ khai cuộc kinh điển (Pháo đầu, Tiên nhân chỉ lộ, Khởi mã, Phi tượng cuộc, Thuận/Nghịch pháo...). Ở những nước đầu tiên, AI truy xuất dữ liệu từ Zobrist Hash để đánh ngay lập tức các nước đi chuẩn mực thế giới với thời gian phản hồi 0 giây.

---

## 3. Kết quả đạt được
- **Hệ thống chơi cờ đa dạng:** Đã hoàn thiện chế độ Người đánh với Máy (`vs_bot`) và Máy tự đấu với Máy trong Đấu trường (`bot_vs_bot` / `arena`).
- **Hiệu năng:** Tốc độ suy nghĩ của Bot ổn định ở độ sâu (Depth) 3 và 4 nhờ các thuật toán cắt tỉa. Việc thêm Quiescence Search giúp AI thông minh hơn hẳn trong các pha đổi quân phức tạp.
- **Tính năng phụ trợ chuyên nghiệp:** 
  - Tự động ghi lại thời gian suy nghĩ (Time Logging).
  - Khả năng xuất lịch sử ván đấu theo chuẩn quốc tế **PGN** (Portable Game Notation) ở chế độ Arena, cho phép đưa vào các phần mềm GUI để phân tích lại sau ván đấu.
- **Sẵn sàng thi đấu:** AI có thể chơi mượt mà với những khai cuộc đa dạng, không bị rập khuôn và phản xạ ngay lập tức ở giai đoạn mở màn.
