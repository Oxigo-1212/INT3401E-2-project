# Tài Liệu Dự Án — Engine Cờ Tướng

> [← Quay lại README](../README.md)

---

## Kiến Trúc Hệ Thống

Dự án được chia thành 3 module chính, mỗi module có một trách nhiệm rõ ràng:

```
src/
├── main.py              ← Điểm vào (entry point), lệnh `btl`
│
├── core/                ← Lõi engine: bàn cờ, luật, sinh nước đi
│   ├── board.py         ← Trạng thái bàn cờ, make/undo move, FEN, Zobrist
│   ├── pieces.py        ← Định nghĩa quân cờ, màu, giá trị
│   ├── move.py          ← Mã hóa/giải mã nước đi 16-bit, chuyển đổi UCI
│   ├── move_generator.py← Sinh nước đi pseudo-legal cho 7 loại quân
│   ├── rules.py         ← Chiếu, chiếu bí, hòa, lộ mặt Tướng, lọc legal
│   ├── zobrist.py       ← Bảng băm Zobrist 64-bit, cập nhật gia số O(1)
│   ├── board_renderer.py← Hiển thị bàn cờ ANSI + ký tự Hán
│   └── utils.py         ← load_fen, print_board, tọa độ
│
├── bots/                ← Các bot AI và thuật toán tìm kiếm
│   ├── bot.py           ← Bot base class, NegmaxBot, MinimaxBot,
│   │                       RandomBot, GreedyBot, BotManager
│   └── engine/
│       ├── algorithm.py          ← Negamax, Minimax + Alpha-Beta
│       ├── iterative_deepening.py← IDS: time limit & depth limit
│       ├── linear_evaluator.py   ← Heuristic: material, position,
│       │                            mobility, king safety, pawn
│       ├── quiescence_search.py  ← Tìm kiếm tĩnh (chỉ nước ăn quân)
│       ├── transposition_table.py← Bảng chuyển vị (hash table)
│       ├── move_ordering.py      ← MVV-LVA, killer, history heuristic
│       └── opening_book.py       ← Sổ khai cuộc (Zobrist → moves)
│
├── arena/               ← Hệ thống đấu trường tự động
│   ├── game.py          ← Game loop, resign, timeout, PGN export
│   └── logger.py        ← Ghi log có cấu trúc (file + console)
│
└── tests/               ← Bộ kiểm thử (pytest)
```

### Luồng dữ liệu chính

```
Board ──→ MoveGenerator ──→ rules.get_legal_moves() ──→ Bot.get_move()
  ↑                                                          │
  └──── board.make_move(move) ←───────────────────────────────┘
```

1. `Board` lưu trạng thái bàn cờ dưới dạng mảng 90 ô.
2. `MoveGenerator` sinh tất cả nước đi pseudo-legal cho phe đang đến lượt.
3. `rules.get_legal_moves()` lọc bỏ nước tự chiếu và lộ mặt Tướng.
4. `Bot.get_move()` chọn nước đi tốt nhất (qua Negamax/Minimax + IDS + TT + Opening Book).
5. `Board.make_move()` thực thi nước đi, cập nhật Zobrist hash, đổi lượt.

### Luồng tìm kiếm (Search Pipeline)

```
Bot.get_move()
  │
  ├─ Tra Opening Book (Zobrist key → nước đi có sẵn)
  │
  └─ Iterative Deepening Search (tăng depth từ 1)
       │
       └─ Negamax / Minimax + Alpha-Beta
            │
            ├─ Probe Transposition Table
            ├─ Move Ordering (TT → MVV-LVA → Killers → History)
            ├─ Đệ quy depth-1 cho mỗi nước đi
            ├─ Quiescence Search (tại depth=0, chỉ nước ăn quân)
            └─ Store vào Transposition Table
```

### Hàm đánh giá (Evaluation)

`linear_evaluator.heuristic()` tổng hợp 5 thành phần có trọng số:

| Thành phần | Mô tả |
|---|---|
| **Material** | Chênh lệch tổng giá trị quân cờ hai bên |
| **Position** | Điểm thưởng/phạt theo vị trí quân trên bảng piece-square tables |
| **Mobility** | Chênh lệch số nước đi khả thi giữa hai bên |
| **King Safety** | Áp lực tấn công vào vùng Tướng, lá chắn Sĩ/Tượng, khoảng cách quân tấn công (tropism) |
| **Pawn Structure** | Điểm thưởng vị trí Tốt (đã qua sông, cột trung tâm, ...) |

---

## API Reference

> Các trang API chi tiết cho từng module. Nội dung sẽ được bổ sung.

### Module `core` — Lõi Engine

- [core.board](api/core-board.md) — Bàn cờ, trạng thái, make/undo move
- [core.pieces](api/core-pieces.md) — Quân cờ, màu, giá trị
- [core.move](api/core-move.md) — Mã hóa nước đi 16-bit, chuyển đổi UCI
- [core.move_generator](api/core-move-generator.md) — Sinh nước đi pseudo-legal
- [core.rules](api/core-rules.md) — Luật chơi, chiếu, hòa, lọc nước đi hợp lệ
- [core.zobrist](api/core-zobrist.md) — Băm Zobrist
- [core.board_renderer](api/core-board-renderer.md) — Hiển thị bàn cờ
- [core.utils](api/core-utils.md) — Hàm tiện ích

### Module `bots` — Bot AI

- [bots.bot](api/bots-bot.md) — Bot base class, NegmaxBot, MinimaxBot, RandomBot, GreedyBot, BotManager
- [bots.engine.algorithm](api/bots-engine-algorithm.md) — Negamax, Minimax + Alpha-Beta
- [bots.engine.iterative_deepening](api/bots-engine-iterative-deepening.md) — Tìm kiếm sâu dần (IDS)
- [bots.engine.linear_evaluator](api/bots-engine-linear-evaluator.md) — Hàm đánh giá Heuristic
- [bots.engine.quiescence_search](api/bots-engine-quiescence-search.md) — Tìm kiếm tĩnh
- [bots.engine.transposition_table](api/bots-engine-transposition-table.md) — Bảng chuyển vị
- [bots.engine.move_ordering](api/bots-engine-move-ordering.md) — Sắp xếp nước đi
- [bots.engine.opening_book](api/bots-engine-opening-book.md) — Sổ khai cuộc

### Module `arena` — Hệ Thống Đấu Trường

- [arena.game](api/arena-game.md) — Quản lý trận đấu, PGN export
- [arena.logger](api/arena-logger.md) — Ghi log trận đấu
