from base64 import b64decode
from contextlib import asynccontextmanager
from hashlib import sha256
import json
from math import pow
import os
from pathlib import Path
import secrets
import time
from typing import Literal
from urllib.parse import urlencode, urlsplit
from urllib.request import Request as UrlRequest, urlopen
from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
import numpy as np
from PIL import Image, ImageDraw
from database import connect, initialize_database


def load_local_environment() -> None:
    """Load a small local .env file without adding another runtime package."""
    env_file = Path(__file__).with_name(".env")
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_environment()

try:
    from recognizer import hanzi_model_status, model_status, recognize, recognize_hanzi_rasterized_png, recognize_rasterized_png, recognize_rasterized_strokes
    ML_IMPORT_ERROR = None
except ModuleNotFoundError as error:
    # Keep the vocabulary API available if an optional ML package is not yet
    # installed in the backend virtual environment.
    ML_IMPORT_ERROR = str(error)

    def model_status():
        return {"model_status": "dependencies_missing", "labels": 0, "validation_accuracy": None}

    def hanzi_model_status():
        return {"model_status": "dependencies_missing", "labels": 0, "validation_accuracy": None}

    def recognize(_: bytes, __: int):
        return []

    def recognize_rasterized_strokes(_: object, __: int):
        return []

    def recognize_rasterized_png(_: bytes, __: int):
        return []

    def recognize_hanzi_rasterized_png(_: bytes, __: int):
        return []

@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield

