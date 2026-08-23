"""SQLite storage and initial data for KanjiAI."""
from pathlib import Path
import sqlite3
from n5_curriculum import LESSONS, WORDS, VOCABULARY_GROUPS, LESSON_GROUPS, STAGING_TOPIC_GROUPS, STAGING_PROMOTIONS, N5_STAGING_WORDS
from n5_grammar import LESSONS as GRAMMAR_LESSONS, PATTERNS as GRAMMAR_PATTERNS, EXAMPLES as GRAMMAR_EXAMPLES

DB_PATH = Path(__file__).parent / "kanjiai.db"
SEED_KANJI = [("日","ngày, mặt trời","ニチ・ジツ","ひ・か",4,"N5","日"),("人","người","ジン・ニン","ひと",2,"N5","人"),("学","học","ガク","まな.ぶ",8,"N5","子"),("食","ăn, thực phẩm","ショク・ジキ","た.べる",9,"N5","食"),("水","nước","スイ","みず",4,"N5","水"),("本","sách, gốc","ホン","もと",5,"N5","木"),("会","gặp gỡ, hội","カイ・エ","あ.う",6,"N5","人"),("山","núi","サン","やま",3,"N5","山"),("木","cây, gỗ","モク・ボク","き・こ",4,"N5","木"),("書","viết, sách","ショ","か.く",10,"N5","曰")]

def connect():
    db = sqlite3.connect(DB_PATH); db.row_factory = sqlite3.Row; db.execute("PRAGMA foreign_keys = ON")
    return db

