export default function AboutPage() {
  return <section className="simple-page about-page">
    <p className="eyebrow">VỀ KANJIAI</p>
    <h1>Học chữ Nhật theo từng bước nhỏ.</h1>
    <p className="intro">KanjiAI là dự án web học Kanji, từ vựng và ngữ pháp theo cấp JLPT. Người học có thể xem thứ tự nét, thử nhận diện một chữ viết tay, lưu tiến độ và in phiếu luyện tập.</p>

    <section className="about-grid">
      <article className="panel"><h2>Hiện có thể sử dụng</h2><p>Tra Kanji, lộ trình học theo ngày, flashcard từ vựng, bài ngữ pháp, ôn mục đã lưu và tạo phiếu học để in. Các bài không bị khóa theo tiến độ.</p></article>
      <article className="panel"><h2>Chưa triển khai</h2><p>Chưa có bài tập ngữ pháp tự chấm hoặc AI chấm câu ngữ pháp. Nhận diện viết tay gợi ý ký tự, không chấm đúng/sai thứ tự nét.</p></article>
    </section>

    <section className="panel about-section"><h2>Nguồn dữ liệu và ghi công</h2><ul>
      <li>Nét viết SVG: <a href="https://kanjivg.tagaini.net/" target="_blank" rel="noreferrer">KanjiVG / Ulrich Apel</a> (CC BY-SA 3.0).</li>
      <li>Thông tin Kanji và từ điển tham khảo: <a href="https://www.edrdg.org/edrdg/licence.html" target="_blank" rel="noreferrer">KANJIDIC2, JMdict / EDRDG</a> (CC BY-SA 4.0 và điều kiện ghi công của EDRDG); nghĩa tiếng Việt được biên tập cho KanjiAI.</li>
      <li>Danh sách và một phần dữ liệu JLPT được tham khảo từ <a href="https://kanjikana.com/vi/kanji/jlpt/n1" target="_blank" rel="noreferrer">Kanjikana</a>. Quyền tái sử dụng phần dữ liệu phái sinh này đang được rà soát.</li>
      <li>Mẫu ngữ pháp và ví dụ tham khảo: <a href="https://github.com/jkindrix/japanese-language-data" target="_blank" rel="noreferrer">Japanese Language Data</a> (CC BY-SA 4.0); lộ trình và bản địa hóa được biên tập lại.</li>
      <li>Mô hình nhận diện tiếng Nhật: <a href="https://github.com/dariyooo/DaKanji-Single-Kanji-Recognition" target="_blank" rel="noreferrer">DaKanji / DaAppLab</a>. Mô hình Hán tự do dự án huấn luyện từ CASIA-HWDB.</li>
    </ul><p>Chi tiết nhập liệu và ghi công: <a href="https://github.com/Hiepnguyen17/Kanji/blob/main/KANJI_SOURCES.md" target="_blank" rel="noreferrer">Kanji</a> · <a href="https://github.com/Hiepnguyen17/Kanji/blob/main/GRAMMAR_SOURCES.md" target="_blank" rel="noreferrer">Ngữ pháp</a>.</p></section>

    <section className="panel about-section"><h2>Dữ liệu tài khoản được lưu</h2><ul>
      <li>Khi đăng nhập Google: mã tài khoản Google, email, tên hiển thị và ảnh đại diện để nhận diện tài khoản.</li>
      <li>Phiên đăng nhập: cookie trên trình duyệt; máy chủ lưu mã băm của token và thời điểm hết hạn. Đăng xuất sẽ hủy phiên hiện tại.</li>
      <li>Tiến độ Kanji/từ vựng/ngữ pháp, mục ôn tập và kết quả ôn, cùng cài đặt giao diện được lưu theo tài khoản trong SQLite.</li>
      <li>Ảnh/nét viết gửi để nhận diện được xử lý cho yêu cầu đó; thao tác nhận diện thông thường không lưu thành mẫu huấn luyện. Endpoint lưu mẫu riêng chỉ dành cho quản trị viên.</li>
    </ul><p>Dữ liệu SQLite trên máy chủ có thể nằm trong bản sao lưu vận hành. Khi chưa đăng nhập, lựa chọn giao diện chỉ lưu trên thiết bị. Hiện giao diện chưa có nút tự xóa tài khoản; nếu cần xử lý dữ liệu, hãy <a href="https://github.com/Hiepnguyen17/Kanji/issues" target="_blank" rel="noreferrer">liên hệ qua trang dự án</a>.</p></section>
  </section>;
}
