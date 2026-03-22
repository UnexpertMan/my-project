from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import shogi, random

app = FastAPI(title="Shogi CPU App (Minimal)")

class MoveReq(BaseModel):
    sfen: str
    move_usi: str  # 例: "7g7f"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/new")
def new_game():
    b = shogi.Board()
    return {"sfen": b.sfen(), "turn": "sente"}

@app.post("/move")
def apply_move(req: MoveReq):
    b = shogi.Board(req.sfen)
    # ユーザーの手を適用
    try:
        b.push_usi(req.move_usi)
    except Exception:
        raise HTTPException(400, "illegal move")

    if b.is_game_over():
        return {"sfen": b.sfen(), "game_over": True, "result": b.result()}

    # CPUの応手（ランダム）
    legal = list(b.legal_moves)
    if not legal:
        return {"sfen": b.sfen(), "game_over": True, "result": b.result()}

    cpu_move = random.choice(legal)
    cpu_move_usi = cpu_move.usi()   # ← ★ここがポイント（BoardではなくMoveに対して .usi()）
    b.push(cpu_move)

    return {
        "sfen": b.sfen(),
        "game_over": b.is_game_over(),
        "cpu_move_usi": cpu_move_usi
    }

# ---- 静的ファイル設定（最後に定義）----
ROOT_DIR = Path(__file__).resolve().parents[1]   # backend/
STATIC_DIR = ROOT_DIR / "static"

# / で index.html を返す
@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")

# /static で静的ファイルを配信
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class MoveReq(BaseModel):
    sfen: str
    move_usi: str  # 例: "7g7f"

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/new")
def new_game():
    b = shogi.Board()
    return {"sfen": b.sfen(), "turn": "sente"}

@app.post("/move")
def apply_move(req: MoveReq):
    b = shogi.Board(req.sfen)
    # プレイヤーの手を適用
    try:
        b.push_usi(req.move_usi)
    except Exception:
        raise HTTPException(400, "illegal move")

    if b.is_game_over():
        return {"sfen": b.sfen(), "game_over": True, "result": b.result()}

    # CPUの応手（ランダム）
    legal = list(b.legal_moves)
    if not legal:
        return {"sfen": b.sfen(), "game_over": True, "result": b.result()}

    cpu_move = random.choice(legal)
    cpu_move_usi = b.usi(cpu_move)
    b.push(cpu_move)

    return {
        "sfen": b.sfen(),
        "game_over": b.is_game_over(),
        "cpu_move_usi": cpu_move_usi
    }