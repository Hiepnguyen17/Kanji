from base64 import b64decode
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from database import connect, initialize_database

@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield

app = FastAPI(title="KanjiAI API", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class RecognitionRequest(BaseModel): image: str; top_k: int = Field(default=3, ge=1, le=3)
class KanjiCreate(BaseModel):
    char: str = Field(min_length=1, max_length=1); meaning: str = Field(min_length=1); on_reading: str; kun_reading: str
    strokes: int = Field(ge=1, le=99); level: str = Field(pattern="^N[1-5]$"); radical: str = Field(min_length=1)
class LessonCreate(BaseModel):
    level: str = Field(pattern="^N[1-5]$"); title: str = Field(min_length=1, max_length=120); description: str = ""; order_index: int = Field(default=0, ge=0)
class VocabularyCreate(BaseModel):
    lesson_id: int | None = Field(default=None, ge=1); word: str = Field(min_length=1); reading: str = Field(min_length=1)
    meaning: str = Field(min_length=1); level: str = Field(pattern="^N[1-5]$")

def row(item): return dict(item) if item else None

@app.get("/health")
def health(): return {"status":"ok", "model":"demo", "database":"sqlite"}

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

@app.get("/lessons")
def list_lessons(level: str | None = None):
    query, values = "SELECT * FROM lessons", []
    if level: query += " WHERE level = ?"; values.append(level.upper())
    with connect() as db: return [row(x) for x in db.execute(query + " ORDER BY level, order_index, id", values).fetchall()]

@app.get("/lessons/{lesson_id}")
def lesson_detail(lesson_id: int):
    with connect() as db:
        lesson = db.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
        words = db.execute("SELECT * FROM vocabulary WHERE lesson_id = ? ORDER BY id", (lesson_id,)).fetchall()
    if not lesson: raise HTTPException(404, "Không tìm thấy bài học")
    return {**row(lesson), "vocabulary":[row(x) for x in words]}

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
    try: b64decode(request.image.split(",",1)[-1], validate=True)
    except Exception as error: raise HTTPException(422, "Ảnh canvas không hợp lệ") from error
    return {"predictions":[{"kanji":"食","confidence":0.968},{"kanji":"良","confidence":0.014},{"kanji":"会","confidence":0.009}][:request.top_k], "uncertain":False}
