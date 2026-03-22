from dataclasses import dataclass


FILES = "123456789"
RANKS = "abcdefghi"


@dataclass
class Piece:
    owner: str  # "B" (先手) or "W" (後手)
    kind: str   # P, L, N, S, G, B, R, K and promoted forms: +P ...


def parse_square(text: str):
    text = text.strip().lower()
    if len(text) != 2:
        return None
    f, r = text[0], text[1]
    if f not in FILES or r not in RANKS:
        return None
    x = int(f) - 1
    y = RANKS.index(r)
    return x, y


def in_bounds(x, y):
    return 0 <= x < 9 and 0 <= y < 9


def enemy(owner):
    return "W" if owner == "B" else "B"


def can_promote(kind: str):
    return kind in {"P", "L", "N", "S", "B", "R"}


def promoted(kind: str):
    return "+" + kind if can_promote(kind) else kind


def unpromoted(kind: str):
    return kind[1:] if kind.startswith("+") else kind


def promotion_zone(owner: str, y: int):
    return y <= 2 if owner == "B" else y >= 6


def must_promote(owner: str, kind: str, to_y: int):
    base = unpromoted(kind)
    if base in {"P", "L"}:
        return (owner == "B" and to_y == 0) or (owner == "W" and to_y == 8)
    if base == "N":
        return (owner == "B" and to_y <= 1) or (owner == "W" and to_y >= 7)
    return False


def piece_symbol(piece: Piece):
    s = piece.kind
    return s.lower() if piece.owner == "W" else s


def step_dir(owner):
    return -1 if owner == "B" else 1


