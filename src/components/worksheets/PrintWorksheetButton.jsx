import { useEffect, useRef, useState } from 'react';
import { createPortal, flushSync } from 'react-dom';
import { useLocation } from 'react-router-dom';
import WorksheetPage from '../../pages/worksheets/WorksheetPage';

function WorksheetDialog({ config, user, onClose, go }) {
  const dialogRef = useRef(null);
  const backdropStart = useRef(false);
  useEffect(() => {
    const dialog = dialogRef.current;
    const opener = document.activeElement;
    const { scrollX, scrollY } = window;
    const body = document.body;
    const previousOverflow = body.style.overflow;
    const previousPadding = body.style.paddingRight;
    const gutter = window.innerWidth - document.documentElement.clientWidth;
    if (gutter > 0) body.style.paddingRight = `${parseFloat(getComputedStyle(body).paddingRight) + gutter}px`;
    body.style.overflow = 'hidden';
    dialog.showModal();
    return () => {
      dialog.close();
      body.style.overflow = previousOverflow;
      body.style.paddingRight = previousPadding;
      if (opener?.isConnected) opener.focus({ preventScroll: true });
      window.scrollTo({ left: scrollX, top: scrollY, behavior: 'instant' });
    };
  }, []);
  const outside = event => {
    const rect = dialogRef.current.getBoundingClientRect();
    return event.target === dialogRef.current && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom);
  };
  return createPortal(<dialog ref={dialogRef} className="ws-dialog" aria-labelledby="ws-dialog-title"
    onCancel={event => { event.preventDefault(); onClose(); }}
    onPointerDown={event => { backdropStart.current = outside(event); }}
    onClick={event => { event.stopPropagation(); if (backdropStart.current && outside(event)) onClose(); }}>
    <div className="ws-dialog-header"><div><p className="eyebrow">HỌC TRÊN GIẤY</p><h2 id="ws-dialog-title">In phiếu luyện</h2><p>Đã chọn sẵn nội dung đang học. Bạn có thể bỏ bớt mục trước khi in.</p></div><button type="button" className="outline ws-dialog-close" autoFocus onClick={onClose} aria-label="Đóng xem trước phiếu học">✕ Đóng</button></div>
    <WorksheetPage initialConfig={config} compact user={user} go={go} />
  </dialog>, document.querySelector('.app') || document.body);
}

export default function PrintWorksheetButton({ config, go, user, disabled = false, children = '▧ In phiếu luyện', className = 'outline' }) {
  const location = useLocation();
  const [opened, setOpened] = useState(null);
  const active = opened && opened.routeKey === location.key && opened.userId === user?.id;
  const navigate = url => {
    // Restore focus/scroll before the application handles a real navigation.
    flushSync(() => setOpened(null));
    go(url);
  };
  return <><button type="button" className={className} disabled={disabled} onClick={event => {
    event.stopPropagation();
    setOpened({ config: { ...config }, routeKey: location.key, userId: user?.id });
  }}>{children}</button>{active && <WorksheetDialog config={opened.config} user={user} onClose={() => setOpened(null)} go={navigate} />}</>;
}