app = FastAPI(title="KanjiAI API", version="0.3.0", lifespan=lifespan)
# Comma-separated origins let a deployed frontend opt in without editing code.
cors_origins = [origin.strip() for origin in os.getenv("KANJIAI_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8010/auth/google/callback").strip()
APP_URL = os.getenv("KANJIAI_APP_URL", "http://localhost:5173").rstrip("/")
SESSION_DAYS = max(1, int(os.getenv("KANJIAI_SESSION_DAYS", "30")))
SESSION_COOKIE = "kanjiai_session"
ADMIN_API_KEY = os.getenv("KANJIAI_ADMIN_API_KEY", "").strip()

class RecognitionRequest(BaseModel):
    image: str | None = None
    strokes: list[list[list[float]]] | None = None
    canvas_size: int = Field(default=400, ge=64, le=1024)
    rasterized: bool = False
    top_k: int = Field(default=3, ge=1, le=3)
    stroke_count: int | None = Field(default=None, ge=1, le=40)
    expected_text: str | None = Field(default=None, max_length=20)
    language: str = Field(default="ja", pattern="^(ja|zh)$")

class HandwritingSampleCreate(BaseModel):
    image: str
    expected_text: str = Field(min_length=1, max_length=20)
    source: str = Field(default="flashcard", pattern="^(flashcard|lookup)$")
class KanjiCreate(BaseModel):
    char: str = Field(min_length=1, max_length=1); meaning: str = Field(min_length=1); on_reading: str; kun_reading: str
    strokes: int = Field(ge=1, le=99); level: str = Field(pattern="^N[1-5]$"); radical: str = Field(min_length=1); han_viet: str = ""
class LessonCreate(BaseModel):
    level: str = Field(pattern="^N[1-5]$"); title: str = Field(min_length=1, max_length=120); description: str = ""; order_index: int = Field(default=0, ge=0)
class VocabularyCreate(BaseModel):
    lesson_id: int | None = Field(default=None, ge=1); word: str = Field(min_length=1); reading: str = Field(min_length=1)
    meaning: str = Field(min_length=1); level: str = Field(pattern="^N[1-5]$")
class ProgressUpdate(BaseModel):
    progress_state: Literal["started", "completed"] = "started"
    score: float | None = Field(default=None, ge=0, le=1)
    resume_position: int = Field(default=0, ge=0, le=100000)

class UserSettingsUpdate(BaseModel):
    dark_mode: bool | None = None
    sound_effects: bool | None = None
    kanji_font: Literal["Noto Serif JP", "Yu Mincho", "Hiragino Mincho"] | None = None

class KanjiUpdate(BaseModel):
    meaning: str | None = Field(default=None, min_length=1)
    on_reading: str | None = None
    kun_reading: str | None = None
    strokes: int | None = Field(default=None, ge=1, le=99)
    level: str | None = Field(default=None, pattern="^N[1-5]$")
    radical: str | None = Field(default=None, min_length=1)
    han_viet: str | None = None

class VocabularyUpdate(BaseModel):
    lesson_id: int | None = Field(default=None, ge=1)
    word: str | None = Field(default=None, min_length=1)
    reading: str | None = Field(default=None, min_length=1)
    meaning: str | None = Field(default=None, min_length=1)
    level: str | None = Field(default=None, pattern="^N[1-5]$")
    example_japanese: str | None = None
    example_reading: str | None = None
    example_meaning: str | None = None

class GrammarPatternUpdate(BaseModel):
    formula: str | None = Field(default=None, min_length=1)
    explanation_vi: str | None = Field(default=None, min_length=1)
    note: str | None = None

class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    order_index: int | None = Field(default=None, ge=0)
    group_id: int | None = Field(default=None, ge=1)

def row(item): return dict(item) if item else None

SAMPLES_DIR = Path(__file__).parent / "data" / "handwriting"
MAX_HANDWRITING_IMAGE_BYTES = 2 * 1024 * 1024

# The initial locally trained characters.  This is used only to gently rank
# DaKanji's existing candidates by the number of pen-down strokes; it never
# removes kana or other Kanji from the generic recognizer.
KNOWN_STROKES = {
    "一": 1, "二": 2, "三": 3, "四": 5, "五": 4, "六": 4, "七": 2, "八": 2,
    "九": 2, "十": 2, "百": 6, "千": 3, "円": 4, "年": 6, "時": 10, "分": 4,
    "半": 5, "月": 4, "火": 4, "水": 4, "木": 4, "金": 8, "土": 3, "日": 4,
    "人": 2, "口": 3, "目": 5, "耳": 6, "手": 4, "足": 7,
}

def canvas_png(image: str) -> bytes:
    """Validate the browser canvas image before it is stored or processed."""
    try:
        raw = b64decode(image.split(",", 1)[-1], validate=True)
    except Exception as error:
        raise HTTPException(422, "Ảnh canvas không hợp lệ") from error
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(422, "Chỉ nhận ảnh PNG từ vùng viết")
    if not raw or len(raw) > MAX_HANDWRITING_IMAGE_BYTES:
        raise HTTPException(413, "Ảnh nét viết quá lớn")
    return raw


def rasterize_strokes(strokes: list[list[list[float]]], size: int) -> np.ndarray:
    """Independently recreate DaKanji's public vector-to-raster contract.

    The model receives smooth white ink on a black square, cropped around the
    original vector points and padded proportionally. Keeping a square avoids
    distorting wide glyphs such as 二 when the model resizes to 64×64.
    """
    if not strokes or len(strokes) > 40:
        raise ValueError("Số nét viết không hợp lệ")
    image = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(image)
    points_for_bounds: list[tuple[float, float]] = []
    stroke_width = 16
    for stroke in strokes:
        if not stroke or len(stroke) > 4000:
            raise ValueError("Dữ liệu một nét viết không hợp lệ")
        points: list[tuple[float, float]] = []
        for point in stroke:
            if len(point) < 2:
                raise ValueError("Tọa độ nét viết không hợp lệ")
            x, y = float(point[0]), float(point[1])
            if not (np.isfinite(x) and np.isfinite(y)):
                raise ValueError("Tọa độ nét viết không hợp lệ")
            points.append((x, y))
            points_for_bounds.append((x, y))
        if len(points) == 1:
            x, y = points[0]
            draw.ellipse((x - stroke_width / 2, y - stroke_width / 2, x + stroke_width / 2, y + stroke_width / 2), fill=255)
        else:
            draw.line(points, fill=255, width=stroke_width, joint="curve")
    if not points_for_bounds:
        raise ValueError("Chưa có nét viết")
    xs, ys = zip(*points_for_bounds)
    left, top = max(0, int(np.floor(min(xs) - stroke_width))), max(0, int(np.floor(min(ys) - stroke_width)))
    right, bottom = min(size, int(np.ceil(max(xs) + stroke_width))), min(size, int(np.ceil(max(ys) + stroke_width)))
    glyph_width, glyph_height = max(1, right - left), max(1, bottom - top)
    padding = int(np.ceil(max(glyph_width, glyph_height) * 0.1))
    side = max(glyph_width, glyph_height) + padding * 2
    crop_left, crop_top = int(np.floor(left - (side - glyph_width) / 2)), int(np.floor(top - (side - glyph_height) / 2))
    crop_left, crop_top = max(0, crop_left), max(0, crop_top)
    if crop_left + side > size:
        crop_left = max(0, size - side)
    if crop_top + side > size:
        crop_top = max(0, size - side)
    crop_width, crop_height = min(side, size - crop_left), min(side, size - crop_top)
    return np.asarray(image.crop((crop_left, crop_top, crop_left + crop_width, crop_top + crop_height)), dtype=np.float32)

def rank_with_stroke_count(predictions: list[dict], stroke_count: int | None) -> list[dict]:
    """Use stroke count as a soft tie-breaker, preserving generic DaKanji."""
    if stroke_count is None:
        return predictions
    reranked = []
    for prediction in predictions:
        expected = KNOWN_STROKES.get(prediction["kanji"])
        difference = abs(expected - stroke_count) if expected else 0
        # This is intentionally only a tie-breaker. A learner can split or
        # join a stroke differently, so DaKanji remains the dominant signal.
        # The original probability remains available as ``confidence``.
        score = prediction["confidence"] * pow(0.85, difference)
        reranked.append({**prediction, "expected_strokes": expected, "rank_score": round(score, 5)})
    return sorted(reranked, key=lambda item: item["rank_score"], reverse=True)

@app.get("/health")
def health(): return {"status":"ok", "model": model_status(), "database":"sqlite"}


def oauth_enabled() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    """Reject every admin request unless a deployment-specific key is configured."""
    if not ADMIN_API_KEY:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "API quản trị chưa được cấu hình")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Khóa quản trị không hợp lệ")