def path_clear(board, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    stepx = 0 if dx == 0 else (1 if dx > 0 else -1)
    stepy = 0 if dy == 0 else (1 if dy > 0 else -1)
    cx, cy = x1 + stepx, y1 + stepy
    while (cx, cy) != (x2, y2):
        if board[cy][cx] is not None:
            return False
        cx += stepx
        cy += stepy
    return True


def legal_delta(owner, kind, dx, dy, sliding=False):
    f = step_dir(owner)
    base = unpromoted(kind)

    if kind in {"+P", "+L", "+N", "+S"}:
        base = "G"
    elif kind == "+B":
        # horse: bishop + king orthogonal steps
        if abs(dx) == abs(dy) and dx != 0:
            return "slide"
        if (abs(dx), abs(dy)) in {(1, 0), (0, 1)}:
            return True
        return False
    elif kind == "+R":
        # dragon: rook + king diagonal steps
        if (dx == 0 and dy != 0) or (dy == 0 and dx != 0):
            return "slide"
        if abs(dx) == 1 and abs(dy) == 1:
            return True
        return False

    if base == "K":
        return abs(dx) <= 1 and abs(dy) <= 1 and not (dx == 0 and dy == 0)
    if base == "G":
        allowed = {(0, f), (-1, f), (1, f), (-1, 0), (1, 0), (0, -f)}
        return (dx, dy) in allowed
    if base == "S":
        allowed = {(0, f), (-1, f), (1, f), (-1, -f), (1, -f)}
        return (dx, dy) in allowed
    if base == "N":
        return (dx, dy) in {(-1, 2 * f), (1, 2 * f)}
    if base == "L":
        return dx == 0 and ((dy < 0 and owner == "B") or (dy > 0 and owner == "W")) and (dy != 0)
    if base == "P":
        return (dx, dy) == (0, f)
    if base == "B":
        if abs(dx) == abs(dy) and dx != 0:
            return "slide"
        return False
    if base == "R":
        if (dx == 0 and dy != 0) or (dy == 0 and dx != 0):
            return "slide"
        return False
    return False


def legal_move(board, x1, y1, x2, y2, owner):
    if not in_bounds(x1, y1) or not in_bounds(x2, y2):
        return False, "盤外です。"
    piece = board[y1][x1]
    if piece is None:
        return False, "移動元に駒がありません。"
    if piece.owner != owner:
        return False, "自分の駒ではありません。"
    target = board[y2][x2]
    if target is not None and target.owner == owner:
        return False, "自分の駒があるマスには移動できません。"

    dx, dy = x2 - x1, y2 - y1
    ok = legal_delta(owner, piece.kind, dx, dy)
    if not ok:
        return False, "その駒の動きとして不正です。"
    if ok == "slide" and not path_clear(board, x1, y1, x2, y2):
        return False, "駒の間に別の駒があります。"
    return True, ""


def has_pawn_in_file(board, owner, x):
    for y in range(9):
        p = board[y][x]
        if p and p.owner == owner and p.kind == "P":
            return True
    return False


def legal_drop(board, hands, owner, kind, x, y):
    if not in_bounds(x, y):
        return False, "盤外です。"
    if board[y][x] is not None:
        return False, "そのマスにはすでに駒があります。"
    if hands[owner].get(kind, 0) <= 0:
        return False, "その持ち駒はありません。"
    if kind == "P":
        if has_pawn_in_file(board, owner, x):
            return False, "二歩です。"
        if (owner == "B" and y == 0) or (owner == "W" and y == 8):
            return False, "その位置に歩は打てません。"
    if kind == "L":
        if (owner == "B" and y == 0) or (owner == "W" and y == 8):
            return False, "その位置に香は打てません。"
    if kind == "N":
        if (owner == "B" and y <= 1) or (owner == "W" and y >= 7):
            return False, "その位置に桂は打てません。"
    return True, ""


def create_initial_board():
    b = [[None for _ in range(9)] for _ in range(9)]

    # 後手
    back = ["L", "N", "S", "G", "K", "G", "S", "N", "L"]
    for x, k in enumerate(back):
        b[0][x] = Piece("W", k)
    b[1][1] = Piece("W", "R")
    b[1][7] = Piece("W", "B")
    for x in range(9):
        b[2][x] = Piece("W", "P")

    # 先手
    for x in range(9):
        b[6][x] = Piece("B", "P")
    b[7][1] = Piece("B", "B")
    b[7][7] = Piece("B", "R")
    for x, k in enumerate(back):
        b[8][x] = Piece("B", k)

    return b


def print_board(board, hands):
    print("\n    1  2  3  4  5  6  7  8  9")
    print("   " + "---" * 9)
    for y in range(9):
        row = []
        for x in range(9):
            p = board[y][x]
            if p is None:
                row.append(" . ")
            else:
                s = piece_symbol(p)
                if len(s) == 1:
                    s = " " + s
                row.append(f"{s}")
        print(f" {RANKS[y]}|{' '.join(row)}")
    print()

    def hand_text(owner):
        order = ["R", "B", "G", "S", "N", "L", "P"]
        out = []
        for k in order:
            n = hands[owner].get(k, 0)
            if n:
                out.append(f"{k}x{n}")
        return " ".join(out) if out else "(なし)"

    print(f"先手持ち駒(B): {hand_text('B')}")
    print(f"後手持ち駒(W): {hand_text('W')}")
    print()


def apply_move(board, hands, owner, x1, y1, x2, y2, promote_flag):
    piece = board[y1][x1]
    target = board[y2][x2]
    if target is not None:
        captured = unpromoted(target.kind)
        if captured != "K":
            hands[owner][captured] = hands[owner].get(captured, 0) + 1

    board[y1][x1] = None

    new_kind = piece.kind
    if can_promote(piece.kind):
        from_zone = promotion_zone(owner, y1)
        to_zone = promotion_zone(owner, y2)
        if must_promote(owner, piece.kind, y2):
            new_kind = promoted(piece.kind)
        elif (from_zone or to_zone) and promote_flag:
            new_kind = promoted(piece.kind)
    board[y2][x2] = Piece(owner, new_kind)


def apply_drop(board, hands, owner, kind, x, y):
    hands[owner][kind] -= 1
    if hands[owner][kind] == 0:
        del hands[owner][kind]
    board[y][x] = Piece(owner, kind)


def king_exists(board, owner):
    for y in range(9):
        for x in range(9):
            p = board[y][x]
            if p and p.owner == owner and p.kind == "K":
                return True
    return False


def main():
    board = create_initial_board()
    hands = {"B": {}, "W": {}}
    turn = "B"

    print("将棋ローカル対戦 (人 vs 人)")
    print("コマンド例:")
    print("  move 7g 7f        # 駒を移動")
    print("  move 2h 2b+       # 成りを指定")
    print("  drop P 5e         # 持ち駒を打つ")
    print("  quit              # 終了")

    while True:
        print_board(board, hands)
        player_name = "先手(B)" if turn == "B" else "後手(W)"
        cmd = input(f"{player_name} の手番 > ").strip()
        if not cmd:
            continue
        if cmd.lower() in {"quit", "exit"}:
            print("終了します。")
            break

        parts = cmd.split()
        if parts[0].lower() == "move" and len(parts) == 3:
            src = parse_square(parts[1])
            dst_text = parts[2]
            promote_flag = False
            if dst_text.endswith("+"):
                promote_flag = True
                dst_text = dst_text[:-1]
            dst = parse_square(dst_text)
            if src is None or dst is None:
                print("座標形式が不正です。例: 7g 7f")
                continue
            x1, y1 = src
            x2, y2 = dst
            ok, reason = legal_move(board, x1, y1, x2, y2, turn)
            if not ok:
                print(f"不正な手: {reason}")
                continue
            apply_move(board, hands, turn, x1, y1, x2, y2, promote_flag)

        elif parts[0].lower() == "drop" and len(parts) == 3:
            kind = parts[1].upper()
            dst = parse_square(parts[2])
            if kind not in {"P", "L", "N", "S", "G", "B", "R"}:
                print("打てる駒は P L N S G B R です。")
                continue
            if dst is None:
                print("座標形式が不正です。例: 5e")
                continue
            x, y = dst
            ok, reason = legal_drop(board, hands, turn, kind, x, y)
            if not ok:
                print(f"不正な手: {reason}")
                continue
            apply_drop(board, hands, turn, kind, x, y)
        else:
            print("コマンド形式が不正です。")
            continue

        if not king_exists(board, enemy(turn)):
            print_board(board, hands)
            print(f"{player_name} の勝ちです。(相手玉を取りました)")
            break

        turn = enemy(turn)


if __name__ == "__main__":
    main()