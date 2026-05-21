# BÁO CÁO KỸ THUẬT: ITERATIVE DEEPENING SEARCH (IDS)
**File áp dụng:** `src/bots/engine/iterative_deepening.py`

---

## 1. Mô tả bài toán
Trong các hệ thống AI đánh cờ (Chess/Xiangqi Engine), thời gian để duyệt toàn bộ cây trò chơi tới một độ sâu cố định (ví dụ: `depth = 5`) là hoàn toàn **không thể đoán trước**. Ở những thế cờ đơn giản (tàn cuộc), việc tìm kiếm có thể chỉ mất `0.1` giây. Tuy nhiên, ở những thế cờ giằng co phức tạp (trung cuộc), hệ số phân nhánh tăng vọt, thời gian suy nghĩ có thể kéo dài lên tới `30` giây hoặc vài phút.

Điều này tạo ra hai vấn đề lớn:
1. **Vi phạm thời gian thi đấu:** Bot có thể bị xử thua nếu vượt quá thời gian suy nghĩ cho phép của một nước đi (ví dụ: giới hạn 1 giây/nước).
2. **Lãng phí thời gian:** Trong những thế cờ dễ, Bot hoàn toàn có thể tính sâu hơn (đến depth 7 hoặc 8) với lượng thời gian dư dả, nhưng vì bị "cứng" ở `depth=5`, nó lại dừng lại một cách lãng phí.

Yêu cầu đặt ra là phải xây dựng một cơ chế điều phối giúp thuật toán tìm kiếm (Negamax) hoạt động **linh hoạt theo thời gian thực** thay vì bị gò bó bởi một độ sâu tĩnh.

---

## 2. Phương pháp giải quyết (Iterative Deepening Search)
Để giải quyết bài toán trên, dự án sử dụng cơ chế **Sâu dần lặp lại (Iterative Deepening Search - IDS)**. 

Cách thức hoạt động:
*   **Tìm kiếm tăng dần:** Thay vì tìm thẳng tới `depth = N`, AI sẽ bắt đầu tìm kiếm ở `depth = 1`. Sau khi hoàn thành, nó tăng lên `depth = 2`, rồi `depth = 3`, và cứ tiếp tục như vậy.
*   **Kiểm tra thời gian liên tục:** Trước khi bắt đầu một độ sâu mới (hoặc trong lúc duyệt), hệ thống sẽ kiểm tra xem thời gian cho phép (ví dụ `1000ms`) đã hết chưa.
*   **Fallback an toàn:** Nếu thời gian hết khi đang tính dang dở ở `depth = N`, hệ thống sẽ lập tức hủy bỏ kết quả tính toán của `depth = N` và **trả về nước đi tốt nhất đã tìm thấy ở `depth = N-1`**.

Sự kết hợp tối ưu:
* Mặc dù có vẻ như việc duyệt lại từ đầu (1, 2, 3...) là lãng phí, nhưng thực chất nó lại **làm AI chạy nhanh hơn**. Nước đi tốt nhất tìm thấy ở `depth = N-1` sẽ được đưa vào làm nước đi thử đầu tiên (First move to try) ở `depth = N` thông qua `MoveSorter`. Kết hợp với Alpha-Beta Pruning, điều này giúp AI lập tức cắt tỉa được hàng triệu nhánh sai lầm, khiến tốc độ duyệt ở độ sâu tiếp theo tăng gấp nhiều lần.

---

## 3. Kết quả
Module `iterative_deepening.py` đã giải quyết triệt để bài toán quản lý thời gian của Bot với các kết quả cụ thể:
- **Hàm `search_with_time_limit`:** Đảm bảo Bot luôn đưa ra quyết định tối ưu nhất đúng trong khoảng thời gian quy định (ví dụ: đúng 1 giây), không bao giờ lo bị "Time out" trong các đấu trường (Arena). Ở những thế cờ dễ, Bot tự động đào sâu hơn bình thường.
- **Hàm `search_with_depth_limit`:** Giữ nguyên khả năng duyệt tới một độ sâu cố định (để benchmark hoặc debug), nhưng tốc độ nhanh hơn hẳn thuật toán duyệt thông thường nhờ việc kế thừa Move Ordering từ các độ sâu thấp.
- Mang lại tính ổn định cực cao cho hệ thống AI trong chế độ Người đánh với Máy.
