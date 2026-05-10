from enum import IntEnum
from pathlib import Path

type TTEntry = TT_Entry | None

class TT_FLAG(IntEnum):
    EXACT = 0 # Use whene there is no cutoff
    LOWERBOUND = 1 # Use when there is cutoff.
    UPPERBOUND = 2 # Use when there is no cutoff and it is the best score in expanding

TT_TABLE: list[TTEntry] = []

class TT_Entry:
    __slots__ = ['key', 'depth', 'score', 'flag', 'best_move']

    def __init__(self, key, depth, score, flag, best_move):
        self.key = key
        self.depth = depth
        self.score = score
        self.flag = flag
        self.best_move = best_move

def init_tt(size: int, TT_TABLE: list) -> None:
    TT_TABLE[:] = [ None for _ in enumerate(range(size)) ]

def clear_tt(TT_TABLE: list):
    for i in range(len(TT_TABLE)):
        TT_TABLE[i] = None

def store(key: int, depth: int, score: float, flag: TT_FLAG, best_move: int, TT_TABLE: list):
    if not TT_TABLE:
        return
    
    index = key % len(TT_TABLE)
    entry = TT_TABLE[index]

    # Ghi đè nếu ô trống hoặc kết quả mới tính toán sâu hơn kết quả cũ
    if entry is None:
        TT_TABLE[index] = TT_Entry(key, depth, score, flag, best_move)
    elif depth >= entry.depth:
        entry.key = key
        entry.depth = depth
        entry.score = score
        entry.flag = flag
        entry.best_move = best_move

def probe(key: int, depth: int, alpha: float, beta: float, TT_TABLE: list) -> tuple[TTEntry, bool]:
    if not TT_TABLE:
        return None, False
    
    index = key % len(TT_TABLE)
    entry = TT_TABLE[index]

    # 1. Key Verification: Is this actually the same position?
    if entry is not None and entry.key == key:
        # 2. Depth Check: Is this information high-quality enough and if the certain condition is match?
        is_useful = (entry.depth >= depth) and (
        (entry.flag == TT_FLAG.EXACT) or
        (entry.flag == TT_FLAG.LOWERBOUND and entry.score >= beta) or
        (entry.flag == TT_FLAG.UPPERBOUND and entry.score <= alpha)
    )
        return entry, is_useful

    return None, False # Cache Miss


def save(path: str = "data/tt") -> None:
    import pickle

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('wb') as f:
        pickle.dump(TT_TABLE, f)

def load(path: str = "data/tt") -> None:
    import pickle

    target = Path(path)
    with target.open('rb') as f:
        data = pickle.load(f)
    TT_TABLE[:] = data