def session_is_secure() -> bool:
    return APP_URL.startswith("https://")


def session_digest(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def public_user(user) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "avatar_url": user["avatar_url"],
    }


def session_user(token: str | None):
    if not token:
        return None
    now = int(time.time())
    with connect() as db:
        db.execute("DELETE FROM user_sessions WHERE expires_at <= ?", (now,))
        return db.execute("""SELECT u.* FROM users u
            JOIN user_sessions s ON s.user_id=u.id
            WHERE s.token_hash=? AND s.expires_at>?""", (session_digest(token), now)).fetchone()


def require_user(token: str | None):
    user = session_user(token)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bạn cần đăng nhập để lưu tiến độ")
    return user


def callback_page(ok: bool, message: str) -> HTMLResponse:
    origin = f"{urlsplit(APP_URL).scheme}://{urlsplit(APP_URL).netloc}"
    payload = json.dumps({"type": "kanjiai-google-auth", "ok": ok, "message": message}, ensure_ascii=False)
    target_origin = json.dumps(origin)
    app_url = json.dumps(f"{APP_URL}/login")
    body = f"""<!doctype html><html lang=\"vi\"><meta charset=\"utf-8\"><title>KanjiAI</title>
    <body><p>{message}</p><script>
    const result={payload};
    if(window.opener) {{ window.opener.postMessage(result, {target_origin}); window.close(); }}
    else {{ window.location.replace({app_url}); }}
    </script></body></html>"""
    return HTMLResponse(body, status_code=200 if ok else 400)


@app.get("/auth/google/status")
def google_auth_status():
    return {"enabled": oauth_enabled(), "redirect_uri": GOOGLE_REDIRECT_URI}


@app.get("/auth/google/login")
def google_login():
    if not oauth_enabled():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Google OAuth chưa được cấu hình trên máy chủ")
    now = int(time.time())
    state = secrets.token_urlsafe(32)
    with connect() as db:
        db.execute("DELETE FROM oauth_login_states WHERE expires_at <= ?", (now,))
        db.execute("INSERT INTO oauth_login_states(state,expires_at) VALUES (?,?)", (state, now + 600))
    query = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@app.get("/auth/google/callback")
