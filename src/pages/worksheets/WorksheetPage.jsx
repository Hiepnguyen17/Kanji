import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useLocation } from 'react-router-dom';
import { apiFetch, useRemoteJson } from '../../api/client';
import { paginateBlocks, selectWorksheetItems, shuffled, worksheetKey, WORKSHEET_LIMIT } from '../../lib/worksheets';
import '../../styles/worksheets.css';

async function getJson(path, signal) {
  const response = await apiFetch(path, { signal });
  if (!response.ok) throw new Error(response.status === 401 ? 'Hãy đăng nhập để lấy danh sách ôn tập.' : 'Không tải được nội dung. Hãy thử lại.');
  return response.json();
}

function useWorksheetSource({ source, type, level, day, endDay, lesson, char, user, retry }) {
  const [result, setResult] = useState({ key: '', items: [], status: 'loading', title: '' });
  const key = JSON.stringify([source, type, level, day, endDay, lesson, char, user?.id, retry]);
  useEffect(() => {
    const controller = new AbortController(), signal = controller.signal;
    setResult({ key, items: [], status: 'loading', title: '' });
    async function load() {
      if (source === 'single' && type === 'kanji' && char) {
        const item = await getJson(`/api/kanji/${encodeURIComponent(char)}`, signal);
        return { items: [item], title: `Kanji ${item.char} · ${item.level}` };
      }
      if (source === 'review') {
        if (!user) throw new Error('Hãy đăng nhập để tạo phiếu từ danh sách ôn tập.');
        const saved = (await getJson('/review-items', signal)).filter(item => item.content_type === type);
        if (type === 'kanji') {
          const library = await getJson('/api/kanji', signal);
          const byChar = new Map(library.map(item => [item.char, item]));
          return { items: saved.map(item => byChar.get(item.content_id)).filter(Boolean), title: 'Kanji đã lưu ôn tập' };
        }
        const ids = [...new Set(saved.map(item => item.href.match(/\/lesson\/(\d+)/)?.[1]).filter(Boolean))];
        // Small batches avoid flooding the API for a large saved collection.
        const byId = new Map();
        for (let start = 0; start < ids.length; start += 4) {
          const lessons = await Promise.all(ids.slice(start, start + 4).map(id => getJson(`/lessons/${id}`, signal)));
          lessons.forEach(item => item.vocabulary.forEach(word => byId.set(`word-${word.id}`, word)));
        }
        return { items: saved.map(item => byId.get(item.content_id)).filter(Boolean), title: 'Từ vựng đã lưu ôn tập' };
      }
      if (type === 'kanji') {
        const library = await getJson(`/api/kanji?level=${level}`, signal);
        return { items: library.slice((day - 1) * 10, endDay * 10), title: `Kanji ${level} · Ngày ${day}${endDay !== day ? `–${endDay}` : ''}`, days: Math.ceil(library.length / 10) };
      }
      if (!lesson) return { items: [], title: 'Chọn một bài từ vựng' };
      const data = await getJson(`/lessons/${lesson}`, signal);
      if (data.level !== level) throw new Error('Bài học không thuộc cấp độ đang chọn. Hãy chọn lại bài.');
      return { items: data.vocabulary, title: `${level} · ${data.title}` };
    }
    load().then(data => { if (!signal.aborted) setResult({ key, ...data, status: 'ready' }); })
      .catch(error => { if (!signal.aborted) setResult({ key, items: [], status: 'error', error: error.message, title: '' }); });
    return () => controller.abort();
  }, [key]);
  return result.key === key ? result : { key, items: [], status: 'loading', title: '' };
}

function useStrokeData(chars) {
  const [result, setResult] = useState({ key: '', paths: {}, missing: [] });
  const key = chars.join('');
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      const paths = {}, missing = [];
      for (let i = 0; i < chars.length; i += 6) {
        await Promise.all(chars.slice(i, i + 6).map(async char => {
          try {
            // These are frontend static assets, not files on the API origin.
            const code = char.codePointAt(0).toString(16).padStart(5, '0');
            const response = await fetch(`/kanjivg/${code}.svg`, { signal: controller.signal });
            if (!response.ok) throw new Error();
            const doc = new DOMParser().parseFromString(await response.text(), 'image/svg+xml');
            const strokes = [...doc.querySelectorAll('path')].map(path => path.getAttribute('d')).filter(Boolean);
            if (doc.querySelector('parsererror') || !strokes.length) throw new Error();
            const numbers = [...doc.querySelectorAll('text')].map(node => ({ text: node.textContent, transform: node.getAttribute('transform'), x: node.getAttribute('x'), y: node.getAttribute('y') }));
            paths[char] = { strokes, numbers };
          } catch { missing.push(char); }
        }));
        if (controller.signal.aborted) return;
      }
      setResult({ key, paths, missing });
    }
    load();
    return () => controller.abort();
  }, [key]);
  return result.key === key ? { ...result, ready: true } : { paths: {}, missing: [], ready: false };
}