def initialize_database():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS kanji (char TEXT PRIMARY KEY, meaning TEXT NOT NULL, on_reading TEXT NOT NULL, kun_reading TEXT NOT NULL, strokes INTEGER NOT NULL CHECK(strokes > 0), level TEXT NOT NULL, radical TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS lesson_groups (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT NOT NULL, japanese_title TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', order_index INTEGER NOT NULL DEFAULT 0, UNIQUE(level, title));
        CREATE TABLE IF NOT EXISTS lessons (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', order_index INTEGER NOT NULL DEFAULT 0, group_id INTEGER REFERENCES lesson_groups(id) ON DELETE SET NULL);
        CREATE TABLE IF NOT EXISTS vocabulary (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_id INTEGER REFERENCES lessons(id) ON DELETE SET NULL, word TEXT NOT NULL, reading TEXT NOT NULL, meaning TEXT NOT NULL, level TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS vocabulary_staging (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT NOT NULL, suggested_topic TEXT NOT NULL, word TEXT NOT NULL, reading TEXT NOT NULL, meaning TEXT NOT NULL, source_note TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'review' CHECK(status IN ('review','approved','rejected')), UNIQUE(level, word, reading));
        CREATE TABLE IF NOT EXISTS grammar_lessons (id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL, order_index INTEGER NOT NULL, UNIQUE(level, title));
        CREATE TABLE IF NOT EXISTS grammar_patterns (id INTEGER PRIMARY KEY AUTOINCREMENT, lesson_id INTEGER NOT NULL REFERENCES grammar_lessons(id) ON DELETE CASCADE, formula TEXT NOT NULL, explanation_vi TEXT NOT NULL, note TEXT NOT NULL, UNIQUE(lesson_id, formula));
        CREATE TABLE IF NOT EXISTS grammar_examples (id INTEGER PRIMARY KEY AUTOINCREMENT, pattern_id INTEGER NOT NULL REFERENCES grammar_patterns(id) ON DELETE CASCADE, japanese TEXT NOT NULL, reading TEXT NOT NULL, meaning_vi TEXT NOT NULL, UNIQUE(pattern_id, japanese));
        """)
        # Migration for databases created before lesson groups were introduced.
        lesson_columns = {column["name"] for column in db.execute("PRAGMA table_info(lessons)")}
        if "group_id" not in lesson_columns:
            db.execute("ALTER TABLE lessons ADD COLUMN group_id INTEGER REFERENCES lesson_groups(id) ON DELETE SET NULL")
        for kanji in SEED_KANJI: db.execute("INSERT OR IGNORE INTO kanji VALUES (?, ?, ?, ?, ?, ?, ?)", kanji)
        for level, japanese_title, title, description, order_index in VOCABULARY_GROUPS:
            db.execute("""INSERT INTO lesson_groups(level,japanese_title,title,description,order_index)
                SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS(SELECT 1 FROM lesson_groups WHERE level=? AND title=?)""", (level,japanese_title,title,description,order_index,level,title))
        for level, title, description, order_index in LESSONS:
            db.execute("""INSERT INTO lessons(level,title,description,order_index)
                SELECT ?, ?, ?, ? WHERE NOT EXISTS(SELECT 1 FROM lessons WHERE level=? AND title=?)""", (level,title,description,order_index,level,title))
        for order_index, word, reading, meaning in WORDS:
            lesson_title = LESSONS[order_index - 1][1]
            lesson = db.execute("SELECT id FROM lessons WHERE level='N5' AND title=?", (lesson_title,)).fetchone()
            db.execute("""INSERT INTO vocabulary(lesson_id,word,reading,meaning,level)
                SELECT ?, ?, ?, ?, 'N5' WHERE NOT EXISTS(SELECT 1 FROM vocabulary WHERE lesson_id=? AND word=? AND reading=?)""", (lesson[0],word,reading,meaning,lesson[0],word,reading))
        for topic, word, reading, meaning in N5_STAGING_WORDS:
            db.execute("""INSERT INTO vocabulary_staging(level,suggested_topic,word,reading,meaning,source_note)
                SELECT 'N5', ?, ?, ?, ?, 'KanjiAI curated from JMdict/EDICT; needs curriculum review'
                WHERE NOT EXISTS(SELECT 1 FROM vocabulary WHERE level='N5' AND word=? AND reading=?)
                AND NOT EXISTS(SELECT 1 FROM vocabulary_staging WHERE level='N5' AND word=? AND reading=?)""", (topic,word,reading,meaning,word,reading,word,reading))
        # Existing lessons are placed by their actual topic; no vocabulary is discarded.
        for lesson_title, group_title in LESSON_GROUPS.items():
            group = db.execute("SELECT id FROM lesson_groups WHERE level='N5' AND title=?", (group_title,)).fetchone()
            if group:
                db.execute("UPDATE lessons SET group_id=? WHERE level='N5' AND title=?", (group[0], lesson_title))
        for old_topic, new_topic in STAGING_TOPIC_GROUPS.items():
            db.execute("UPDATE vocabulary_staging SET suggested_topic=? WHERE level='N5' AND suggested_topic=?", (new_topic, old_topic))
        for topic, promotion in STAGING_PROMOTIONS.items():
            title, description, order_index = promotion[:3]
            parent_topic = promotion[3] if len(promotion) > 3 else topic
            candidates = db.execute("SELECT * FROM vocabulary_staging WHERE level='N5' AND status='review' AND suggested_topic=? ORDER BY id LIMIT 10", (topic,)).fetchall()
            if len(candidates) != 10:
                continue
            group = db.execute("SELECT id FROM lesson_groups WHERE level='N5' AND title=?", (parent_topic,)).fetchone()
            if not group:
                continue
            db.execute("""INSERT INTO lessons(level,title,description,order_index,group_id)
                SELECT 'N5', ?, ?, ?, ? WHERE NOT EXISTS(SELECT 1 FROM lessons WHERE level='N5' AND title=?)""", (title,description,order_index,group[0],title))
            lesson = db.execute("SELECT id FROM lessons WHERE level='N5' AND title=? ORDER BY id LIMIT 1", (title,)).fetchone()
            for candidate in candidates:
                db.execute("""INSERT INTO vocabulary(lesson_id,word,reading,meaning,level)
                    SELECT ?, ?, ?, ?, 'N5' WHERE NOT EXISTS(SELECT 1 FROM vocabulary WHERE lesson_id=? AND word=? AND reading=?)""", (lesson[0],candidate['word'],candidate['reading'],candidate['meaning'],lesson[0],candidate['word'],candidate['reading']))
                db.execute("UPDATE vocabulary_staging SET status='approved' WHERE id=?", (candidate['id'],))
        # Remove only obsolete, empty parent groups from the earlier five-topic layout.
        for old_group in ("Làm quen & giới thiệu", "Học tập & thời gian", "Đời sống hằng ngày", "Thành phố & hoạt động", "Thiên nhiên & miêu tả"):
            db.execute("""DELETE FROM lesson_groups WHERE level='N5' AND title=?
                AND NOT EXISTS(SELECT 1 FROM lessons WHERE lessons.group_id=lesson_groups.id)""", (old_group,))
        # Correct legacy starter content whose old lesson title was too broad.
        legacy = db.execute("SELECT id FROM lessons WHERE level='N5' AND title='Cuộc sống hằng ngày' ORDER BY id LIMIT 1").fetchone()
        introduction = db.execute("SELECT id FROM lessons WHERE level='N5' AND title='Tự giới thiệu' ORDER BY id LIMIT 1").fetchone()
        food = db.execute("SELECT id FROM lessons WHERE level='N5' AND title='Ăn uống' ORDER BY id LIMIT 1").fetchone()
        animals = db.execute("SELECT id FROM lessons WHERE level='N5' AND title='Động vật gần gũi' ORDER BY id LIMIT 1").fetchone()
        family = db.execute("SELECT id FROM lessons WHERE level='N5' AND title='Gia đình' ORDER BY id LIMIT 1").fetchone()
        if legacy and introduction:
            db.execute("UPDATE vocabulary SET lesson_id=? WHERE lesson_id=? AND word='日本'", (introduction[0], legacy[0]))
        if legacy and food:
            db.execute("UPDATE vocabulary SET lesson_id=? WHERE lesson_id=? AND word='食べる'", (food[0], legacy[0]))
        if animals and family:
            db.execute("UPDATE vocabulary SET lesson_id=? WHERE lesson_id=? AND word='犬'", (animals[0], family[0]))
        if animals:
            # A previous seed placed 犬 in the family lesson. Keep only one identical card.
            db.execute("""DELETE FROM vocabulary WHERE lesson_id=? AND word='犬' AND reading='いぬ'
                AND id NOT IN (SELECT MIN(id) FROM vocabulary WHERE lesson_id=? AND word='犬' AND reading='いぬ')""", (animals[0], animals[0]))
        for level, title, description, order_index in GRAMMAR_LESSONS:
            db.execute("INSERT OR IGNORE INTO grammar_lessons(level,title,description,order_index) VALUES (?, ?, ?, ?)", (level,title,description,order_index))
        for lesson_order, formula, explanation, note in GRAMMAR_PATTERNS:
            lesson = db.execute("SELECT id FROM grammar_lessons WHERE level='N5' AND order_index=?", (lesson_order,)).fetchone()
            db.execute("INSERT OR IGNORE INTO grammar_patterns(lesson_id,formula,explanation_vi,note) VALUES (?, ?, ?, ?)", (lesson[0],formula,explanation,note))
        for pattern_offset, (_, japanese, reading, meaning) in enumerate(GRAMMAR_EXAMPLES):
            pattern = db.execute("SELECT id FROM grammar_patterns ORDER BY id LIMIT 1 OFFSET ?", (pattern_offset,)).fetchone()
            db.execute("INSERT OR IGNORE INTO grammar_examples(pattern_id,japanese,reading,meaning_vi) VALUES (?, ?, ?, ?)", (pattern[0],japanese,reading,meaning))