def google_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return callback_page(False, "Bạn đã hủy đăng nhập Google.")
    if not oauth_enabled() or not code or not state:
        return callback_page(False, "Không thể hoàn tất đăng nhập Google.")
    now = int(time.time())
    with connect() as db:
        valid_state = db.execute("SELECT state FROM oauth_login_states WHERE state=? AND expires_at>?", (state, now)).fetchone()
        db.execute("DELETE FROM oauth_login_states WHERE state=?", (state,))
    if not valid_state:
        return callback_page(False, "Phiên đăng nhập đã hết hạn. Hãy thử lại.")
    try:
        request_data = urlencode({
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }).encode("utf-8")
        request = UrlRequest("https://oauth2.googleapis.com/token", data=request_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        token_data = json.loads(urlopen(request, timeout=12).read().decode("utf-8"))
        claims = id_token.verify_oauth2_token(token_data["id_token"], GoogleRequest(), GOOGLE_CLIENT_ID)
        if not claims.get("email_verified") or not claims.get("sub") or not claims.get("email"):
            raise ValueError("Google không xác minh được địa chỉ email")
    except Exception:
        return callback_page(False, "Google không xác minh được đăng nhập. Hãy thử lại.")
    email = claims["email"].strip().lower()
    name = str(claims.get("name") or email.split("@", 1)[0]).strip()
    picture = str(claims.get("picture") or "").strip()
    with connect() as db:
        user = db.execute("SELECT * FROM users WHERE google_sub=? OR email=? ORDER BY google_sub=? DESC LIMIT 1", (claims["sub"], email, claims["sub"])).fetchone()
        if user:
            db.execute("UPDATE users SET google_sub=?,email=?,display_name=?,avatar_url=?,last_login_at=? WHERE id=?", (claims["sub"], email, name, picture, now, user["id"]))
            user_id = user["id"]
        else:
            cursor = db.execute("INSERT INTO users(google_sub,email,display_name,avatar_url,created_at,last_login_at) VALUES (?,?,?,?,?,?)", (claims["sub"], email, name, picture, now, now))
            user_id = cursor.lastrowid
        raw_token = secrets.token_urlsafe(48)
        db.execute("DELETE FROM user_sessions WHERE user_id=?", (user_id,))
        db.execute("INSERT INTO user_sessions(token_hash,user_id,expires_at,created_at) VALUES (?,?,?,?)", (session_digest(raw_token), user_id, now + SESSION_DAYS * 86400, now))
    response = callback_page(True, "Đăng nhập thành công. Bạn có thể quay lại KanjiAI.")
    response.set_cookie(SESSION_COOKIE, raw_token, max_age=SESSION_DAYS * 86400, httponly=True, secure=session_is_secure(), samesite="lax", path="/")
    return response


@app.get("/auth/me")
def auth_me(kanjiai_session: str | None = Cookie(default=None)):
    user = require_user(kanjiai_session)
    return public_user(user)


@app.post("/auth/logout")
def auth_logout(kanjiai_session: str | None = Cookie(default=None)):
    if kanjiai_session:
        with connect() as db:
            db.execute("DELETE FROM user_sessions WHERE token_hash=?", (session_digest(kanjiai_session),))
    response = HTMLResponse("", status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path="/", secure=session_is_secure(), samesite="lax")
    return response


def default_user_settings() -> dict:
    return {"dark_mode": False, "sound_effects": True, "kanji_font": "Noto Serif JP"}


@app.get("/user-settings")
def get_user_settings(kanjiai_session: str | None = Cookie(default=None)):
    """Return interface preferences for the currently signed-in learner only."""
    user = require_user(kanjiai_session)
    with connect() as db:
        item = db.execute("SELECT dark_mode,sound_effects,kanji_font,updated_at FROM user_settings WHERE user_id=?", (user["id"],)).fetchone()
    if not item:
        return default_user_settings()
    return {
        "dark_mode": bool(item["dark_mode"]),
        "sound_effects": bool(item["sound_effects"]),
        "kanji_font": item["kanji_font"],
        "updated_at": item["updated_at"],
    }


@app.put("/user-settings")
def save_user_settings(settings: UserSettingsUpdate, kanjiai_session: str | None = Cookie(default=None)):
    user = require_user(kanjiai_session)
    now = int(time.time())
    with connect() as db:
        current = db.execute("SELECT dark_mode,sound_effects,kanji_font FROM user_settings WHERE user_id=?", (user["id"],)).fetchone()
        values = dict(current) if current else default_user_settings()
        if settings.dark_mode is not None:
            values["dark_mode"] = settings.dark_mode
        if settings.sound_effects is not None:
            values["sound_effects"] = settings.sound_effects
        if settings.kanji_font is not None:
            values["kanji_font"] = settings.kanji_font
        db.execute("""INSERT INTO user_settings(user_id,dark_mode,sound_effects,kanji_font,updated_at)
            VALUES (?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET
            dark_mode=excluded.dark_mode,sound_effects=excluded.sound_effects,
            kanji_font=excluded.kanji_font,updated_at=excluded.updated_at""",
            (user["id"], int(values["dark_mode"]), int(values["sound_effects"]), values["kanji_font"], now))
    return {**values, "updated_at": now}


@app.get("/progress")
def get_progress(kanjiai_session: str | None = Cookie(default=None)):
    user = require_user(kanjiai_session)
    with connect() as db:
        rows = db.execute("SELECT content_type,content_id,progress_state,score,resume_position,updated_at FROM user_progress WHERE user_id=? ORDER BY updated_at DESC", (user["id"],)).fetchall()
    return [dict(item) for item in rows]


@app.put("/progress/{content_type}/{content_id}")
def save_progress(content_type: Literal["kanji", "vocabulary", "grammar"], content_id: str, progress: ProgressUpdate, kanjiai_session: str | None = Cookie(default=None)):
    user = require_user(kanjiai_session)
    if not content_id.strip() or len(content_id) > 200:
        raise HTTPException(422, "Mã nội dung không hợp lệ")
    now = int(time.time())
    with connect() as db:
        db.execute("""INSERT INTO user_progress(user_id,content_type,content_id,progress_state,score,resume_position,updated_at)
            VALUES (?,?,?,?,?,?,?) ON CONFLICT(user_id,content_type,content_id) DO UPDATE SET
            progress_state=excluded.progress_state,score=excluded.score,resume_position=excluded.resume_position,updated_at=excluded.updated_at""",
            (user["id"], content_type, content_id.strip(), progress.progress_state, progress.score, progress.resume_position, now))
    return {"ok": True}


@app.get("/review-items")
def get_review_items(kanjiai_session: str | None = Cookie(default=None)):
    """Items explicitly saved by a learner for later review, separate from course progress."""
    user = require_user(kanjiai_session)
    with connect() as db:
        rows = db.execute("SELECT content_type,content_id,created_at FROM user_review_items WHERE user_id=? ORDER BY created_at DESC", (user["id"],)).fetchall()
        items = []
        for item in rows:
            record = dict(item)
            if item["content_type"] == "kanji":
                source = db.execute("SELECT char,meaning,han_viet,level FROM kanji WHERE char=?", (item["content_id"],)).fetchone()
                if source:
                    record.update(title=source["char"], subtitle=f"{source['han_viet']} · {source['meaning']}", href=f"/kanji/{source['char']}")
            elif item["content_type"] == "vocabulary" and item["content_id"].startswith("word-"):
                source = db.execute("""SELECT v.id,v.word,v.reading,v.meaning,v.level,v.lesson_id
                    FROM vocabulary v WHERE v.id=?""", (item["content_id"][5:],)).fetchone()
                if source:
                    record.update(title=source["word"], subtitle=f"{source['reading']} · {source['meaning']}", href=f"/vocabulary/{source['level'].lower()}/lesson/{source['lesson_id']}/flashcard")
            elif item["content_type"] == "grammar" and item["content_id"].startswith("pattern-"):
                source = db.execute("""SELECT p.id,p.formula,p.explanation_vi,l.id AS lesson_id,l.level
                    FROM grammar_patterns p JOIN grammar_lessons l ON l.id=p.lesson_id WHERE p.id=?""", (item["content_id"][8:],)).fetchone()
                if source:
                    record.update(title=source["formula"], subtitle=source["explanation_vi"], href=f"/grammar/{source['level'].lower()}/lesson/{source['lesson_id']}/pattern/{source['id']}")
            if "href" in record:
                items.append(record)
    return items


@app.put("/review-items/{content_type}/{content_id}")
def add_review_item(content_type: Literal["kanji", "vocabulary", "grammar"], content_id: str, kanjiai_session: str | None = Cookie(default=None)):
    user = require_user(kanjiai_session)
    if not content_id.strip() or len(content_id) > 200:
        raise HTTPException(422, "Mã nội dung không hợp lệ")
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO user_review_items(user_id,content_type,content_id,created_at) VALUES (?,?,?,?)", (user["id"], content_type, content_id.strip(), int(time.time())))
    return {"ok": True}


@app.delete("/review-items/{content_type}/{content_id}")
def remove_review_item(content_type: Literal["kanji", "vocabulary", "grammar"], content_id: str, kanjiai_session: str | None = Cookie(default=None)):
    user = require_user(kanjiai_session)
    with connect() as db:
        db.execute("DELETE FROM user_review_items WHERE user_id=? AND content_type=? AND content_id=?", (user["id"], content_type, content_id.strip()))
    return {"ok": True}

@app.get("/kanji")
def list_kanji(level: str | None = None):
    query, values = "SELECT * FROM kanji", []
    if level: query += " WHERE level = ?"; values.append(level.upper())
    with connect() as db: return [row(x) for x in db.execute(query + " ORDER BY CASE WHEN order_index=0 THEN 1 ELSE 0 END, order_index, char", values).fetchall()]

@app.get("/kanji/{char}")
def kanji_detail(char: str):
    with connect() as db: item = db.execute("SELECT * FROM kanji WHERE char = ?", (char,)).fetchone()
    if not item: raise HTTPException(404, "Không tìm thấy Kanji")
    return row(item)

@app.get("/kanji/{char}/related-words")
def related_words(char: str):
    with connect() as db:
        curated = db.execute("""SELECT word, reading, meaning, order_index
            FROM kanji_related_words WHERE kanji=? ORDER BY order_index""", (char,)).fetchall()
        if curated:
            return [row(item) for item in curated]
        # Keep lookup useful for characters that do not yet have curated data.
        return [row(item) for item in db.execute("SELECT word, reading, meaning FROM vocabulary WHERE word LIKE ? ORDER BY id LIMIT 8", (f"%{char}%",)).fetchall()]

@app.get("/kanji/{char}/related-kanji")
def related_kanji(char: str):
    with connect() as db:
        return [row(item) for item in db.execute("""SELECT related_char, meaning, order_index
            FROM kanji_related_characters WHERE kanji=? ORDER BY order_index""", (char,)).fetchall()]

@app.get("/vocabulary")
def vocabulary(level: str | None = None, lesson_id: int | None = None):
    clauses, values = [], []
    if level: clauses.append("level = ?"); values.append(level.upper())
    if lesson_id: clauses.append("lesson_id = ?"); values.append(lesson_id)
    query = "SELECT * FROM vocabulary" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY id"
    with connect() as db: return [row(x) for x in db.execute(query, values).fetchall()]

@app.get("/vocabulary/search")
def search_vocabulary(q: str):
    with connect() as db: return [row(x) for x in db.execute("SELECT * FROM vocabulary WHERE word LIKE ? OR reading LIKE ? OR meaning LIKE ?", (f"%{q}%",) * 3).fetchall()]


def normalized_jlpt_level(level: str) -> str:
    normalized = level.strip().upper()
    if normalized not in {"N1", "N2", "N3", "N4", "N5"}:
        raise HTTPException(422, "Cấp độ JLPT không hợp lệ")
    return normalized


@app.get("/lesson-groups")
def list_lesson_groups(level: str = "N5"):
    """Return the vocabulary curriculum in the shape used by the learner UI."""
    with connect() as db:
        groups = db.execute(
            "SELECT * FROM lesson_groups WHERE level=? ORDER BY order_index, id",
            (normalized_jlpt_level(level),),
        ).fetchall()
        result = []
        for group in groups:
            lessons = db.execute(
                """SELECT l.*, COUNT(v.id) AS word_count
                    FROM lessons l
                    LEFT JOIN vocabulary v ON v.lesson_id=l.id
                    WHERE l.group_id=?
                    GROUP BY l.id
                    HAVING COUNT(v.id) > 0
                    ORDER BY l.order_index, l.id""",
                (group["id"],),
            ).fetchall()
            result.append({**row(group), "lessons": [row(lesson) for lesson in lessons]})
    return result


@app.get("/lessons/{lesson_id}")
def lesson_detail(lesson_id: int):
    with connect() as db:
        lesson = db.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone()
        if not lesson:
            raise HTTPException(404, "Không tìm thấy bài học")
        words = db.execute(
            "SELECT * FROM vocabulary WHERE lesson_id=? ORDER BY id",
            (lesson_id,),
        ).fetchall()
    return {**row(lesson), "vocabulary": [row(word) for word in words]}


@app.get("/grammar/lessons")
def grammar_lessons(level: str = "N5"):
    with connect() as db:
        lessons = db.execute(
            """SELECT l.*, COUNT(p.id) AS pattern_count
                FROM grammar_lessons l
                LEFT JOIN grammar_patterns p ON p.lesson_id=l.id
                WHERE l.level=?
                GROUP BY l.id
                ORDER BY l.order_index, l.id""",
            (normalized_jlpt_level(level),),
        ).fetchall()
    return [row(lesson) for lesson in lessons]


@app.get("/grammar/lessons/{lesson_id}")
def grammar_lesson_detail(lesson_id: int):
    with connect() as db:
        lesson = db.execute("SELECT * FROM grammar_lessons WHERE id=?", (lesson_id,)).fetchone()
        if not lesson:
            raise HTTPException(404, "Không tìm thấy bài ngữ pháp")
        patterns = db.execute(
            "SELECT * FROM grammar_patterns WHERE lesson_id=? ORDER BY id",
            (lesson_id,),
        ).fetchall()
        detail = []
        for pattern in patterns:
            examples = db.execute(
                "SELECT * FROM grammar_examples WHERE pattern_id=? ORDER BY id",
                (pattern["id"],),
            ).fetchall()
            detail.append({**row(pattern), "examples": [row(example) for example in examples]})
    return {**row(lesson), "patterns": detail}


@app.get("/admin/content-audit")
def content_audit(_: None = Depends(require_admin)):
    """Report content that needs editorial work without changing learner data."""
    with connect() as db:
        missing_kanji = db.execute("""SELECT char, level FROM kanji
            WHERE TRIM(meaning)='' OR TRIM(on_reading)='' OR TRIM(kun_reading)='' OR TRIM(radical)='' OR strokes<1
            ORDER BY level, char LIMIT 30""").fetchall()
        missing_vocabulary = db.execute("""SELECT id, word, reading, level FROM vocabulary
            WHERE TRIM(reading)='' OR TRIM(meaning)='' ORDER BY level, id LIMIT 30""").fetchall()
        missing_examples = db.execute("""SELECT id, word, reading, level FROM vocabulary
            WHERE level='N5' AND (TRIM(example_japanese)='' OR TRIM(example_meaning)='') ORDER BY id LIMIT 30""").fetchall()
        unassigned_vocabulary = db.execute("""SELECT id, word, reading, level FROM vocabulary
            WHERE lesson_id IS NULL ORDER BY level, id LIMIT 30""").fetchall()
        missing_patterns = db.execute("""SELECT p.id, l.level, p.formula FROM grammar_patterns p
            JOIN grammar_lessons l ON l.id=p.lesson_id
            WHERE TRIM(p.formula)='' OR TRIM(p.explanation_vi)='' OR TRIM(p.note)='' ORDER BY l.level, p.id LIMIT 30""").fetchall()
        missing_counts = {
            "kanji_fields": db.execute("SELECT COUNT(*) FROM kanji WHERE TRIM(meaning)='' OR TRIM(on_reading)='' OR TRIM(kun_reading)='' OR TRIM(radical)='' OR strokes<1").fetchone()[0],
            "vocabulary_fields": db.execute("SELECT COUNT(*) FROM vocabulary WHERE TRIM(reading)='' OR TRIM(meaning)=''").fetchone()[0],
            "n5_examples": db.execute("SELECT COUNT(*) FROM vocabulary WHERE level='N5' AND (TRIM(example_japanese)='' OR TRIM(example_meaning)='')").fetchone()[0],
            "vocabulary_without_lesson": db.execute("SELECT COUNT(*) FROM vocabulary WHERE lesson_id IS NULL").fetchone()[0],
            "grammar_fields": db.execute("SELECT COUNT(*) FROM grammar_patterns WHERE TRIM(formula)='' OR TRIM(explanation_vi)='' OR TRIM(note)=''").fetchone()[0],
        }
        return {
            "missing": {
                "kanji_fields": {"count": missing_counts["kanji_fields"], "items": [row(item) for item in missing_kanji]},
                "vocabulary_fields": {"count": missing_counts["vocabulary_fields"], "items": [row(item) for item in missing_vocabulary]},
                "n5_examples": {"count": missing_counts["n5_examples"], "items": [row(item) for item in missing_examples]},
                "vocabulary_without_lesson": {"count": missing_counts["vocabulary_without_lesson"], "items": [row(item) for item in unassigned_vocabulary]},
                "grammar_fields": {"count": missing_counts["grammar_fields"], "items": [row(item) for item in missing_patterns]},
            },
            "note": "Báo cáo chỉ đọc; không xóa dữ liệu và không ảnh hưởng tiến độ học.",
        }


@app.get("/admin/vocabulary-staging")
def vocabulary_staging(level: str = "N5", status_filter: str = "review", _: None = Depends(require_admin)):
    if status_filter not in {"review", "approved", "rejected"}:
        raise HTTPException(422, "Trạng thái staging không hợp lệ")
    with connect() as db:
        return [row(x) for x in db.execute("SELECT * FROM vocabulary_staging WHERE level=? AND status=? ORDER BY suggested_topic, id", (level.upper(), status_filter)).fetchall()]


@app.patch("/admin/kanji/{char}")
def update_kanji(char: str, item: KanjiUpdate, _: None = Depends(require_admin)):
    fields = item.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(422, "Chưa có nội dung để cập nhật")
    assignments = ", ".join(f"{field}=?" for field in fields)
    with connect() as db:
        updated = db.execute(f"UPDATE kanji SET {assignments} WHERE char=?", (*fields.values(), char)).rowcount
        if not updated:
            raise HTTPException(404, "Không tìm thấy Kanji")
        return row(db.execute("SELECT * FROM kanji WHERE char=?", (char,)).fetchone())


@app.patch("/admin/lessons/{lesson_id}")
def update_lesson(lesson_id: int, item: LessonUpdate, _: None = Depends(require_admin)):
    fields = item.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(422, "Chưa có nội dung để cập nhật")
    with connect() as db:
        if "group_id" in fields and not db.execute("SELECT 1 FROM lesson_groups WHERE id=?", (fields["group_id"],)).fetchone():
            raise HTTPException(404, "Không tìm thấy nhóm bài học")
        assignments = ", ".join(f"{field}=?" for field in fields)
        updated = db.execute(f"UPDATE lessons SET {assignments} WHERE id=?", (*fields.values(), lesson_id)).rowcount
        if not updated:
            raise HTTPException(404, "Không tìm thấy bài học")
        return row(db.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone())


@app.patch("/admin/vocabulary/{vocabulary_id}")
def update_vocabulary(vocabulary_id: int, item: VocabularyUpdate, _: None = Depends(require_admin)):
    fields = item.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(422, "Chưa có nội dung để cập nhật")
    with connect() as db:
        if "lesson_id" in fields and not db.execute("SELECT 1 FROM lessons WHERE id=?", (fields["lesson_id"],)).fetchone():
            raise HTTPException(404, "Không tìm thấy bài học")
        assignments = ", ".join(f"{field}=?" for field in fields)
        updated = db.execute(f"UPDATE vocabulary SET {assignments} WHERE id=?", (*fields.values(), vocabulary_id)).rowcount
        if not updated:
            raise HTTPException(404, "Không tìm thấy từ vựng")
        return row(db.execute("SELECT * FROM vocabulary WHERE id=?", (vocabulary_id,)).fetchone())


@app.patch("/admin/grammar/patterns/{pattern_id}")
def update_grammar_pattern(pattern_id: int, item: GrammarPatternUpdate, _: None = Depends(require_admin)):
    fields = item.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(422, "Chưa có nội dung để cập nhật")
    assignments = ", ".join(f"{field}=?" for field in fields)
    with connect() as db:
        updated = db.execute(f"UPDATE grammar_patterns SET {assignments} WHERE id=?", (*fields.values(), pattern_id)).rowcount
        if not updated:
            raise HTTPException(404, "Không tìm thấy mẫu ngữ pháp")
        return row(db.execute("SELECT * FROM grammar_patterns WHERE id=?", (pattern_id,)).fetchone())


@app.post("/admin/maintenance/reconcile")
def reconcile_content(_: None = Depends(require_admin)):
    """Re-run idempotent imports; users, sessions and progress are never cleared."""
    with connect() as db:
        progress_before = db.execute("SELECT COUNT(*) FROM user_progress").fetchone()[0]
    initialize_database()
    with connect() as db:
        progress_after = db.execute("SELECT COUNT(*) FROM user_progress").fetchone()[0]
        counts = {
            "kanji": db.execute("SELECT COUNT(*) FROM kanji").fetchone()[0],
            "vocabulary": db.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0],
            "grammar_patterns": db.execute("SELECT COUNT(*) FROM grammar_patterns").fetchone()[0],
        }
    return {"ok": True, "message": "Đã đối soát và nhập bổ sung dữ liệu.", "progress_before": progress_before, "progress_after": progress_after, "counts": counts}


