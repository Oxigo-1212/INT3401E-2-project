
class Bot():
    def get_move(self, board: Board) -> int | None: ...
    
    def get_name(self) -> str: ...        # tên bot (để log tournament)
    def get_config(self) -> dict: ...     # depth, algorithm, v.v.