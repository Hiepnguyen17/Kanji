import { useRef, useState } from 'react';
import { API_BASE_URL, apiFetch, useRemoteJson } from '../../api/client';
import DataState from '../../components/DataState';
import PrintWorksheetButton from '../../components/worksheets/PrintWorksheetButton';

export function ReviewPage({ user, go, notify }) {
  const { data, status, retry } = useRemoteJson(user ? `${API_BASE_URL}/review-items` : null);
  const [tab, setTab] = useState('kanji');
  const [session, setSession] = useState(null);
  const answerPending = useRef(false);
  const items = data || [];
  const tabs = [['kanji', 'Kanji'], ['vocabulary', 'Từ vựng'], ['grammar', 'Ngữ pháp']];
  const current = items.filter(item => item.content_type === tab);
  const printButton = tab !== 'grammar' && current.length > 0 && <PrintWorksheetButton config={{ source: 'review', type: tab }} go={go} user={user}>▧ In phiếu ôn tập</PrintWorksheetButton>;
  const startSession = (source = current) => {
    if (!source.length) return;
    setSession({ items: source.slice(0, 10), index: 0, revealed: false, remembered: 0, forgot: 0, missed: [], saving: false, error: '' });
  };
  const answer = async remembered => {
    if (!session || answerPending.current) return;
    answerPending.current = true;
    setSession(previous => ({ ...previous, saving: true, error: '' }));
    const item = session.items[session.index];
    try {
      const response = await apiFetch(`${API_BASE_URL}/review-items/${item.content_type}/${encodeURIComponent(item.content_id)}/result`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ remembered }),
      });
      if (!response.ok) throw new Error('Không lưu được kết quả ôn tập');
      const finished = session.index + 1 === session.items.length;
      setSession(previous => ({ ...previous, index: previous.index + 1, revealed: false, saving: false,
        remembered: previous.remembered + Number(remembered), forgot: previous.forgot + Number(!remembered),
        missed: remembered ? previous.missed : [...previous.missed, item], error: '' }));
      if (finished) retry();
    } catch {
      setSession(previous => ({ ...previous, saving: false, error: 'Chưa lưu được kết quả. Hãy thử lại.' }));
    } finally { answerPending.current = false; }
  };
  const remove = async item => {
    try {
      const response = await apiFetch(`${API_BASE_URL}/review-items/${item.content_type}/${encodeURIComponent(item.content_id)}`, { method: 'DELETE' });
      if (!response.ok) throw new Error();
      notify('Đã bỏ khỏi danh sách ôn tập'); retry();
    } catch { notify('Không thể cập nhật danh sách ôn tập'); }
  };
  if (!user) return <section className="simple-page review-page"><p className="eyebrow">ÔN TẬP</p><h1>Danh sách ôn của bạn.</h1><section className="panel review-empty"><p>Đăng nhập để lưu Kanji, từ vựng và ngữ pháp muốn ôn lại.</p><button className="primary" onClick={() => go('/login')}>Đăng nhập bằng Google</button></section></section>;
  if (session) {
    const done = session.index >= session.items.length;
    const item = session.items[session.index];
    return <section className="simple-page review-page review-session">
      <p className="eyebrow">PHIÊN ÔN TẬP · {tabs.find(([id]) => id === tab)?.[1].toUpperCase()}</p>
      <h1>{done ? 'Kết quả phiên ôn tập' : 'Tự kiểm tra trí nhớ'}</h1>
      {!done ? <>
        <div className="review-session-top"><span>Mục {session.index + 1}/{session.items.length}</span><button className="outline" onClick={() => { setSession(null); retry(); }} disabled={session.saving}>Quay lại danh sách</button></div>
        <progress max={session.items.length} value={session.index} aria-label="Tiến độ phiên ôn tập" />
        <article className="panel review-question">
          <small>{tab === 'grammar' ? 'Đọc ý nghĩa và nhớ lại cấu trúc' : 'Nhìn nội dung và nhớ cách đọc, ý nghĩa'}</small>
          <strong lang={tab === 'grammar' ? 'vi' : 'ja'}>{item.quiz_prompt || item.title}</strong>
          {!session.revealed ? <button className="primary" onClick={() => setSession(previous => ({ ...previous, revealed: true }))}>Hiện đáp án</button> : <>
            <div className="review-answer"><span>ĐÁP ÁN</span><b>{item.quiz_answer || item.subtitle}</b>{item.quiz_example && <p>{item.quiz_example}</p>}</div>
            <p>Bạn có nhớ được trước khi xem đáp án không?</p>
            <div className="review-answer-actions"><button className="outline review-forgot" disabled={session.saving} onClick={() => answer(false)}>Chưa nhớ</button><button className="primary" disabled={session.saving} onClick={() => answer(true)}>Đã nhớ</button></div>
          </>}
          {session.error && <p className="review-session-error" role="alert">{session.error}</p>}
        </article>
      </> : <article className="panel review-summary">
        <p>Đã ôn <b>{session.items.length}</b> mục</p>
        <div><span>✓ Đã nhớ <b>{session.remembered}</b></span><span>Cần học lại <b>{session.forgot}</b></span></div>
        <small>{session.forgot ? 'Các mục chưa nhớ sẽ được ưu tiên trong phiên ôn sau.' : 'Tốt lắm! Bạn đã nhớ toàn bộ mục trong phiên này.'}</small>
        <div className="review-summary-actions"><button className="outline" onClick={() => { setSession(null); retry(); }}>Về danh sách</button>{session.missed.length > 0 && <button className="primary" onClick={() => startSession(session.missed)}>Ôn lại mục chưa nhớ</button>}</div>
      </article>}
    </section>;
  }
  return <section className="simple-page review-page">
    <p className="eyebrow">ÔN TẬP</p><h1>Danh sách ôn của bạn.</h1>
    <p className="intro">Các mục bạn chủ động thêm từ Kanji, từ vựng và ngữ pháp.</p>
    <div className="review-tabs">{tabs.map(([id, label]) => <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>{label} <b>{items.filter(item => item.content_type === id).length}</b></button>)}</div>
    <div className="review-list-actions">{status === 'ready' && current.length > 0 && <button className="primary" onClick={() => startSession()}>Bắt đầu ôn tập · tối đa 10 mục</button>}{printButton}</div>
    {status === 'loading' ? <DataState kind="loading" /> : status === 'error' ? <DataState kind="error" onRetry={retry} /> : current.length ? <section className="review-items">{current.map(item => <article key={`${item.content_type}-${item.content_id}`}><button className="review-item-main" onClick={() => go(item.href)}><strong>{item.title}</strong><span>{item.subtitle}</span>{item.last_result === 'forgot' && <em className="review-status forgot">Cần ôn lại</em>}{item.last_result === 'remembered' && <em className="review-status remembered">Đã nhớ lần trước</em>}<i>›</i></button><button className="review-remove" onClick={() => remove(item)} aria-label={`Bỏ ${item.title} khỏi danh sách ôn tập`}>×</button></article>)}</section> : <section className="panel review-empty"><p>Chưa có {tabs.find(item => item[0] === tab)?.[1].toLowerCase()} nào trong danh sách ôn.</p><small>Hãy mở một nội dung và bấm “Thêm vào ôn tập”.</small></section>}
  </section>;
}

