from base64 import b64decode
from contextlib import asynccontextmanager
from hashlib import sha256
from math import pow
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from PIL import Image, ImageDraw
from database import connect, initialize_database
try:
    from recognizer import model_status, recognize, recognize_rasterized_png, recognize_rasterized_strokes
    ML_IMPORT_ERROR = None
except ModuleNotFoundError as error:
    # Keep the vocabulary API available if an optional ML package is not yet
    # installed in the backend virtual environment.
    ML_IMPORT_ERROR = str(error)

    def model_status():
        return {"model_status": "dependencies_missing", "labels": 0, "validation_accuracy": None}

    def recognize(_: bytes, __: int):
        return []

    def recognize_rasterized_strokes(_: object, __: int):
        return []

    def recognize_rasterized_png(_: bytes, __: int):
        return []

@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield

app = FastAPI(title="KanjiAI API", version="0.3.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class RecognitionRequest(BaseModel):
    image: str | None = None
    strokes: list[list[list[float]]] | None = None
    canvas_size: int = Field(default=400, ge=64, le=1024)
    rasterized: bool = False
    top_k: int = Field(default=3, ge=1, le=3)
    stroke_count: int | None = Field(default=None, ge=1, le=40)
    expected_text: str | None = Field(default=None, max_length=20)

class HandwritingSampleCreate(BaseModel):
    image: str
    expected_text: str = Field(min_length=1, max_length=20)
    source: str = Field(default="flashcard", pattern="^(flashcard|lookup)$")
class KanjiCreate(BaseModel):
    char: str = Field(min_length=1, max_length=1); meaning: str = Field(min_length=1); on_reading: str; kun_reading: str
    strokes: int = Field(ge=1, le=99); level: str = Field(pattern="^N[1-5]$"); radical: str = Field(min_length=1)
class LessonCreate(BaseModel):
    level: str = Field(pattern="^N[1-5]$"); title: str = Field(min_length=1, max_length=120); description: str = ""; order_index: int = Field(default=0, ge=0)
class VocabularyCreate(BaseModel):
    lesson_id: int | None = Field(default=None, ge=1); word: str = Field(min_length=1); reading: str = Field(min_length=1)
    meaning: str = Field(min_length=1); level: str = Field(pattern="^N[1-5]$")

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

@app.get("/kanji")
def list_kanji(level: str | None = None):
    query, values = "SELECT * FROM kanji", []
    if level: query += " WHERE level = ?"; values.append(level.upper())
    with connect() as db: return [row(x) for x in db.execute(query + " ORDER BY char", values).fetchall()]

@app.get("/kanji/{char}")
def kanji_detail(char: str):
    with connect() as db: item = db.execute("SELECT * FROM kanji WHERE char = ?", (char,)).fetchone()
    if not item: raise HTTPException(404, "Không tìm thấy Kanji")
    return row(item)

@app.get("/kanji/{char}/related-words")
def related_words(char: str):
    with connect() as db: return [row(x) for x in db.execute("SELECT * FROM vocabulary WHERE word LIKE ? ORDER BY id", (f"%{char}%",)).fetchall()]

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

@app.get("/admin/vocabulary-staging")
def vocabulary_staging(level: str = "N5", status_filter: str = "review"):
    with connect() as db:
        return [row(x) for x in db.execute("SELECT * FROM vocabulary_staging WHERE level=? AND status=? ORDER BY suggested_topic, id", (level.upper(), status_filter)).fetchall()]

@app.get("/lessons")
def list_lessons(level: str | None = None):
    query, values = "SELECT l.*, COUNT(v.id) AS word_count FROM lessons l LEFT JOIN vocabulary v ON v.lesson_id = l.id", []
    if level: query += " WHERE l.level = ?"; values.append(level.upper())
    query += " GROUP BY l.id ORDER BY l.level, l.order_index, l.id"
    with connect() as db: return [row(x) for x in db.execute(query, values).fetchall()]

@app.get("/lesson-groups")
def list_lesson_groups(level: str = "N5"):
    with connect() as db:
        groups = db.execute("SELECT * FROM lesson_groups WHERE level=? ORDER BY order_index, id", (level.upper(),)).fetchall()
        result = []
        for group in groups:
            lessons = db.execute("""SELECT l.*, COUNT(v.id) AS word_count
                FROM lessons l LEFT JOIN vocabulary v ON v.lesson_id=l.id
                WHERE l.group_id=? GROUP BY l.id HAVING COUNT(v.id) > 0
                ORDER BY l.order_index, l.id""", (group["id"],)).fetchall()
            result.append({**row(group), "lessons": [row(lesson) for lesson in lessons]})
    return result

@app.get("/lessons/{lesson_id}")
def lesson_detail(lesson_id: int):
    with connect() as db:
        lesson = db.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
        words = db.execute("SELECT * FROM vocabulary WHERE lesson_id = ? ORDER BY id", (lesson_id,)).fetchall()
    if not lesson: raise HTTPException(404, "Không tìm thấy bài học")
    return {**row(lesson), "vocabulary":[row(x) for x in words]}

@app.get("/grammar/lessons")
def grammar_lessons(level: str = "N5"):
    with connect() as db:
        return [row(x) for x in db.execute("SELECT * FROM grammar_lessons WHERE level = ? ORDER BY order_index", (level.upper(),)).fetchall()]

@app.get("/grammar/lessons/{lesson_id}")
def grammar_lesson_detail(lesson_id: int):
    with connect() as db:
        lesson = db.execute("SELECT * FROM grammar_lessons WHERE id = ?", (lesson_id,)).fetchone()
        patterns = db.execute("SELECT * FROM grammar_patterns WHERE lesson_id = ? ORDER BY id", (lesson_id,)).fetchall()
        detail = []
        for pattern in patterns:
            examples = db.execute("SELECT * FROM grammar_examples WHERE pattern_id = ? ORDER BY id", (pattern["id"],)).fetchall()
            detail.append({**row(pattern), "examples":[row(x) for x in examples]})
    if not lesson: raise HTTPException(404, "Không tìm thấy bài ngữ pháp")
    return {**row(lesson), "patterns": detail}

# Local MVP only: protect /admin routes with JWT before a public deployment.
@app.post("/admin/kanji", status_code=status.HTTP_201_CREATED)
def add_kanji(item: KanjiCreate):
    try:
        with connect() as db: db.execute("INSERT INTO kanji VALUES (?, ?, ?, ?, ?, ?, ?)", tuple(item.model_dump().values()))
    except Exception as error: raise HTTPException(409, "Kanji này đã tồn tại") from error
    return item

@app.post("/admin/lessons", status_code=status.HTTP_201_CREATED)
def add_lesson(item: LessonCreate):
    with connect() as db: result = db.execute("INSERT INTO lessons(level,title,description,order_index) VALUES (?, ?, ?, ?)", tuple(item.model_dump().values()))
    return {"id":result.lastrowid, **item.model_dump()}

@app.post("/admin/vocabulary", status_code=status.HTTP_201_CREATED)
def add_vocabulary(item: VocabularyCreate):
    with connect() as db:
        if item.lesson_id and not db.execute("SELECT 1 FROM lessons WHERE id = ?", (item.lesson_id,)).fetchone(): raise HTTPException(404, "Không tìm thấy bài học")
        result = db.execute("INSERT INTO vocabulary(lesson_id,word,reading,meaning,level) VALUES (?, ?, ?, ?, ?)", tuple(item.model_dump().values()))
    return {"id":result.lastrowid, **item.model_dump()}

@app.post("/api/recognition")
def recognition(request: RecognitionRequest):
    # Request more candidates so a correct, stroke-compatible character can
    # move into the visible top three without excluding generic DaKanji output.
    try:
        if request.image and request.rasterized:
            predictions = recognize_rasterized_png(canvas_png(request.image), 30)
        elif request.strokes is not None:
            predictions = recognize_rasterized_strokes(rasterize_strokes(request.strokes, request.canvas_size), 30)
        elif request.image:
            predictions = recognize(canvas_png(request.image), 30)
        else:
            raise HTTPException(422, "Hãy gửi ảnh hoặc dữ liệu nét viết")
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    predictions = rank_with_stroke_count(predictions, request.stroke_count)[:request.top_k]
    status_info = model_status()
    if not predictions:
        message = "AI đang thu thập mẫu; chưa có mô hình đã huấn luyện để nhận diện."
        if ML_IMPORT_ERROR:
            message = "Thiếu gói AI trong môi trường backend. Hãy cài backend/requirements-ml.txt."
        return {"predictions": [], "uncertain": True, **status_info, "message": message}
    return {"predictions": predictions, "uncertain": predictions[0]["confidence"] < 0.7, **status_info}

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