function Glyph({ char, data, step, numbered = false }) {
  if (!data) return <span>{char}</span>;
  return <svg viewBox="0 0 109 109" aria-label={step == null ? `Chữ ${char}` : `Nét ${step + 1}`}>
    <g fill="none" stroke="#171717" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">{data.strokes.map((d, index) => <path key={index} d={d} stroke={step != null && index > step ? '#ddd' : '#171717'} />)}</g>
    {numbered && <g fontSize="8" fill="#333">{data.numbers.map((number, index) => <text key={index} transform={number.transform || undefined} x={number.x || undefined} y={number.y || undefined}>{number.text}</text>)}</g>}
  </svg>;
}

function PracticeRow({ word, size, data }) {
  const chars = Array.from(word), repeats = Math.max(2, Math.floor((179 + 2) / (size * chars.length + 2)));
  return <div className="ws-practice" style={{ '--cell': `${size}mm` }}>
    {Array.from({ length: repeats }, (_, repeat) => <div className={`ws-word-cells ${repeat === 0 ? 'ws-trace' : ''}`} key={repeat}>{chars.map((char, index) => <div className="ws-cell" key={index}>{repeat === 0 && <Glyph char={char} data={data?.[char]} />}</div>)}</div>)}
  </div>;
}

function WorksheetBlock({ item, number, mode, size, reading, examples, direction, strokes }) {
  if (mode === 'kanji') {
    const data = strokes[item.char];
    return <article className="ws-block"><div className="ws-kanji-heading"><div className="ws-model"><Glyph char={item.char} data={data} numbered /></div><div><b>{number}. {item.char} · {item.han_viet || ''}</b><p>{item.meaning}</p>{reading && <small>On: {item.on_reading || '—'} · Kun: {item.kun_reading || '—'}</small>}</div></div>
      {data ? <div className="ws-steps">{data.strokes.map((_, index) => <div key={index}><Glyph char={item.char} data={data} step={index} /><small>{index + 1}</small></div>)}</div> : <small>Chưa có sơ đồ nét; luyện viết theo chữ mẫu.</small>}
      <PracticeRow word={item.char} size={size} data={strokes} /><div className="ws-self-check">□ Cần ôn lại</div></article>;
  }
  if (mode === 'check') return <article className="ws-block ws-question"><b>{number}. {direction === 'meaning' ? `${item.meaning} · ${item.reading}` : item.word}</b>
    {direction === 'meaning' ? <p>Viết từ tiếng Nhật: <span className="ws-answer-line" /></p> : <><p>Cách đọc: <span className="ws-answer-line" /></p><p>Nghĩa: <span className="ws-answer-line" /></p></>}<small>□ Cần ôn lại</small></article>;
  return <article className="ws-block"><div className="ws-word-heading"><b>{number}. <span lang="ja">{item.word}</span></b>{reading && <span>{item.reading}</span>}<span>{item.meaning}</span></div>
    {examples && item.example_japanese && <div className="ws-example"><p lang="ja">{item.example_japanese}</p>{reading && item.example_reading && <small>{item.example_reading}</small>}{item.example_meaning && <p>{item.example_meaning}</p>}</div>}
    <PracticeRow word={item.word} size={size} /><p className="ws-sentence">Tự đặt câu: ........................................................................................................</p><small>□ Cần ôn lại</small></article>;
}

function Paper({ pages, blocks, title, mode }) {
  return pages.map((indices, page) => <section className="ws-sheet" key={page} aria-label={`Trang ${page + 1}`}>
    <div className="ws-sheet-head"><div><b>KanjiAI · {mode === 'kanji' ? 'Luyện viết Kanji' : mode === 'check' ? 'Tự kiểm tra từ vựng' : 'Luyện viết từ vựng'}</b><p>{title}</p></div><small>Họ tên: ........................<br />Ngày: ...... / ...... / ........</small></div>
    <div className="ws-sheet-body">{indices.map(index => <div key={index}>{blocks[index]}</div>)}</div>
    <div className="ws-sheet-foot"><span>kanjiai.online · {mode === 'kanji' ? 'Nét: KanjiVG / Ulrich Apel · CC BY-SA 3.0 · kanjivg.tagaini.net' : 'Từ điển tham khảo: JMdict / EDRDG · CC BY-SA 4.0'}</span><span>{page + 1}/{pages.length}</span></div>
  </section>);
}

