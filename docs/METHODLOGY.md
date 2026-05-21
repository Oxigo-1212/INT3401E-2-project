# Đề cập về vấn đề trong thiết kế một chess engine

Thiết kế chess engine là một bài toán phức tạp đòi hỏi sự tối ưu chặt chẽ về mặt cấu trúc dữ liệu và tư duy thuật toán. Thách thức lớn nhất chính là không gian tìm kiếm (search space) của một ván cờ. Bản thân một ván cờ có một search space khổng lồ (lên tới gần $10^{150}$ trạng thái) với thuật toán cơ bản phải chạy với độ phức tạp $O(b^d)$ (với $b \approx 40$ nhánh/lượt và $d$ là độ sâu).

Với vấn đề như vậy, mục tiêu cốt lõi của chúng ta là làm thế nào để lược bỏ (prune) tối đa không gian tìm kiếm dư thừa mà vẫn đảm bảo xét được những nhánh đi tiềm năng nhất ở độ sâu lớn nhất có thể trong giới hạn thời gian.

# Phương pháp luận

Để điều hướng trong không gian tìm kiếm khổng lồ của Cờ Tướng — với độ phức tạp cây trò chơi xấp xỉ $10^{150}$ — engine chuyển đổi từ cách tiếp cận vét cạn thô sơ sang một đồ thị tìm kiếm được tối ưu hóa cao độ. Kiến trúc này tích hợp chặt chẽ nhiều kỹ thuật thuật toán: sắp xếp nước đi động bốn tầng (hash move, MVV-LVA, killer heuristic, history heuristic), bộ nhớ đệm hoán vị trạng thái qua Zobrist hashing, tìm kiếm chọn lọc quiescence để ổn định chân trời, ba kỹ thuật cắt tỉa (Null-Move, LMR, Futility), tìm kiếm sâu dần với cửa sổ nguyện vọng (aspiration windows), và hàm đánh giá nội suy pha trò chơi (tapered evaluation).

---

## Nâng cao Alpha-Beta thông qua sắp xếp nước đi tối ưu

Khung tìm kiếm lõi được xây dựng trên nền thuật toán cắt tỉa Alpha-Beta. Về mặt thống kê, một phép tìm kiếm negamax tiêu chuẩn có độ phức tạp thời gian $O(b^d)$, trong đó $b \approx 40$ là hệ số phân nhánh của Cờ Tướng và $d$ là độ sâu tính theo nửa lượt (ply). Trong điều kiện không tối ưu, sự tăng trưởng hàm mũ này giới hạn khả năng tính toán thời gian thực ở một tầm nhìn rất nông.

Như đã được chứng minh toán học bởi Knuth và Moore (1975), hiệu quả của cắt tỉa Alpha-Beta phụ thuộc nghiêm ngặt vào thứ tự đánh giá các nhánh. Nếu engine đánh giá nước đi tối ưu đầu tiên tại mọi node, không gian tìm kiếm sụp đổ về cận dưới lý thuyết:

$$O\left(b^{\lceil d/2 \rceil} + b^{\lfloor d/2 \rfloor} - 1\right) \approx O(b^{d/2})$$

Bằng cách giảm số mũ đi một nửa, việc sắp xếp nước đi hoàn hảo cho phép engine tăng gấp đôi độ sâu tìm kiếm trong cùng một ngân sách thời gian. Để xấp xỉ thứ tự sắp xếp lý tưởng này, engine triển khai một pipeline sắp xếp nước đi phân tầng, hiệu năng cao:

* **Hash Move:** Nước đi được lưu trong Bảng hoán vị (Transposition Table) từ vòng lặp tìm kiếm nông hơn trước đó được ưu tiên trên tất cả các nước đi khác.
* **Chọn lọc chiến thuật (MVV-LVA):** Các nước ăn quân và phong cấp được sắp xếp theo heuristic *Nạn nhân giá trị nhất - Kẻ tấn công giá trị thấp nhất* (Most Valuable Victim - Least Valuable Attacker), đảm bảo các thay đổi vật chất có tác động lớn được tính toán ngay lập tức nhằm kích hoạt cắt tỉa Beta nhanh chóng.
* **Heuristic nước đi yên tĩnh:** Các nước đi không ăn quân được sắp xếp động bằng *History Heuristic* (Schaeffer, 1989). Những nước đi trong lịch sử thường gây ra cắt tỉa Beta ở các nhánh khác của cây tìm kiếm được gán trọng số cao hơn, cho phép engine khai thác các mẫu cấu trúc xuyên suốt cây trò chơi mà không phát sinh chi phí tính toán dư thừa.
* **Killer Move Heuristic:** Hai nước đi gây cắt tỉa Beta gần đây nhất ở mỗi độ sâu ply được lưu vào bộ nhớ killer hai khe (Akl & Newborn, 1977). Khi gặp lại ở cùng độ sâu ply, các nước killer được ưu tiên ngay sau nước ăn quân, tránh phải tính toán lại toàn bộ tập nước đi yên tĩnh trong khi vẫn khai thác được mẫu chiến thuật cục bộ.

---

## Thu hẹp không gian trạng thái thông qua Bảng hoán vị (Transposition Table)

Mặc dù các biến thể trò chơi thường được mô hình hóa dưới dạng cây, một trò chơi tuần tự như Cờ Tướng về bản chất hoạt động như một Đồ thị có hướng không chu trình (DAG) do các hoán vị trạng thái (ví dụ: đạt đến cùng một thế cờ thông qua các trình tự nước đi đảo ngược). Nếu không có cơ chế lưu giữ trạng thái, quá trình tìm kiếm tiêu chuẩn thường xuyên đánh giá lại các đồ thị con giống hệt nhau, tạo ra sự dư thừa thuật toán khổng lồ.

Để ánh xạ cây trò chơi thành đồ thị, engine triển khai hệ thống bộ nhớ đệm Bảng hoán vị (TT) dựa trên các nguyên lý được Marsland và Campbell (1982) đề xuất.

> **Tìm kiếm trên cây vs. Bộ nhớ đệm đồ thị:**
> * **Tìm kiếm tiêu chuẩn:** `[Gốc] -> [A] -> [Trạng thái X]` và `[Gốc] -> [B] -> [Trạng thái X]` buộc engine phải đánh giá `[Trạng thái X]` hai lần.
> * **Tìm kiếm đồ thị:** Đường đi thứ hai trúng bộ nhớ đệm trong Bảng hoán vị, cắt tỉa toàn bộ cây con trùng lặp ngay lập tức.

### Thành phần Zobrist Hashing
Để thực hiện tra cứu bộ nhớ đệm trong thời gian hằng số $O(1)$, mỗi cấu hình bàn cờ riêng biệt cần được ánh xạ thành một định danh có tính phân bố đồng đều cao. Engine sử dụng *Zobrist Hashing* (Zobrist, 1970).

Tại thời điểm khởi tạo, một ma trận các số nguyên giả ngẫu nhiên 64-bit được sinh ra cho mọi tổ hợp quân cờ và ô trên bàn cờ:

$$Z_{p, s} \quad \text{trong đó } p \in \{\text{K, A, E, H, R, C, P, k, a, e, h, r, c, p}\}, \; s \in [0, 89]$$

và một khóa riêng cho lượt đi:

$$Z_{\text{side}} \in \{0, 1\}^{64}$$

Khóa băm tổng hợp $\mathcal{H}$ cho bất kỳ trạng thái nào được tính toán và cập nhật gia tăng (incremental) trong quá trình tìm kiếm bằng phép toán XOR theo bit ($\oplus$). Với quân cờ $p$ di chuyển từ ô $a$ sang ô $b$:

$$\mathcal{H}_{\text{mới}} = \mathcal{H}_{\text{cũ}} \oplus Z_{p, a} \oplus Z_{p, b} \oplus Z_{\text{side}} \oplus \begin{cases} Z_{\pi(b), b} & \text{nếu } \pi(b) \neq \epsilon \\ 0 & \text{nếu } \pi(b) = \epsilon \end{cases}$$

