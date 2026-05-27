# Engine Cờ Tướng (Xiangqi Engine)

Một engine Cờ Tướng viết bằng Python, tích hợp nhiều bot AI với các thuật toán tìm kiếm có thể cấu hình, hệ thống đấu trường (arena) chạy tự động các trận bot-vs-bot, cùng giao diện tương tác trên console cho người chơi.

## Các Tính Năng Nổi Bật

- **Đầy đủ luật Cờ Tướng** — Sinh nước đi hợp lệ, phát hiện chiếu/chiếu bí, các điều kiện hòa cờ (lặp nước, luật thế sát/hết nước đi), và luật Lộ mặt Tướng (flying general).
- **Đa dạng Bot AI** — Các chiến thuật Negamax, Random, và Greedy.
- **Tối ưu hóa tìm kiếm** — Cắt tỉa Alpha-Beta (Alpha-Beta pruning), Tìm kiếm sâu dần (Iterative Deepening Search - IDS), Tìm kiếm tĩnh (Quiescence Search), Bảng chuyển vị (Transposition Table), Sắp xếp nước đi (Move Ordering), và Sách khai cuộc (Opening Book).
- **Hàm đánh giá Heuristic chi tiết** — Giá trị quân cờ (material balance), bảng vị trí quân cờ (piece-square tables), độ cơ động (mobility), cấu trúc Tốt (pawn structure), và an toàn Tướng (áp lực tấn công, lá chắn bảo vệ, khoảng cách tới Tướng - tropism).
- **Hệ thống Đấu trường (Arena)** — Tự động chạy trận đấu, hỗ trợ xuất biên bản PGN và ghi log chi tiết.
- **Băm Zobrist (Zobrist hashing)** — Mã hóa trạng thái bàn cờ gia số giúp tra cứu cực nhanh trong bảng chuyển vị.
- **Giao diện Console sinh động** — Hiển thị bàn cờ có màu sắc với các ký tự quân cờ tiếng Việt/Trung.

## Cấu Trúc Thư Mục Dự Án

```
src/
├── main.py                      # File chạy chính: Chế độ Người chơi vs Bot / Bot vs Bot
├── core/                        # Biểu diễn bàn cờ và luật chơi
│   ├── board.py                 # Trạng thái bàn cờ, đọc/ghi FEN, thực hiện/hủy nước đi
│   ├── pieces.py                # Định nghĩa quân cờ, màu quân, giá trị quân
│   ├── move.py                  # Mã hóa/giải mã nước đi 16-bit, chuyển đổi UCI
│   ├── move_generator.py        # Sinh nước đi hợp lệ cho tất cả các loại quân
│   ├── rules.py                 # Kiểm tra chiếu, chiếu bí, hết nước đi, hòa cờ
│   ├── zobrist.py               # Băm Zobrist cho trạng thái bàn cờ
│   ├── board_renderer.py        # Hiển thị bàn cờ màu sắc trên console
│   └── utils.py                 # Hàm hỗ trợ tải FEN, tọa độ bàn cờ
├── bots/
│   ├── bot.py                   # Lớp cơ sở Bot, NegmaxBot, RandomBot, GreedyBot, BotManager
│   └── engine/
│       ├── algorithm.py         # Thuật toán tìm kiếm Negamax với cắt tỉa alpha-beta
│       ├── iterative_deepening.py  # IDS hỗ trợ giới hạn thời gian (time limit) và giới hạn độ sâu (depth limit)
│       ├── linear_evaluator.py  # Đánh giá Heuristic (lực lượng, vị trí, cơ động, an toàn Tướng)
│       ├── quiescence_search.py # Tìm kiếm tĩnh giúp giảm hiệu ứng chân trời (horizon effect)
│       ├── transposition_table.py  # Bảng chuyển vị để lưu trữ kết quả tìm kiếm
│       ├── move_ordering.py     # Sắp xếp nước đi bằng MVV-LVA và nước đi sát thủ (killer moves)
│       └── opening_book.py      # Sổ khai cuộc có sẵn cho các biến phổ biến
├── arena/
│   ├── game.py                  # Quản lý trận đấu: vòng lặp chơi, xin thua, hết giờ, xuất PGN
│   └── logger.py                # Ghi log trận đấu có cấu trúc (ra file + console)
└── tests/                       # Unit tests
    ├── test_board.py
    ├── test_rules.py
    ├── test_move_gen.py
    ├── test_algorithm.py
    ├── test_linear_evaluator.py
    ├── test_move_ordering.py
    └── test_move_sorted.py
```

## Yêu Cầu Hệ Thống

- Python >= 3.12
- Thư viện phụ thuộc: `numpy`, `scipy`, `networkx`, `pygame`, `colorama`
- Môi trường phát triển: `pytest`, `black`

## Hướng Dẫn Cài Đặt

```bash
# Clone repository này về máy
git clone <repo-url>
cd btl

# Cài đặt bằng uv (khuyên dùng)
uv sync

# Hoặc cài đặt bằng pip truyền thống
pip install -r requirements.txt
```

## Cách Sử Dụng

### Chơi Trực Tiếp Trên Console

**Cách 1: Sử dụng lệnh tắt `btl` (Khuyên dùng)**

Cài đặt gói ở chế độ editable mode (sẽ tự động đăng ký lệnh `btl` hệ thống):

```bash
# Cài đặt với uv
uv pip install -e .

# Hoặc cài đặt với pip
pip install -e .
```

Sau đó, bạn có thể chạy game trực tiếp từ bất kỳ đâu chỉ bằng lệnh:

```bash
btl
```

**Cách 2: Chạy trực tiếp file Python**

Chạy file chính từ thư mục `src/`:

```bash
cd src
python main.py
```

Bạn sẽ được lựa chọn:

1. **Con người vs Bot** — Chọn loại bot (Negamax, Random, Greedy), chọn bên đi trước (Đỏ/Đen), và nhập nước đi theo định dạng UCI (Ví dụ: `h2e2`).
2. **Bot vs Bot** — Xem hai bot Negamax tự đấu với nhau trên màn hình console theo từng nước đi.

Mặc định, các tệp log và PGN của ván đấu sẽ được tự động lưu vào thư mục `logs/`.

### Front-end UCCI cho GUI/engine host

Engine hiện cung cấp front-end **UCCI** làm giao diện protocol chính cho các GUI/engine host.

```bash
btl --ucci
```

Lệnh cũ `--uci` vẫn được giữ như một alias tương thích ngược.

Khi chạy ở chế độ này, engine có thể nhận các lệnh chuẩn như `ucci`, `isready`, `position`, `go`, `stop`, và `quit` từ GUI hoặc tool host.

### Danh Sách Các Bot AI

| Tên Bot | Thuật Toán | Mô Tả |
|---|---|---|
| `negamax` | Negamax + Alpha-Beta + IDS | Bot mạnh nhất. Hỗ trợ tham số độ sâu `depth` và giới hạn thời gian `time_limit_ms`. |
| `greedy` | Ăn quân tham lam (1-ply) | Ưu tiên chọn các nước đi ăn quân có giá trị lớn nhất ngay lập tức; nếu không có nước ăn quân thì đi nước đầu tiên. |
| `random` | Ngẫu nhiên | Chọn ngẫu nhiên một nước đi hợp lệ. Dùng chủ yếu để kiểm thử. |

## Tài Liệu

Báo cáo chi tiết về phương pháp giải quyết và kết quả của dự án có sẵn tại **[Report](docs/REPORT.md)**.

## Bản Quyền (License)

Bản quyền MIT. Xem chi tiết tại tệp [LICENSE](LICENSE).
