# Đề cập về vấn đề trong thiết kế một chess engine

Thiết kế chess engine là một bài toán phức tạp đòi hỏi sự tối ưu chặt chẽ về mặt cấu trúc dữ liệu và tư duy thuật toán. Thách thức lớn nhất chính là không gian tìm kiếm (search space) của một ván cờ. Bản thân một ván cờ có một search space khổng lồ (lên tới gần $10^{150}$ trạng thái) với thuật toán cơ bản phải chạy với độ phức tạp $O(b^d)$ (với $b \approx 40$ nhánh/lượt và $d$ là độ sâu).

Với vấn đề như vậy, mục tiêu cốt lõi của chúng ta là làm thế nào để lược bỏ (prune) tối đa không gian tìm kiếm dư thừa mà vẫn đảm bảo xét được những nhánh đi tiềm năng nhất ở độ sâu lớn nhất có thể trong giới hạn thời gian.

# Phương pháp luận

Để điều hướng trong không gian tìm kiếm khổng lồ của Cờ Tướng — với độ phức tạp cây trò chơi xấp xỉ $10^{150}$ — engine chuyển đổi từ cách tiếp cận vét cạn thô sơ sang một đồ thị tìm kiếm được tối ưu hóa cao độ. Kiến trúc này dựa trên ba kỹ thuật thuật toán được tích hợp chặt chẽ: sắp xếp nước đi động, bộ nhớ đệm hoán vị trạng thái, và tìm kiếm chọn lọc ổn định chân trời.

---

## Nâng cao Alpha-Beta thông qua sắp xếp nước đi tối ưu

Khung tìm kiếm lõi được xây dựng trên nền thuật toán cắt tỉa Alpha-Beta. Về mặt thống kê, một phép tìm kiếm minimax tiêu chuẩn có độ phức tạp thời gian $O(b^d)$, trong đó $b \approx 40$ là hệ số phân nhánh của Cờ Tướng và $d$ là độ sâu tính theo nửa lượt (ply). Trong điều kiện không tối ưu, sự tăng trưởng hàm mũ này giới hạn khả năng tính toán thời gian thực ở một tầm nhìn rất nông.

Như đã được chứng minh toán học bởi Knuth và Moore (1975), hiệu quả của cắt tỉa Alpha-Beta phụ thuộc nghiêm ngặt vào thứ tự đánh giá các nhánh. Nếu engine đánh giá nước đi tối ưu đầu tiên tại mọi node, không gian tìm kiếm sụp đổ về cận dưới lý thuyết:

$$O\left(b^{\lceil d/2 \rceil} + b^{\lfloor d/2 \rfloor} - 1\right) \approx O(b^{d/2})$$

Bằng cách giảm số mũ đi một nửa, việc sắp xếp nước đi hoàn hảo cho phép engine tăng gấp đôi độ sâu tìm kiếm trong cùng một ngân sách thời gian. Để xấp xỉ thứ tự sắp xếp lý tưởng này, engine triển khai một pipeline sắp xếp nước đi phân tầng, hiệu năng cao:

* **Hash Move:** Nước đi được lưu trong Bảng hoán vị (Transposition Table) từ vòng lặp tìm kiếm nông hơn trước đó được ưu tiên trên tất cả các nước đi khác.
* **Chọn lọc chiến thuật (MVV-LVA):** Các nước ăn quân và phong cấp được sắp xếp theo heuristic *Nạn nhân giá trị nhất - Kẻ tấn công giá trị thấp nhất* (Most Valuable Victim - Least Valuable Attacker), đảm bảo các thay đổi vật chất có tác động lớn được tính toán ngay lập tức nhằm kích hoạt cắt tỉa Beta nhanh chóng.
* **Heuristic nước đi yên tĩnh:** Các nước đi không ăn quân được sắp xếp động bằng *History Heuristic* (Schaeffer, 1989). Những nước đi trong lịch sử thường gây ra cắt tỉa Beta ở các nhánh khác của cây tìm kiếm được gán trọng số cao hơn, cho phép engine khai thác các mẫu cấu trúc xuyên suốt cây trò chơi mà không phát sinh chi phí tính toán dư thừa.

---

## Thu hẹp không gian trạng thái thông qua Bảng hoán vị (Transposition Table)

Mặc dù các biến thể trò chơi thường được mô hình hóa dưới dạng cây, một trò chơi tuần tự như Cờ Tướng về bản chất hoạt động như một Đồ thị có hướng không chu trình (DAG) do các hoán vị trạng thái (ví dụ: đạt đến cùng một thế cờ thông qua các trình tự nước đi đảo ngược). Nếu không có cơ chế lưu giữ trạng thái, quá trình tìm kiếm tiêu chuẩn thường xuyên đánh giá lại các đồ thị con giống hệt nhau, tạo ra sự dư thừa thuật toán khổng lồ.

Để ánh xạ cây trò chơi thành đồ thị, engine triển khai hệ thống bộ nhớ đệm Bảng hoán vị (TT) dựa trên các nguyên lý được Marsland và Campbell (1982) đề xuất.