export default function WorksheetPage({ go, user, initialConfig, compact = false }) {
  const location = useLocation(), params = new URLSearchParams(initialConfig || location.search);
  const [type, setType] = useState(params.get('type') === 'vocabulary' ? 'vocabulary' : 'kanji');
  const [source, setSource] = useState(['review', 'single'].includes(params.get('source')) ? params.get('source') : 'course');
  const [char] = useState(params.get('char') || '');
  const [level, setLevel] = useState(/^N[1-5]$/.test(params.get('level')) ? params.get('level') : 'N5');
  const initialDay = Math.max(1, Math.floor(Number(params.get('day')) || 1));
  const [day, setDay] = useState(initialDay), [endDay, setEndDay] = useState(initialDay);
  const [lesson, setLesson] = useState(/^\d+$/.test(params.get('lesson')) ? params.get('lesson') : '');
  const [vocabMode, setVocabMode] = useState(params.get('mode') === 'check' ? 'check' : 'vocab'), [size, setSize] = useState([10, 12, 15].includes(Number(params.get('size'))) ? Number(params.get('size')) : 12);
  const [reading, setReading] = useState(params.get('reading') !== '0'), [examples, setExamples] = useState(params.get('examples') !== '0'), [answers, setAnswers] = useState(params.get('answers') !== '0'), [direction, setDirection] = useState(params.get('direction') === 'meaning' ? 'meaning' : 'word');
  const [retry, setRetry] = useState(0), [selection, setSelection] = useState({ key: '', ids: new Set(), order: [] });
  const [printing, setPrinting] = useState(false), [printError, setPrintError] = useState('');
  const groups = useRemoteJson(!compact && type === 'vocabulary' && source === 'course' ? `/lesson-groups?level=${level}` : null);
  const data = useWorksheetSource({ source, type, level, day, endDay, lesson, char, user, retry });
  useEffect(() => {
    if (data.status === 'ready') setSelection({ key: data.key, ids: new Set(data.items.slice(0, WORKSHEET_LIMIT).map(worksheetKey)), order: data.items.map(worksheetKey) });
  }, [data.key, data.status]);
  const selected = selection.key === data.key ? selectWorksheetItems(data.items, selection.ids, selection.order) : [];
  const mode = type === 'kanji' ? 'kanji' : vocabMode;
  const strokeData = useStrokeData(type === 'kanji' ? selected.map(item => item.char) : []);
  const blocks = selected.map((item, index) => <WorksheetBlock key={worksheetKey(item)} item={item} number={index + 1} mode={mode} size={size} reading={reading} examples={examples} direction={direction} strokes={strokeData.paths} />);
  const questionCount = blocks.length;
  if (mode === 'check' && answers && selected.length) {
    // The answer sheet follows the exact same selected/shuffled order as the questions.
    for (let i = 0; i < selected.length; i += 10) blocks.push(<article className="ws-block ws-key" key={`answers-${i}`}><h3>Đáp án · Câu {i + 1}–{Math.min(i + 10, selected.length)}</h3>{selected.slice(i, i + 10).map((item, index) => <p key={item.id}><b>{i + index + 1}. {item.word}</b> · {item.reading} · {item.meaning}</p>)}</article>);
  }
  const measure = useRef(null), [layout, setLayout] = useState({ signature: '', pages: [], oversized: false });
  const [fontsReady, setFontsReady] = useState(false);
  useEffect(() => { let active = true; document.fonts.ready.then(() => { if (active) setFontsReady(true); }); return () => { active = false; }; }, []);
  const signature = JSON.stringify([data.key, selected.map(worksheetKey), mode, size, reading, examples, answers, direction, strokeData.ready, fontsReady]);
  useLayoutEffect(() => {
    if (!measure.current || !fontsReady || !strokeData.ready) return;
    const nodes = [...measure.current.querySelectorAll(':scope > .ws-measure-block')];
    const heights = nodes.map(node => node.getBoundingClientRect().height);
    const capacity = measure.current.querySelector('.ws-capacity').getBoundingClientRect().height;
    const gap = 4 * 96 / 25.4;
    const questions = paginateBlocks(heights.slice(0, questionCount), capacity, gap);
    const answerPages = paginateBlocks(heights.slice(questionCount), capacity, gap).map(page => page.map(index => index + questionCount));
    setLayout({ signature, pages: [...questions, ...answerPages], oversized: heights.some(height => height > capacity) });
  }, [signature]);
  const ready = selected.length > 0 && data.status === 'ready' && strokeData.ready && fontsReady && layout.signature === signature && !layout.oversized;
  const toggle = item => setSelection(current => {
    const ids = new Set(current.ids), id = worksheetKey(item);
    if (ids.has(id)) ids.delete(id); else if (ids.size < WORKSHEET_LIMIT) ids.add(id);
    return { ...current, ids };
  });
  const print = async () => {
    if (!ready) return;
    setPrinting(true); setPrintError('');
    try { await document.fonts.ready; window.print(); }
    catch { setPrintError('Không mở được hộp thoại in. Hãy thử trên trình duyệt máy tính.'); }
    finally { setPrinting(false); }
  };
  const printRoot = useRef(null);
  useEffect(() => {
    const node = document.createElement('div'); node.id = 'worksheet-print-root'; document.body.appendChild(node); printRoot.current = node;
    return () => { node.remove(); printRoot.current = null; };
  }, []);
  const resetLevel = value => { setLevel(value); setLesson(''); setDay(1); setEndDay(1); };
  const customize = () => go(`/worksheets?${new URLSearchParams({ type, source, level, day: String(day), lesson, char, mode: vocabMode, size: String(size), reading: reading ? '1' : '0', examples: examples ? '1' : '0', answers: answers ? '1' : '0', direction })}`);
  return <section className={`worksheet-page${compact ? ' ws-compact' : ''}`}>
    {!compact && <div className="ws-toolbar"><p className="eyebrow">HỌC TRÊN GIẤY</p><h1>Tạo phiếu học</h1><p>Chọn nội dung, xem trước trang A4 rồi in hoặc lưu PDF. Không thay đổi tiến độ học.</p></div>}
    <div className="ws-workspace"><div className="ws-controls">
      <h2>{compact ? 'Nội dung in' : '1. Chọn nội dung'}</h2>
      {compact ? <p className="ws-context-title">{data.title || 'Nội dung đang học'}</p> : <>
      <label>Loại nội dung<select value={type} onChange={event => { setType(event.target.value); if (source === 'single') setSource('course'); }}><option value="kanji">Kanji</option><option value="vocabulary">Từ vựng</option></select></label>
      <label>Nguồn<select value={source} onChange={event => setSource(event.target.value)}><option value="course">Bài học / lộ trình</option><option value="review">Đã lưu ôn tập</option>{char && type === 'kanji' && <option value="single">Chữ {char}</option>}</select></label>
      {source === 'course' && <><label>Cấp độ<select value={level} onChange={event => resetLevel(event.target.value)}>{['N5', 'N4', 'N3', 'N2', 'N1'].map(value => <option key={value}>{value}</option>)}</select></label>
        {type === 'kanji' ? <div className="ws-day-inputs"><label>Từ ngày<input type="number" min="1" max={data.days || 114} value={day} onChange={event => { const value = Math.min(data.days || 114, Math.max(1, Math.floor(Number(event.target.value) || 1))); setDay(value); setEndDay(value); }} /></label><label>Đến ngày<input type="number" min={day} max={Math.min(data.days || 114, day + 9)} value={endDay} onChange={event => setEndDay(Math.min(data.days || 114, day + 9, Math.max(day, Math.floor(Number(event.target.value) || day))))} /></label></div>
          : <><label>Bài từ vựng<select value={lesson} onChange={event => setLesson(event.target.value)}><option value="">Chọn bài học…</option>{(groups.data || []).map(group => <optgroup label={group.title} key={group.id}>{group.lessons.map(item => <option key={item.id} value={item.id}>{item.title} · {item.word_count} từ</option>)}</optgroup>)}</select></label>{groups.status === 'error' && <button onClick={groups.retry}>Tải lại danh sách bài</button>}{groups.status === 'loading' && <p>Đang tải danh sách bài…</p>}</>}
      </>}
      </>}
      {source === 'review' && !user && <button className="outline" onClick={() => go('/login')}>Đăng nhập Google</button>}
      {data.status === 'loading' && <p role="status">Đang tải nội dung…</p>}
      {data.status === 'error' && <p role="alert">{data.error} <button onClick={() => setRetry(value => value + 1)}>Thử lại</button></p>}
      {data.status === 'ready' && <><div className="ws-selection-head"><b>Đã chọn {selected.length}/{data.items.length}</b><button onClick={() => setSelection(current => ({ ...current, ids: new Set(data.items.slice(0, WORKSHEET_LIMIT).map(worksheetKey)) }))}>Chọn tất cả</button><button onClick={() => setSelection(current => ({ ...current, ids: new Set() }))}>Bỏ chọn</button></div><small>Tối đa {WORKSHEET_LIMIT} mục mỗi phiếu.</small><div className="ws-items">{data.items.map(item => <label key={worksheetKey(item)}><input type="checkbox" checked={selection.key === data.key && selection.ids.has(worksheetKey(item))} disabled={selected.length >= WORKSHEET_LIMIT && !selection.ids.has(worksheetKey(item))} onChange={() => toggle(item)} /><span><b>{item.char || item.word}</b> {item.reading || item.han_viet}<small>{item.meaning}</small></span></label>)}</div>{!data.items.length && <p>Chưa có nội dung. Hãy chọn bài hoặc lưu thêm mục ôn tập.</p>}</>}
      <h2>{compact ? 'Tùy chọn in' : '2. Chọn mẫu'}</h2>
      {type === 'vocabulary' ? <label>Mẫu phiếu<select value={vocabMode} onChange={event => setVocabMode(event.target.value)}><option value="vocab">Luyện viết từ vựng</option><option value="check">Tự kiểm tra từ vựng</option></select></label> : <p>Luyện viết Kanji · Mẫu nét → tô mờ → tự viết</p>}
      {mode !== 'check' ? <><label>Cỡ ô viết<select value={size} onChange={event => setSize(Number(event.target.value))}><option value="10">Nhỏ · 10 mm</option><option value="12">Vừa · 12 mm</option><option value="15">Lớn · 15 mm</option></select></label><label className="ws-checkbox"><input type="checkbox" checked={reading} onChange={event => setReading(event.target.checked)} />Hiện cách đọc</label>{mode === 'vocab' && <label className="ws-checkbox"><input type="checkbox" checked={examples} onChange={event => setExamples(event.target.checked)} />Hiện ví dụ nếu có</label>}</> : <><label>Dạng câu hỏi<select value={direction} onChange={event => setDirection(event.target.value)}><option value="word">Nhìn từ → điền cách đọc và nghĩa</option><option value="meaning">Nhìn nghĩa + cách đọc → viết từ</option></select></label><label className="ws-checkbox"><input type="checkbox" checked={answers} onChange={event => setAnswers(event.target.checked)} />Đáp án ở trang cuối</label><button className="outline" onClick={() => setSelection(current => ({ ...current, order: shuffled(current.order) }))}>Đảo thứ tự câu hỏi</button></>}
      <div className="ws-print-actions"><button className="primary" disabled={!ready || printing} onClick={print}>{printing ? 'Đang mở…' : `In / Lưu PDF${ready ? ` · ${layout.pages.length} trang` : ''}`}</button><small>Trong hộp thoại in: chọn A4, tỷ lệ 100%, tắt đầu/chân trang của trình duyệt. Chọn “Lưu dưới dạng PDF” để tải file.</small></div>
      {compact && <button className="ws-customize" onClick={customize}>Tùy chỉnh thêm / Gộp nhiều bài →</button>}
      {printError && <p role="alert">{printError}</p>}
      {!strokeData.ready && selected.length > 0 && <p role="status">Đang tải sơ đồ nét…</p>}
      {strokeData.missing.length > 0 && <p role="status">Thiếu SVG: {strokeData.missing.join('、')}. Các chữ này dùng chữ mẫu, không có sơ đồ nét.</p>}
      {layout.oversized && <p role="alert">Có mục dài quá một trang. Hãy tắt ví dụ, giảm cỡ ô hoặc bỏ chọn mục dài.</p>}
    </div><div className="ws-preview"><div className="ws-preview-label"><h2>Xem trước A4</h2><span>{ready ? `${layout.pages.length} trang · ${selected.length} mục` : 'Chọn nội dung để tạo phiếu'}</span></div>{ready ? <div className="ws-paper"><Paper pages={layout.pages} blocks={blocks} title={data.title} mode={mode} /></div> : <div className="ws-empty">{selected.length ? 'Đang chuẩn bị phiếu…' : 'Phiếu học sẽ xuất hiện tại đây.'}</div>}</div></div>
    <div className="ws-paper ws-measure" ref={measure} aria-hidden="true"><div className="ws-capacity" />{blocks.map((block, index) => <div className="ws-measure-block" key={index}>{block}</div>)}</div>
    {printRoot.current && createPortal(<div className="ws-paper">{ready && <Paper pages={layout.pages} blocks={blocks} title={data.title} mode={mode} />}</div>, printRoot.current)}
  </section>;
}
