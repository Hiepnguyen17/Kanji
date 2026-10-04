import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { matchesGrammarReference } from '../../lib/grammarAnswer';
import { practiceQuestions } from '../../data/grammarPractice';
import { apiFetch } from '../../api/client';

export default function GrammarExerciseButton({ pattern, level }) {
  const questions = practiceQuestions(pattern, level);
  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [checked, setChecked] = useState(null);
  const [showHint, setShowHint] = useState(false);
  const [showReference, setShowReference] = useState(false);
  const [aiFeedback, setAiFeedback] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [results, setResults] = useState([]);
  const inputRef = useRef(null);
  const aiRequest = useRef(null);

  const cancelAI = () => {
    aiRequest.current?.abort();
    aiRequest.current = null;
    setAiLoading(false);
    setAiFeedback(null);
  };

  const evaluateAI = async () => {
    const controller = new AbortController();
    aiRequest.current = controller;
    setAiLoading(true);
    setAiFeedback(null);
    try {
      const response = await apiFetch(`/grammar/patterns/${pattern.id}/evaluate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: controller.signal,
        body: JSON.stringify({ meaning: current.meaning, reference: current.japanese, answer: answer.trim() }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(response.status === 401 ? 'Hãy đăng nhập Google để dùng đánh giá AI.' : (typeof data.detail === 'string' ? data.detail : 'Không thể đánh giá bằng AI.'));
      if (!controller.signal.aborted) setAiFeedback({ verdict: data.verdict, message: data.feedback });
    } catch (error) {
      if (!controller.signal.aborted) setAiFeedback({ message: error.message || 'Không thể kết nối AI.' });
    } finally {
      if (aiRequest.current === controller) { aiRequest.current = null; setAiLoading(false); }
    }
  };

  useEffect(() => {
    if (!open) return undefined;
    const previousOverflow = document.body.style.overflow;
    const onKeyDown = event => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', onKeyDown);
    inputRef.current?.focus();
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open, index]);

  const current = questions[index];
  const recordAndContinue = () => {
    const result = checked === true ? true : false;
    const updated = [...results, result];
    setResults(updated);
    setAnswer('');
    setChecked(null);
    setShowHint(false);
    setShowReference(false);
    cancelAI();
    setIndex(index + 1);
  };
  const restart = () => {
    setIndex(0);
    setResults([]);
    setAnswer('');
    setChecked(null);
    setShowHint(false);
    setShowReference(false);
    cancelAI();
  };

  return <>
    <button type="button" className="grammar-exercise-trigger" onClick={() => { restart(); setOpen(true); }}>
      ✎ Làm bài tập
    </button>
    {open && createPortal(
      <div className="grammar-exercise-overlay" onMouseDown={event => { if (event.target === event.currentTarget) setOpen(false); }}>
        <section className="grammar-exercise-dialog" role="dialog" aria-modal="true" aria-label={`Bài tập ngữ pháp ${pattern.formula}`}>
          <header className="grammar-exercise-header">
            <div><small>LUYỆN TẬP NGỮ PHÁP {level}</small><h2>{pattern.formula}</h2></div>
            <button type="button" className="grammar-exercise-close" onClick={() => { cancelAI(); setOpen(false); }} aria-label="Đóng bài tập">×</button>
          </header>
          {index < questions.length ? <>
            <div className="grammar-exercise-progress"><span>Câu {index + 1}/{questions.length}</span><span>{results.filter(Boolean).length} câu trùng đáp án mẫu</span></div>
            {questions.length < 5 && <p className="grammar-exercise-shortage">Mẫu này hiện có {questions.length} câu; các câu bổ sung đang được biên soạn.</p>}
            <article className="grammar-exercise-card">
              <span className="grammar-exercise-number">{index + 1}</span>
              <small>TIẾNG VIỆT</small>
              <p>{current.meaning}</p>
              <button type="button" className="grammar-exercise-text-button" onClick={() => setShowHint(value => !value)}>
                ♧ {showHint ? 'Ẩn gợi ý' : 'Hiện gợi ý'}
              </button>
              {showHint && <p className="grammar-exercise-hint">Cấu trúc: {pattern.formula} · {pattern.explanation_vi}</p>}
              <label htmlFor="grammar-exercise-answer">BẢN DỊCH CỦA BẠN (日本語)</label>
              <textarea id="grammar-exercise-answer" ref={inputRef} value={answer} onChange={event => { cancelAI(); setAnswer(event.target.value); setChecked(null); }} placeholder="Gõ bản dịch tiếng Nhật ở đây..." rows="3" lang="ja" />
              <div className="grammar-exercise-actions">
                <button type="button" className="grammar-exercise-check" disabled={!answer.trim()} onClick={() => setChecked(matchesGrammarReference(answer, current.japanese))}>✓ Kiểm tra</button>
                <button type="button" className="grammar-exercise-ai" disabled={!answer.trim() || aiLoading} onClick={evaluateAI}>✧ {aiLoading ? 'Đang đánh giá…' : 'AI đánh giá'}</button>
                <button type="button" className="grammar-exercise-text-button" onClick={() => setShowReference(value => !value)}>{showReference ? 'Ẩn đáp án' : '◉ Xem đáp án'}</button>
              </div>
              {checked !== null && <p className={checked ? 'grammar-exercise-feedback match' : 'grammar-exercise-feedback mismatch'} role="status">
                {checked ? 'Bản dịch trùng câu mẫu.' : 'Chưa trùng câu mẫu. Một cách diễn đạt khác vẫn có thể đúng; hãy đối chiếu đáp án.'}
              </p>}
              {aiFeedback && <p className={`grammar-exercise-feedback ${aiFeedback.verdict === 'correct' ? 'match' : aiFeedback.verdict === 'incorrect' ? 'mismatch' : ''}`} role="status">{aiFeedback.message}</p>}
              {showReference && <div className="grammar-exercise-reference"><small>ĐÁP ÁN MẪU</small><strong lang="ja">{current.japanese}</strong>{current.reading && <span>{current.reading}</span>}</div>}
              {(checked !== null || showReference) && <button type="button" className="grammar-exercise-next" onClick={recordAndContinue}>{index + 1 === questions.length ? 'Xem kết quả' : 'Câu tiếp theo →'}</button>}
            </article>
          </> : <div className="grammar-exercise-summary">
            <h3>Hoàn thành lượt luyện tập</h3>
            <p>{results.filter(Boolean).length}/{questions.length} câu trùng đáp án mẫu</p>
            <small>Phần kiểm tra hiện chỉ đối chiếu với câu mẫu, chưa đánh giá mọi cách dịch đúng.</small>
            <div><button type="button" onClick={restart}>Làm lại</button><button type="button" onClick={() => setOpen(false)}>Đóng</button></div>
          </div>}
        </section>
      </div>, document.body)}
  </>;
}
