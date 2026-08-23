"""Original KanjiAI N5 grammar curriculum; not copied from a textbook."""

LESSONS = [
    ("N5", "Giới thiệu bản thân", "Câu khẳng định, phủ định và nghi vấn với danh từ.", 1),
    ("N5", "Đồ vật và sở hữu", "Chỉ định đồ vật bằng これ・それ・あれ và biểu thị sở hữu với の.", 2),
    ("N5", "Địa điểm và tồn tại", "Nói một người hoặc đồ vật ở đâu với あります・います.", 3),
    ("N5", "Động từ thể ます", "Dùng động từ lịch sự để nói về hoạt động hằng ngày.", 4),
    ("N5", "Thời gian và tần suất", "Nói thời điểm và thói quen bằng に・から・まで・毎〜.", 5),
]

PATTERNS = [
    (1,"A は B です","A là B.","Dùng は để nêu chủ đề; です tạo câu lịch sự."),(1,"A は B じゃありません","A không phải là B.","じゃありません là phủ định lịch sự của です."),(1,"A は B ですか","A có phải là B không?","Thêm か ở cuối câu để hỏi; không cần đổi trật tự từ."),
    (2,"これ・それ・あれ は N です","Đây/đó/kia là N.","これ ở gần người nói, それ gần người nghe, あれ ở xa cả hai."),(2,"A の B","B của A.","Trợ từ の nối hai danh từ để chỉ sở hữu hoặc mối quan hệ."),(2,"この・その・あの N","N này/N đó/N kia.","Khác với これ, nhóm này luôn đứng ngay trước danh từ."),
    (3,"Place に N が あります","Có đồ vật N ở Place.","Dùng あります cho đồ vật, thực vật và sự vật vô tri."),(3,"Place に Person が います","Có Person ở Place.","Dùng います cho người và động vật."),(3,"N は Place に あります・います","N ở Place.","Đổi chủ đề lên đầu câu khi muốn nhấn vào N."),
    (4,"Vます","Làm V (lịch sự).","Dạng ます dùng trong hội thoại lịch sự."),(4,"Vません","Không làm V.","Thay ます bằng ません để phủ định ở hiện tại/tương lai."),(4,"Vますか","Có làm V không?","Dùng để hỏi lịch sự về hành động."),
    (5,"Time に Vます","Làm V vào Time.","Dùng に với giờ, ngày, thứ cụ thể; thường bỏ với 今日・毎日."),(5,"Time から Time まで","Từ Time đến Time.","から chỉ điểm bắt đầu, まで chỉ điểm kết thúc."),(5,"毎〜 Vます","Làm V mỗi ~.","毎日, 毎朝, 毎週 diễn tả thói quen lặp lại."),
]

EXAMPLES = [
    (1,"わたしは学生です。","わたしは がくせいです。","Tôi là học sinh/sinh viên."),(1,"田中さんは先生じゃありません。","たなかさんは せんせいじゃありません。","Anh/chị Tanaka không phải là giáo viên."),(1,"あなたは日本人ですか。","あなたは にほんじんですか。","Bạn có phải là người Nhật không?"),
    (2,"これは本です。","これは ほんです。","Đây là sách."),(2,"これはわたしの辞書です。","これは わたしの じしょです。","Đây là từ điển của tôi."),(2,"あの人は先生です。","あの ひとは せんせいです。","Người kia là giáo viên."),
    (3,"教室に机があります。","きょうしつに つくえが あります。","Có một cái bàn trong lớp học."),(3,"学校に学生がいます。","がっこうに がくせいが います。","Có học sinh ở trường."),(3,"本は机の上にあります。","ほんは つくえの うえに あります。","Quyển sách ở trên bàn."),
    (4,"毎日日本語を勉強します。","まいにち にほんごを べんきょうします。","Tôi học tiếng Nhật mỗi ngày."),(4,"今日は学校へ行きません。","きょうは がっこうへ いきません。","Hôm nay tôi không đi đến trường."),(4,"明日来ますか。","あした きますか。","Ngày mai bạn đến chứ?"),
    (5,"七時に起きます。","しちじに おきます。","Tôi thức dậy lúc bảy giờ."),(5,"学校は八時から三時までです。","がっこうは はちじから さんじまでです。","Trường học từ tám giờ đến ba giờ."),(5,"毎朝お茶を飲みます。","まいあさ おちゃを のみます。","Tôi uống trà mỗi sáng."),
]