trong đó $\pi(b)$ là quân cờ tại ô đích (nếu có), $\epsilon$ ký hiệu ô trống. Khi ô đích trống ($\pi(b) = \epsilon$), số hạng XOR bằng $0$ và triệt tiêu (do $x \oplus 0 = x$).

Chiến lược cập nhật gia tăng này loại bỏ hoàn toàn nhu cầu quét lại toàn bộ bàn cờ $9 \times 10$ tại mỗi node, duy trì thông lượng vượt trội tính bằng số node trên giây (NPS).

### Ánh xạ bộ nhớ và lưu trữ node
Khi một node được đánh giá, dữ liệu của nó được lưu vào bảng chuyển vị dưới dạng `TT_Entry` gồm 5 trường:
- **key** ($k$): khóa Zobrist 64-bit dùng để xác thực thế cờ
- **depth** ($d_e$): độ sâu tìm kiếm khi lưu
- **score** ($s_e$): điểm số minimax tính được
- **flag** ($f_e$): cờ hiệu phân loại — EXACT (0), LOWERBOUND (1), UPPERBOUND (2)
- `best_move` ($m_e$): nước đi tốt nhất tìm được

Trong các vòng lặp tìm kiếm tiếp theo, khi truy xuất entry tại chỉ mục $\text{index} = k \bmod N$, engine kiểm tra hai điều kiện:

1. **Xác thực khóa:** $k_e = k$ (entry có cùng khóa Zobrist với thế cờ hiện tại)
2. **Tính hữu dụng:** $d_e \ge d$ và một trong ba trường hợp:
   - $f_e = \text{EXACT}$: luôn hữu dụng
   - $f_e = \text{LOWERBOUND} \land s_e \ge \beta$: cận dưới đủ cao để gây cắt
   - $f_e = \text{UPPERBOUND} \land s_e \le \alpha$: cận trên đủ thấp để gây cắt

Nếu entry hữu dụng, engine áp dụng vào cửa sổ tìm kiếm:
- **EXACT:** trả về $s_e$ ngay lập tức, cắt toàn bộ cây con
- **LOWERBOUND:** $\alpha \gets \max(\alpha, s_e)$ — thu hẹp cận dưới
- **UPPERBOUND:** $\beta \gets \min(\beta, s_e)$ — thu hẹp cận trên

Nếu $\alpha \ge \beta$ sau khi điều chỉnh, cửa sổ đóng lại và engine trả về $s_e$, cắt tỉa cây con. Cơ chế này giúp triệt tiêu độ phức tạp không gian trạng thái dư thừa khi nhiều đường đi khác nhau hội tụ về cùng một thế cờ.

---

## Khắc phục Hiệu ứng chân trời thông qua Quiescence Search

Một thuật toán tìm kiếm có độ sâu cố định ($d$) chắc chắn phải chịu *Hiệu ứng chân trời* (Horizon Effect) — một điểm mù nhận thức trong đó các sự kiện chiến thuật thảm khốc (chẳng hạn như một nước chiếu không thể chặn hoặc ăn mất quân lớn) xảy ra ở độ sâu $d+1$ bị che khuất hoàn toàn khỏi hàm đánh giá (Marsland, 1987).

Để đảm bảo tính ổn định chiến thuật, engine kết thúc tìm kiếm toàn diện tại độ sâu $d$ và khởi động một *Quiescence Search* có tính chọn lọc cao. Tuân theo mô hình thiết kế "Loại B" được Shannon (1950) đề xuất ban đầu, quiescence search bổ sung một phần mở rộng có độ sâu giới hạn ($Q_{\text{max}} = 4$), lọc tập nước đi xuống **chỉ còn các nước ăn quân** (captures). Các nước đi không ăn quân và phản hồi chiếu Tướng không được sinh ra trong giai đoạn này.

* **Bước 1:** Tìm kiếm toàn diện chạy đến giới hạn tiêu chuẩn (Độ sâu $D$). Độ phức tạp thời gian theo $O(b^d)$.
* **Bước 2:** Tìm kiếm chạm giới hạn độ sâu, chuyển sang chế độ Quiescence.
* **Bước 3:** Tập nước đi bị giới hạn chỉ còn các nước ăn quân ($b_{\text{ăn}} \ll b$). Độ sâu mở rộng bị chặn trên tại $Q_{\text{max}} = 4$.
* **Bước 4:** Node đạt trạng thái yên tĩnh, ổn định và truyền điểm số ngược về gốc.

