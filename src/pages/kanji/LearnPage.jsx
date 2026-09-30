import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { API_BASE_URL, useRemoteJson } from '../../api/client';
import DataState from '../../components/DataState';
import PrintWorksheetButton from '../../components/worksheets/PrintWorksheetButton';

const CURRICULUM_COUNTS = { N5: 80, N4: 170, N3: 370, N2: 380, N1: 1136 };

export default function LearnPage({ openKanji, go, user, progress, updateProgress, notify }) {
  const routeLocation = useLocation();
  const navigate = useNavigate();
  const search = new URLSearchParams(routeLocation.search);
  const requestedLevel = (search.get('level') || 'N5').toUpperCase();
  const level = /^N[1-5]$/.test(requestedLevel) ? requestedLevel : 'N5';
  const dailyCount = 10;
  const { data, status, retry } = useRemoteJson(`${API_BASE_URL}/api/kanji?level=${level}`);
  const kanji = data || [];
  const days = Array.from({ length: Math.ceil(kanji.length / dailyCount) }, (_, index) => kanji.slice(index * dailyCount, (index + 1) * dailyCount));

  useEffect(() => {
    if (status !== 'ready') return undefined;
    let position;
    try { position = Number(sessionStorage.getItem(`kanjiai-scroll:${routeLocation.key}`)); } catch { return undefined; }
    if (!Number.isFinite(position) || position <= 0) return undefined;
    const frame = requestAnimationFrame(() => requestAnimationFrame(() => window.scrollTo(0, position)));
    return () => cancelAnimationFrame(frame);
  }, [status, routeLocation.key]);

  const requestedDay = Number(search.get('day') || 1);
  const dayNumber = Math.min(Math.max(Number.isFinite(requestedDay) ? requestedDay : 1, 1), Math.max(days.length, 1));
  const day = days[dayNumber - 1] || [];
  const pathId = `kanji-path:${level}:day-${String(dayNumber).padStart(3, '0')}`;
  const recordFor = number => progress.find(item => item.content_type === 'kanji' && item.content_id === `kanji-path:${level}:day-${String(number).padStart(3, '0')}`);
  const currentRecord = recordFor(dayNumber);
  const completedDays = days.filter((_, index) => recordFor(index + 1)?.progress_state === 'completed').length;
  const percent = days.length ? Math.round(completedDays / days.length * 100) : 0;
  const ongoingDay = days.findIndex((_, index) => recordFor(index + 1)?.progress_state === 'started') + 1;
  const selectLevel = nextLevel => go(`/learn/kanji?level=${nextLevel}&day=1`);
  const selectDay = number => navigate(`/learn/kanji?level=${level}&day=${number}`);
  const saveDay = async (progress_state, resume_position = 0) => {
    if (!user) {
      notify('Hãy đăng nhập Google để lưu lộ trình học');
      go('/login');
      return false;
    }
    try {
      await updateProgress('kanji', pathId, { progress_state, score: progress_state === 'completed' ? 1 : currentRecord?.progress_state === 'completed' ? 0 : currentRecord?.score || 0, resume_position });
      return true;
    } catch {
      notify('Không thể lưu tiến độ. Hãy thử lại.');
      return false;
    }
  };
  const beginDay = async () => { if (await saveDay('started', currentRecord?.resume_position || 0)) notify(`Đã bắt đầu ngày ${dayNumber} · ${level}`); };
  const openDayKanji = async (item, index) => { if (user && currentRecord?.progress_state !== 'completed') await saveDay('started', index); openKanji(item); };
  const completeDay = async () => { if (await saveDay('completed')) notify(`Đã hoàn thành ngày ${dayNumber} · ${level}`); };

  return <section className="simple-page kanji-learning-page">
    <p className="eyebrow">LỘ TRÌNH HỌC KANJI</p><h1>Đi từng bước nhỏ.</h1>
    <p className="intro">Mỗi ngày 10 chữ. Bạn có thể chọn bất kỳ ngày nào; tiến độ chỉ dùng để ghi nhận và tiếp tục, không khóa bài học.</p>
    <div className="path-levels" role="tablist" aria-label="Chọn cấp JLPT">{['N5', 'N4', 'N3', 'N2', 'N1'].map(item => {
      const total = CURRICULUM_COUNTS[item]; const totalDays = Math.ceil(total / dailyCount);
      return <button role="tab" aria-selected={item === level} className={item === level ? 'active' : ''} key={item} onClick={() => selectLevel(item)}><b>{item}</b><span>{total} chữ · {totalDays} ngày</span></button>;
    })}</div>
    {status !== 'ready' ? <DataState kind={status} title={status === 'empty' ? `Chưa có dữ liệu Kanji ${level}.` : undefined} onRetry={retry} /> : <>
      <section className="path-summary path-overview"><div><p className="eyebrow">JLPT {level} · {days.length} NGÀY</p><h2>{completedDays}/{days.length} ngày hoàn thành</h2><small>{user ? (ongoingDay ? `Bạn đang học dở ngày ${ongoingDay}.` : 'Chọn một ngày để bắt đầu lộ trình.') : 'Đăng nhập để lưu lộ trình riêng của bạn.'}</small></div><div className="path-progress"><b>{percent}%</b><i><em style={{ width: `${percent}%` }} /></i></div>{ongoingDay > 0 && <button className="outline" onClick={() => selectDay(ongoingDay)}>Tiếp tục ngày {ongoingDay} →</button>}</section>
      <section className="path-day-navigator" aria-label="Điều hướng ngày học"><button className="path-day-arrow" disabled={dayNumber === 1} onClick={() => selectDay(dayNumber - 1)} aria-label="Ngày trước">‹</button><div><p className="eyebrow">LỘ TRÌNH {level}</p><h2>Ngày {dayNumber}</h2><span>{currentRecord?.progress_state === 'completed' ? '✓ Đã học' : currentRecord?.progress_state === 'started' ? '● Đang học' : `○ Chưa học · ${day.length} Kanji`}</span></div><button className="path-day-arrow" disabled={dayNumber === days.length} onClick={() => selectDay(dayNumber + 1)} aria-label="Ngày kế tiếp">›</button></section>
      <label className="path-day-slider"><span>Ngày 1</span><input type="range" min="1" max={days.length} value={dayNumber} onChange={event => selectDay(Number(event.target.value))} aria-label={`Chọn ngày học, hiện ngày ${dayNumber}`} /><span>Ngày {days.length}</span></label>
      <section className="panel path-day-detail"><div className="section-heading"><div><p className="eyebrow">◎ LỘ TRÌNH {level}</p><h2>Kanji ngày {dayNumber}</h2><small>{day.length} chữ · Nhấn từng chữ để xem, nghe, viết và luyện nét.</small></div><div className="path-actions"><PrintWorksheetButton config={{ type: 'kanji', level, day: String(dayNumber) }} go={go} user={user} disabled={!day.length} />{currentRecord?.progress_state !== 'completed' && <button className="primary" onClick={beginDay}>{currentRecord?.progress_state === 'started' ? 'Tiếp tục học' : 'Học ngay'}</button>}{currentRecord?.progress_state === 'completed' ? <button className="outline" onClick={() => saveDay('started', 0)}>Học lại</button> : <button className="outline" onClick={completeDay}>Đánh dấu hoàn thành</button>}</div></div><div className="path-kanji-list">{day.map((item, index) => <button key={item.char} onClick={() => openDayKanji(item, index)} title={`Mở chữ ${item.char}`}><b>{String(index + 1).padStart(2, '0')}</b><strong>{item.char}</strong><span>{item.han_viet || item.meaning}</span><i>→</i></button>)}</div></section>
    </>}
  </section>;
}