> **Tìm kiếm trên cây vs. Bộ nhớ đệm đồ thị:**
> * **Tìm kiếm tiêu chuẩn:** `[Gốc] -> [A] -> [Trạng thái X]` và `[Gốc] -> [B] -> [Trạng thái X]` buộc engine phải đánh giá `[Trạng thái X]` hai lần.
> * **Tìm kiếm đồ thị:** Đường đi thứ hai trúng bộ nhớ đệm trong Bảng hoán vị, cắt tỉa toàn bộ cây con trùng lặp ngay lập tức.

### Thành phần Zobrist Hashing
Để thực hiện tra cứu bộ nhớ đệm trong thời gian hằng số $O(1)$, mỗi cấu hình bàn cờ riêng biệt cần được ánh xạ thành một định danh có tính phân bố đồng đều cao. Engine sử dụng *Zobrist Hashing* (Zobrist, 1970).

Tại thời điểm khởi tạo, một ma trận các số nguyên giả ngẫu nhiên 64-bit được sinh ra cho mọi tổ hợp loại quân, màu sắc và ô trên bàn cờ:

$$Z_{p, c, s} \quad \text{trong đó } p \in \text{Quân cờ}, \, c \in \text{Màu}, \, s \in [0, 89]$$

Khóa băm tổng hợp $\mathcal{H}$ cho bất kỳ trạng thái nào được tính toán và cập nhật gia tăng (incremental) trong quá trình tìm kiếm bằng phép toán XOR theo bit ($\oplus$):

$$\mathcal{H}_{\text{mới}} = \mathcal{H}_{\text{cũ}} \oplus Z_{p, c, s_{\text{gốc}}} \oplus Z_{p, c, s_{\text{đích}}}$$

Chiến lược cập nhật gia tăng này loại bỏ hoàn toàn nhu cầu quét lại toàn bộ bàn cờ $9 \times 10$ tại mỗi node, duy trì thông lượng vượt trội tính bằng số node trên giây (NPS).

### Ánh xạ bộ nhớ và lưu trữ node
Khi một node được đánh giá, dữ liệu của nó được nén vào một slot bộ nhớ đệm nhỏ gọn chứa: khóa Zobrist 64-bit, độ sâu tìm kiếm tuyệt đối, nước đi tốt nhất đã tính được, và cờ điểm số (Chính xác - Exact, Cận dưới/Fail-High - Lower Bound, hoặc Cận trên/Fail-Low - Upper Bound). Trong các vòng lặp tìm kiếm tiếp theo, nếu một trạng thái khớp với khóa Zobrist đã lưu ở độ sâu bằng hoặc lớn hơn, engine lập tức cắt tỉa toàn bộ cây con bằng cách trả về giá trị đã lưu, trực tiếp triệt tiêu độ phức tạp không gian trạng thái dư thừa.

---

## Khắc phục Hiệu ứng chân trời thông qua Quiescence Search

Một thuật toán tìm kiếm có độ sâu cố định ($d$) chắc chắn phải chịu *Hiệu ứng chân trời* (Horizon Effect) — một điểm mù nhận thức trong đó các sự kiện chiến thuật thảm khốc (chẳng hạn như một nước chiếu không thể chặn hoặc ăn mất quân lớn) xảy ra ở độ sâu $d+1$ bị che khuất hoàn toàn khỏi hàm đánh giá (Marsland, 1987).

Để đảm bảo tính ổn định chiến thuật, engine kết thúc tìm kiếm toàn diện tại độ sâu $d$ và khởi động một *Quiescence Search* có tính chọn lọc cao. Tuân theo mô hình thiết kế "Loại B" được Shannon (1950) đề xuất ban đầu, quiescence search bổ sung một phần mở rộng có độ sâu thay đổi, lọc tập nước đi xuống **chỉ còn các hành động chiến thuật bắt buộc** (ăn quân và phản hồi chiếu Tướng).

* **Bước 1:** Tìm kiếm toàn diện chạy đến giới hạn tiêu chuẩn (Độ sâu $D$). Độ phức tạp thời gian theo $O(b^d)$.
* **Bước 2:** Tìm kiếm chạm giới hạn độ sâu, chuyển sang chế độ Quiescence.
* **Bước 3:** Tập nước đi bị giới hạn chỉ còn các hành động chiến thuật. Độ phức tạp giảm xuống $O(b_{\text{chiến thuật}}^{d_{\text{mở rộng}}})$.
* **Bước 4:** Node đạt trạng thái yên tĩnh, ổn định và truyền điểm số ngược về gốc.

Thuật toán đánh giá các chuỗi chiến thuật này lặp đi lặp lại cho đến khi đạt được một trạng thái "yên tĩnh" (quiescent) ổn định. Bằng cách giới hạn hệ số phân nhánh trong phần mở rộng này chỉ ở các nước ăn quân chiến thuật ($b_{\text{chiến thuật}} \ll b$), engine thiết lập được một chỉ số cân bằng vật chất chính xác mà không kích hoạt sự bùng nổ hàm mũ của không gian tìm kiếm.