Thuật toán đánh giá các chuỗi chiến thuật này lặp đi lặp lại cho đến khi đạt được một trạng thái "yên tĩnh" (quiescent) ổn định. Bằng cách giới hạn hệ số phân nhánh trong phần mở rộng này chỉ ở các nước ăn quân chiến thuật ($b_{\text{chiến thuật}} \ll b$), engine thiết lập được một chỉ số cân bằng vật chất chính xác mà không kích hoạt sự bùng nổ hàm mũ của không gian tìm kiếm.

---

## Lược bỏ không gian tìm kiếm thông qua Null-Move, LMR, và Futility Pruning

Bên cạnh việc tối ưu thứ tự nước đi và tránh trùng lặp trạng thái, engine triển khai ba kỹ thuật cắt tỉa bổ sung nhằm giảm hệ số phân nhánh ở các node không tiềm năng. Các kỹ thuật này vận hành ở các mức độ thận trọng khác nhau, từ an toàn tuyệt đối (Null-Move) đến phỏng đoán thống kê (Futility).

### Null-Move Pruning
Null-Move Pruning (Donninger, 1993) dựa trên quan sát: nếu bỏ qua lượt của mình mà vị thế vẫn vượt ngưỡng $\beta$ (tức là quá tốt), thì đối thủ đã tránh được nhánh này từ trước. Engine thử bỏ qua lượt (null move), giảm độ sâu tìm kiếm đi $R + 1$ tầng với $R = 2$, và tìm kiếm với cửa sổ null $[\beta - 1, \beta]$. Nếu điểm null-move $\ge \beta$, nhánh bị cắt ngay lập tức.

Điều kiện kích hoạt:
* Độ sâu hiện tại $d \ge 3$ (`_NULL_MOVE_MIN_DEPTH`).
* Không phải nước null-move liên tiếp (tránh null-null).
* Bên đi không đang bị chiếu.
* Tổng số Xe, Mã, Pháo còn lại $\ge 2$ (tránh zugzwang ở tàn cuộc).

### Late Move Reduction (LMR)
LMR giả định rằng các nước đi xuất hiện cuối danh sách (sau khi đã sắp xếp) ít có khả năng là nước đi tốt nhất. Thay vì tìm kiếm đầy đủ, engine giảm độ sâu đi $1$ tầng (`_LMR_REDUCTION = 1`) cho các nước từ vị trí thứ $4$ trở đi (`_LMR_MIN_MOVE_INDEX = 3`). Nếu kết quả tìm kiếm rút gọn vượt qua $\alpha$, engine tìm kiếm lại với độ sâu đầy đủ. LMR chỉ áp dụng khi $d \ge 3$, nước đi không phải ăn quân, và bên đi không đang bị chiếu.

### Futility Pruning
Futility Pruning cắt bỏ các nước đi yên tĩnh (non-capture) ở độ sâu nông ($d \le 2$) nếu đánh giá tĩnh cộng biên futility vẫn không đạt $\alpha$. Biên futility theo độ sâu:

$$\text{margin} = \begin{cases} 0 & d = 0 \\ 200 & d = 1 \\ 450 & d = 2 \end{cases}$$

(đơn vị centipawn; $200 \approx 1$ Tốt, $450 \approx 1$ Mã). Nước đi đầu tiên trong danh sách luôn được tìm kiếm đầy đủ để tránh bỏ sót chiến thuật quan trọng.

---

## Điều hướng thời gian thực thông qua Iterative Deepening & Aspiration Windows

Để vận hành trong môi trường có giới hạn thời gian nghiêm ngặt, engine sử dụng chiến lược *Iterative Deepening* (IDS): tìm kiếm tuần tự từ độ sâu $d = 1, 2, \dots$ cho đến khi hết ngân sách thời gian. Chiến lược này đảm bảo engine luôn có một nước đi "tốt nhất đến thời điểm hiện tại" để trả về ngay cả khi bị ngắt giữa chừng, đồng thời cung cấp dữ liệu cho Bảng hoán vị để cải thiện thứ tự nước đi ở vòng lặp sâu hơn.