export function SettingsPage({ dark, soundEffects, kanjiFont, user, ready, saving, saveSettings, go }) {
  const disabled = !ready || saving;
  return <section className="simple-page settings"><p className="eyebrow">CÀI ĐẶT</p><h1>Không gian học của bạn.</h1>{!user && <section className="settings-account-note"><b>Cài đặt đang được lưu trên thiết bị này</b><span>Bạn vẫn có thể dùng chế độ tối, âm thanh và font Kanji ngay bây giờ. Đăng nhập Google để đồng bộ chúng giữa các thiết bị.</span><button className="outline" onClick={() => go('/login')}>Đăng nhập để đồng bộ</button></section>}<section className="panel" aria-busy={!ready}><div className="setting"><div><b>Chế độ tối</b><small>Giảm mỏi mắt khi học buổi tối</small></div><button className={dark ? 'toggle on' : 'toggle'} onClick={() => saveSettings({ dark_mode: !dark })} disabled={disabled} aria-label="Bật hoặc tắt chế độ tối"><i /></button></div><div className="setting"><div><b>Hiệu ứng âm thanh</b><small>Âm thanh phản hồi khi học</small></div><button className={soundEffects ? 'toggle on' : 'toggle'} onClick={() => saveSettings({ sound_effects: !soundEffects })} disabled={disabled} aria-label="Bật hoặc tắt hiệu ứng âm thanh"><i /></button></div><div className="setting"><div><b>Font Kanji</b><small>Chọn kiểu hiển thị chữ Hán</small></div><select value={kanjiFont} disabled={disabled} onChange={event => saveSettings({ kanji_font: event.target.value })}><option>Noto Serif JP</option><option>Yu Mincho</option><option>Hiragino Mincho</option></select></div>{user && <small className="settings-sync">{ready ? 'Mọi thay đổi được lưu vào tài khoản này.' : 'Đang tải cài đặt tài khoản…'}</small>}</section></section>;
}

export function LoginPage({ notify, user, logout }) {
  const { data: google, status, retry } = useRemoteJson(`${API_BASE_URL}/auth/google/status`);
  const startGoogle = () => {
    if (!google?.enabled) { notify('Google OAuth chưa được cấu hình. Xem backend/.env.example để thêm Client ID và Client Secret.'); return; }
    const popup = window.open(`${API_BASE_URL}/auth/google/login`, 'kanjiai-google-login', 'popup=yes,width=520,height=720,noopener=no');
    if (!popup) window.location.assign(`${API_BASE_URL}/auth/google/login`);
  };
  if (user) return <section className="login-page"><div className="login-card"><div className="avatar login-avatar">{user.display_name?.trim()?.charAt(0).toUpperCase() || 'K'}</div><p className="eyebrow">ĐÃ ĐĂNG NHẬP</p><h1>{user.display_name || 'Người học KanjiAI'}</h1><p>{user.email}</p><button className="primary wide" onClick={logout}>Đăng xuất</button></div></section>;
  return <section className="login-page"><div className="login-card"><div className="logo big">漢</div><p className="eyebrow">CHÀO MỪNG</p><h1>Học và lưu tiến độ.</h1><p>Đăng nhập bằng Google để đồng bộ tiến độ Kanji, từ vựng và ngữ pháp trên từng tài khoản.</p><button className="primary wide google-signin" disabled={status === 'loading'} onClick={startGoogle}><b>G</b> Đăng nhập bằng Google</button>{status === 'error' && <button className="outline wide" onClick={retry}>Không kết nối được API · Thử lại</button>}{status === 'ready' && !google?.enabled && <small className="login-note">Quản trị viên chưa cấu hình Google OAuth cho máy chủ này.</small>}<p className="login-note">Lần đăng nhập Google đầu tiên sẽ tự tạo tài khoản KanjiAI.</p></div></section>;
}
