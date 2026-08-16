"""SQLite storage and initial data for KanjiAI."""
from pathlib import Path
import sqlite3
from n5_curriculum import LESSONS, WORDS

DB_PATH = Path(__file__).parent / "kanjiai.db"
SEED_KANJI = [("日","ngày, mặt trời","ニチ・ジツ","ひ・か",4,"N5","日"),("人","người","ジン・ニン","ひと",2,"N5","人"),("学","học","ガク","まな.ぶ",8,"N5","子"),("食","ăn, thực phẩm","ショク・ジキ","た.べる",9,"N5","食"),("水","nước","スイ","みず",4,"N5","水"),("本","sách, gốc","ホン","もと",5,"N5","木"),("会","gặp gỡ, hội","カイ・エ","あ.う",6,"N5","人"),("山","núi","サン","やま",3,"N5","山"),("木","cây, gỗ","モク・ボク","き・こ",4,"N5","木"),("書","viết, sách","ショ","か.く",10,"N5","曰")]

def connect():
    db = sqlite3.connect(DB_PATH); db.row_factory = sqlite3.Row; db.execute("PRAGMA foreign_keys = ON")
    return db

def initialize_database():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS kanji (char TEXT PRIMARY KEY, meaning TEXT NOT NULL, on_reading TEXT NOT NULL, kun_reading TEXT NOT NULL, strokes INTEGER NOT NULL CHECK(strokes > 0), level TEXT NOT NULL, radical TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS lessons (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', order_index INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS vocabulary (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_id INTEGER REFERENCES lessons(id) ON DELETE SET NULL, word TEXT NOT NULL, reading TEXT NOT NULL, meaning TEXT NOT NULL, level TEXT NOT NULL);
        """)
        for kanji in SEED_KANJI: db.execute("INSERT OR IGNORE INTO kanji VALUES (?, ?, ?, ?, ?, ?, ?)", kanji)
        for level, title, description, order_index in LESSONS:
            db.execute("""INSERT INTO lessons(level,title,description,order_index)
                SELECT ?, ?, ?, ? WHERE NOT EXISTS(SELECT 1 FROM lessons WHERE level=? AND title=?)""", (level,title,description,order_index,level,title))
        for order_index, word, reading, meaning in WORDS:
            lesson_title = LESSONS[order_index - 1][1]
            lesson = db.execute("SELECT id FROM lessons WHERE level='N5' AND title=?", (lesson_title,)).fetchone()
            db.execute("""INSERT INTO vocabulary(lesson_id,word,reading,meaning,level)
                SELECT ?, ?, ?, ?, 'N5' WHERE NOT EXISTS(SELECT 1 FROM vocabulary WHERE lesson_id=? AND word=? AND reading=?)""", (lesson[0],word,reading,meaning,lesson[0],word,reading))