### Aspiration Windows
Từ độ sâu $d \ge 4$ (`_ASPIRATION_MIN_DEPTH`), thay vì sử dụng cửa sổ $[-\infty, +\infty]$, engine khởi tạo cửa sổ hẹp $[\hat{s} - 50, \hat{s} + 50]$ (`_ASPIRATION_DELTA = 50`) quanh điểm số $\hat{s}$ của vòng lặp trước. Cửa sổ hẹp làm tăng tần suất cắt tỉa $\beta$, dẫn đến tìm kiếm nhanh hơn đáng kể so với cửa sổ mở.

Nếu kết quả nằm ngoài cửa sổ:
* **Fail-low** ($\text{score} \le \hat{s} - 50$): cửa sổ mở rộng xuống $[-\infty, \text{score} + 1]$ và tìm kiếm lại.
* **Fail-high** ($\text{score} \ge \hat{s} + 50$): cửa sổ mở rộng lên $[\text{score} - 1, +\infty]$ và tìm kiếm lại.

Vòng lặp aspiration tiếp tục cho đến khi điểm số nằm trong cửa sổ, đảm bảo kết quả chính xác trong khi vẫn tận dụng được lợi thế của cửa sổ hẹp ở phần lớn trường hợp.

---

## Hàm đánh giá tuyến tính với nội suy pha trò chơi

Hàm đánh giá tổng hợp điểm số từ năm thành phần độc lập, mỗi thành phần được nhân với trọng số tương ứng và nội suy tuyến tính theo pha trò chơi (tapered evaluation):

$$E = w_m \cdot E_{\text{material}} + w_p \cdot E_{\text{position}} + w_k \cdot E_{\text{king safety}} + w_b \cdot E_{\text{mobility}} + w_r \cdot E_{\text{rook open}}$$

### Trọng số thành phần

| Thành phần | Trọng số | Ghi chú |
|:---|:---:|:---|
| Vật chất (`material`) | $1.0$ | Trọng số neo — các trọng số còn lại tỉ lệ tương đối so với vật chất. |
| Vị trí (`position`) | $1.2$ | Cao hơn vật chất để engine ưu tiên triển khai quân ở khai cuộc và trung cuộc. |
| An toàn Tướng (`king_safety`) | $0.5$ | Giảm để bot bớt thụ động, tránh lùi quân về phòng thủ quá mức. |
| Cơ động (`mobility`) | $0.1$ | Trọng số thấp vì mobility đếm pseudo-legal moves, dễ nhiễu ở vị trí đông quân. |
| Xe mở (`rook_open`) | $0.6$ | Thưởng Xe chiếm cột/lộ mở, quan trọng ở trung cuộc nhưng kém hơn vị trí. |

### Pha trò chơi (Game Phase)

Pha trò chơi được xác định bằng tổng giá trị vật chất còn lại (không tính Tướng), nội suy tuyến tính trong khoảng $[1200, 2400]$:

$$\phi = \frac{\sum_{p \notin \{\text{K, k}\}} \text{PIECE-VALUE}(p) - 1200}{2400 - 1200}, \quad \phi \in [0, 1]$$

* $\phi = 1.0$: khai cuộc — tổng vật chất $\ge 2400$.
* $\phi = 0.0$: tàn cuộc — tổng vật chất $\le 1200$.
* $0 < \phi < 1$: trung cuộc, nội suy tuyến tính giữa bảng PST khai cuộc và tàn cuộc.

Các bảng Piece-Square Table (PST) cho từng loại quân được thiết kế riêng cho khai cuộc và tàn cuộc, với quy tắc cụ thể: thưởng triển khai quân lên hàng tiền tuyến, phạt quân lùi sâu về cung, thưởng Tốt vượt sông ở cột trung tâm. Khi $\phi$ thay đổi, điểm vị trí được nội suy tương ứng giữa hai bảng.