@app.post("/admin/kanji", status_code=status.HTTP_201_CREATED)
def add_kanji(item: KanjiCreate, _: None = Depends(require_admin)):
    try:
        with connect() as db:
            db.execute("""INSERT INTO kanji(char,meaning,on_reading,kun_reading,strokes,level,radical,han_viet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", tuple(item.model_dump().values()))
    except Exception as error:
        raise HTTPException(409, "Kanji này đã tồn tại") from error
    return item


@app.post("/admin/lessons", status_code=status.HTTP_201_CREATED)
def add_lesson(item: LessonCreate, _: None = Depends(require_admin)):
    with connect() as db:
        result = db.execute("INSERT INTO lessons(level,title,description,order_index) VALUES (?, ?, ?, ?)", tuple(item.model_dump().values()))
    return {"id": result.lastrowid, **item.model_dump()}


@app.post("/admin/vocabulary", status_code=status.HTTP_201_CREATED)
def add_vocabulary(item: VocabularyCreate, _: None = Depends(require_admin)):
    with connect() as db:
        if item.lesson_id and not db.execute("SELECT 1 FROM lessons WHERE id = ?", (item.lesson_id,)).fetchone():
            raise HTTPException(404, "Không tìm thấy bài học")
        result = db.execute("INSERT INTO vocabulary(lesson_id,word,reading,meaning,level) VALUES (?, ?, ?, ?, ?)", tuple(item.model_dump().values()))
    return {"id": result.lastrowid, **item.model_dump()}
@app.post("/api/recognition")
def recognition(request: RecognitionRequest):
    # Request more candidates so a correct, stroke-compatible character can
    # move into the visible top three without excluding generic DaKanji output.
    try:
        if request.language == "zh" and request.image and request.rasterized:
            predictions = recognize_hanzi_rasterized_png(canvas_png(request.image), request.top_k)
        elif request.image and request.rasterized:
            predictions = recognize_rasterized_png(canvas_png(request.image), 30)
        elif request.strokes is not None:
            predictions = recognize_rasterized_strokes(rasterize_strokes(request.strokes, request.canvas_size), 30)
        elif request.image:
            predictions = recognize(canvas_png(request.image), 30)
        else:
            raise HTTPException(422, "Hãy gửi ảnh hoặc dữ liệu nét viết")
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    if request.language == "ja":
        predictions = rank_with_stroke_count(predictions, request.stroke_count)[:request.top_k]
    status_info = hanzi_model_status() if request.language == "zh" else model_status()
    if not predictions:
        message = "AI đang thu thập mẫu; chưa có mô hình đã huấn luyện để nhận diện."
        if ML_IMPORT_ERROR:
            message = "Thiếu gói AI trong môi trường backend. Hãy cài backend/requirements-ml.txt."
        return {"predictions": [], "uncertain": True, **status_info, "message": message}
    return {"predictions": predictions, "language": request.language, "uncertain": predictions[0]["confidence"] < 0.7, **status_info}

@app.get("/api/handwriting/status")
def handwriting_status():
    with connect() as db:
        samples = db.execute("SELECT COUNT(*) FROM handwriting_samples").fetchone()[0]
        labels = db.execute("SELECT COUNT(DISTINCT expected_text) FROM handwriting_samples").fetchone()[0]
    return {**model_status(), "samples": samples, "sample_labels": labels, "next_step": "Huấn luyện mô hình khi đã có đủ mẫu viết cho từng chữ."}

@app.post("/api/handwriting/samples", status_code=status.HTTP_201_CREATED)
def save_handwriting_sample(request: HandwritingSampleCreate):
    raw = canvas_png(request.image)
    digest = sha256(raw).hexdigest()
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    file_path = SAMPLES_DIR / f"{digest}.png"
    with connect() as db:
        previous = db.execute("SELECT id FROM handwriting_samples WHERE image_sha256=?", (digest,)).fetchone()
        if previous:
            return {"id": previous[0], "saved": False, "message": "Mẫu viết này đã được lưu trước đó."}
        file_path.write_bytes(raw)
        result = db.execute("INSERT INTO handwriting_samples(expected_text,image_path,image_sha256,source) VALUES (?, ?, ?, ?)", (request.expected_text, str(file_path.relative_to(Path(__file__).parent)), digest, request.source))
    return {"id": result.lastrowid, "saved": True, "message": "Đã lưu mẫu để huấn luyện AI."}
