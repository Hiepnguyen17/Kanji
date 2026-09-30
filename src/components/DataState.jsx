export default function DataState({ kind, title, back, onRetry }) {
  const messages = {
    loading: 'Đang tải dữ liệu…',
    empty: 'Chưa có dữ liệu ở đây.',
    error: 'Không kết nối được với máy chủ.',
    notfound: 'Đường dẫn này không tồn tại.',
  };
  return <section className="data-state" role={kind === 'error' ? 'alert' : 'status'}>
    <h2>{title || messages[kind]}</h2>
    <p>{kind === 'error' ? 'Kiểm tra backend rồi thử lại.' : kind === 'notfound' ? 'Kiểm tra lại địa chỉ hoặc quay về trang chủ.' : kind === 'empty' ? 'Hãy chọn mục khác để tiếp tục học.' : 'Vui lòng đợi trong giây lát.'}</p>
    <div className="data-state-actions">
      {kind === 'error' && onRetry && <button className="primary" onClick={onRetry}>Thử lại</button>}
      {back && <button className="outline" onClick={back}>Về trang chủ</button>}
    </div>
  </section>;
}
