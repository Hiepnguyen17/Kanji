"""A KanjiAI-authored N5 learning path. Definitions are sourced from JMdict."""

# Mỗi nhóm là một "bài học lớn" trên giao diện. Các bài trong LESSONS là bài học con.
VOCABULARY_GROUPS = [
    ("N5", "あいさつ", "Chào hỏi & lịch sự", "Lời chào và cách giao tiếp lịch sự.", 1),
    ("N5", "にんしょう", "Đại từ, chỉ định & nghi vấn", "Tự giới thiệu, chỉ người/vật và đặt câu hỏi.", 2),
    ("N5", "ひと", "Con người & nghề nghiệp", "Con người, vai trò và nghề nghiệp cơ bản.", 3),
    ("N5", "かぞく", "Gia đình", "Thành viên trong gia đình.", 4),
    ("N5", "かず", "Số đếm", "Các số cơ bản.", 5),
    ("N5", "じょすうし", "Đơn vị đếm", "Cách đếm người, vật và thời lượng.", 6),
    ("N5", "じかん", "Thời gian & lịch", "Ngày, giờ, mùa và lịch.", 7),
    ("N5", "からだ", "Cơ thể & sức khỏe", "Bộ phận cơ thể và sức khỏe.", 8),
    ("N5", "ばしょ", "Địa điểm công cộng", "Các nơi thường gặp trong thành phố.", 9),
    ("N5", "いどう", "Di chuyển & phương tiện", "Đi lại và phương tiện giao thông.", 10),
    ("N5", "もの", "Nhà cửa, đồ dùng & học tập", "Đồ vật trong nhà, lớp học và sinh hoạt.", 11),
    ("N5", "ふく", "Quần áo, mua sắm & màu sắc", "Trang phục, mua bán và màu sắc.", 12),
    ("N5", "たべもの", "Thức ăn & đồ uống", "Bữa ăn, đồ uống và gọi món.", 13),
    ("N5", "しぜん", "Thiên nhiên & thời tiết", "Thời tiết và cảnh vật.", 14),
    ("N5", "どうぶつ", "Động vật", "Các con vật quen thuộc.", 15),
    ("N5", "うごき", "Động từ hành động", "Hành động trong cuộc sống hằng ngày.", 16),
    ("N5", "じょうたい", "Động từ trạng thái & sở thích", "Trạng thái, giao tiếp và hoạt động yêu thích.", 17),
    ("N5", "けいようし", "Tính từ & miêu tả", "Miêu tả người, vật, cảm xúc và đặc điểm.", 18),
    ("N5", "ふくし", "Trạng từ & mức độ", "Mức độ, tần suất và thời điểm trong câu hằng ngày.", 19),
]

LESSON_GROUPS = {
    "Chào hỏi": "Chào hỏi & lịch sự", "Tự giới thiệu": "Đại từ, chỉ định & nghi vấn", "Đại từ & con người": "Đại từ, chỉ định & nghi vấn",
    "Số đếm": "Số đếm", "Gia đình": "Gia đình", "Thời gian": "Thời gian & lịch", "Mùa & lịch": "Thời gian & lịch",
    "Cơ thể & sức khỏe": "Cơ thể & sức khỏe", "Thành phố": "Địa điểm công cộng", "Địa điểm & di chuyển": "Di chuyển & phương tiện",
    "Trường học": "Nhà cửa, đồ dùng & học tập", "Nhà cửa": "Nhà cửa, đồ dùng & học tập", "Mua sắm": "Quần áo, mua sắm & màu sắc", "Quần áo": "Quần áo, mua sắm & màu sắc",
    "Ăn uống": "Thức ăn & đồ uống", "Nhà hàng": "Thức ăn & đồ uống", "Thời tiết & thiên nhiên": "Thiên nhiên & thời tiết", "Động vật gần gũi": "Động vật",
    "Công việc": "Con người & nghề nghiệp", "Sở thích": "Động từ trạng thái & sở thích", "Liên lạc": "Động từ trạng thái & sở thích", "Tính từ cơ bản": "Tính từ & miêu tả",
    "Cuộc sống hằng ngày": "Động từ hành động",
}

STAGING_TOPIC_GROUPS = {
    "Đại từ & chỉ định": "Đại từ, chỉ định & nghi vấn", "Giao tiếp cơ bản": "Chào hỏi & lịch sự", "Sinh hoạt hằng ngày": "Động từ hành động",
    "Địa điểm công cộng": "Địa điểm công cộng", "Đồ dùng hằng ngày": "Nhà cửa, đồ dùng & học tập", "Thức ăn & đồ uống": "Thức ăn & đồ uống", "Miêu tả cơ bản": "Tính từ & miêu tả",
}

LESSONS = [
    ("N5", "Chào hỏi", "Những lời chào cơ bản trong ngày.", 1),
    ("N5", "Đại từ & con người", "Giới thiệu bản thân và những người xung quanh.", 2),
    ("N5", "Số đếm", "Đếm từ một đến mười và lượng từ thông dụng.", 3),
    ("N5", "Thời gian", "Ngày, tuần và các thời điểm trong ngày.", 4),
    ("N5", "Trường học", "Từ vựng thiết yếu trong lớp học.", 5),
    ("N5", "Gia đình", "Các thành viên trong gia đình.", 6),
    ("N5", "Địa điểm & di chuyển", "Hỏi đường và đi lại hằng ngày.", 7),
    ("N5", "Ăn uống", "Gọi món và nói về bữa ăn.", 8),
    ("N5", "Mua sắm", "Màu sắc, giá cả và đồ vật quen thuộc.", 9),
    ("N5", "Thời tiết & thiên nhiên", "Nói về thời tiết và cảnh vật.", 10),
    ("N5", "Nhà cửa", "Các phòng và đồ vật thường có trong nhà.", 11),
    ("N5", "Cơ thể & sức khỏe", "Tên các bộ phận cơ thể và tình trạng cơ bản.", 12),
    ("N5", "Quần áo", "Trang phục và cách nói về việc mặc đồ.", 13),
    ("N5", "Mùa & lịch", "Bốn mùa, tháng và dịp trong năm.", 14),
    ("N5", "Công việc", "Nghề nghiệp và công việc hằng ngày.", 15),
    ("N5", "Sở thích", "Hoạt động giải trí và sở thích.", 16),
    ("N5", "Thành phố", "Những nơi thường gặp trong thành phố.", 17),
    ("N5", "Tính từ cơ bản", "Miêu tả đồ vật, con người và cảm xúc.", 18),
    ("N5", "Nhà hàng", "Từ cần dùng khi gọi món và thanh toán.", 19),
    ("N5", "Liên lạc", "Gặp gỡ, trao đổi và cách liên lạc cơ bản.", 20),
    ("N5", "Động vật gần gũi", "Tên các con vật quen thuộc trong đời sống.", 21),
]

# lesson order, word, reading, Vietnamese gloss
WORDS = [
    (1,"こんにちは","こんにちは","xin chào"),(1,"おはよう","おはよう","chào buổi sáng"),(1,"こんばんは","こんばんは","chào buổi tối"),(1,"さようなら","さようなら","tạm biệt"),(1,"ありがとう","ありがとう","cảm ơn"),(1,"すみません","すみません","xin lỗi; làm phiền"),(1,"はい","はい","vâng"),(1,"いいえ","いいえ","không"),(1,"お願いします","おねがいします","xin vui lòng"),(1,"はじめまして","はじめまして","rất hân hạnh được gặp"),
    (2,"私","わたし","tôi"),(2,"あなた","あなた","bạn"),(2,"人","ひと","người"),(2,"友達","ともだち","bạn bè"),(2,"先生","せんせい","giáo viên"),(2,"学生","がくせい","học sinh; sinh viên"),(2,"名前","なまえ","tên"),(2,"日本人","にほんじん","người Nhật"),(2,"子供","こども","trẻ em"),(2,"男","おとこ","nam; đàn ông"),
    (3,"一","いち","một"),(3,"二","に","hai"),(3,"三","さん","ba"),(3,"四","よん","bốn"),(3,"五","ご","năm"),(3,"六","ろく","sáu"),(3,"七","なな","bảy"),(3,"八","はち","tám"),(3,"九","きゅう","chín"),(3,"十","じゅう","mười"),
    (4,"今日","きょう","hôm nay"),(4,"明日","あした","ngày mai"),(4,"昨日","きのう","hôm qua"),(4,"毎日","まいにち","mỗi ngày"),(4,"時間","じかん","thời gian; giờ"),(4,"今","いま","bây giờ"),(4,"朝","あさ","buổi sáng"),(4,"昼","ひる","buổi trưa"),(4,"夜","よる","buổi tối; đêm"),(4,"曜日","ようび","thứ trong tuần"),
    (5,"学校","がっこう","trường học"),(5,"教室","きょうしつ","lớp học"),(5,"本","ほん","sách"),(5,"辞書","じしょ","từ điển"),(5,"ノート","ノート","vở ghi"),(5,"鉛筆","えんぴつ","bút chì"),(5,"机","つくえ","bàn học"),(5,"宿題","しゅくだい","bài tập về nhà"),(5,"勉強","べんきょう","học tập"),(5,"読む","よむ","đọc"),
    (6,"家族","かぞく","gia đình"),(6,"父","ちち","bố (của tôi)"),(6,"母","はは","mẹ (của tôi)"),(6,"兄","あに","anh trai (của tôi)"),(6,"姉","あね","chị gái (của tôi)"),(6,"弟","おとうと","em trai"),(6,"妹","いもうと","em gái"),(6,"祖父","そふ","ông (của tôi)"),(6,"祖母","そぼ","bà (của tôi)"),
    (7,"駅","えき","ga tàu"),(7,"電車","でんしゃ","tàu điện"),(7,"車","くるま","ô tô"),(7,"道","みち","đường"),(7,"家","いえ","nhà"),(7,"店","みせ","cửa hàng"),(7,"行く","いく","đi"),(7,"来る","くる","đến"),(7,"帰る","かえる","về"),(7,"歩く","あるく","đi bộ"),
    (8,"食べる","たべる","ăn"),(8,"飲む","のむ","uống"),(8,"ご飯","ごはん","cơm; bữa ăn"),(8,"水","みず","nước"),(8,"お茶","おちゃ","trà"),(8,"肉","にく","thịt"),(8,"魚","さかな","cá"),(8,"野菜","やさい","rau củ"),(8,"果物","くだもの","trái cây"),(8,"美味しい","おいしい","ngon"),
    (9,"買う","かう","mua"),(9,"高い","たかい","đắt; cao"),(9,"安い","やすい","rẻ"),(9,"お金","おかね","tiền"),(9,"服","ふく","quần áo"),(9,"靴","くつ","giày"),(9,"赤","あか","màu đỏ"),(9,"青","あお","màu xanh dương"),(9,"白","しろ","màu trắng"),(9,"黒","くろ","màu đen"),
    (10,"天気","てんき","thời tiết"),(10,"晴れ","はれ","trời nắng"),(10,"雨","あめ","mưa"),(10,"雪","ゆき","tuyết"),(10,"風","かぜ","gió"),(10,"空","そら","bầu trời"),(10,"山","やま","núi"),(10,"川","かわ","sông"),(10,"花","はな","hoa"),(10,"暑い","あつい","nóng (thời tiết)"),
    (11,"部屋","へや","phòng"),(11,"台所","だいどころ","nhà bếp"),(11,"玄関","げんかん","lối vào nhà"),(11,"窓","まど","cửa sổ"),(11,"ドア","ドア","cửa ra vào"),(11,"椅子","いす","ghế"),(11,"冷蔵庫","れいぞうこ","tủ lạnh"),(11,"テレビ","テレビ","ti vi"),(11,"ベッド","ベッド","giường"),(11,"掃除","そうじ","dọn dẹp"),
    (12,"頭","あたま","đầu"),(12,"目","め","mắt"),(12,"耳","みみ","tai"),(12,"口","くち","miệng"),(12,"手","て","tay"),(12,"足","あし","chân"),(12,"体","からだ","cơ thể"),(12,"病気","びょうき","bệnh"),(12,"薬","くすり","thuốc"),(12,"痛い","いたい","đau"),
    (13,"シャツ","シャツ","áo sơ mi"),(13,"ズボン","ズボン","quần"),(13,"スカート","スカート","váy"),(13,"帽子","ぼうし","mũ"),(13,"上着","うわぎ","áo khoác"),(13,"セーター","セーター","áo len"),(13,"着る","きる","mặc (áo)"),(13,"履く","はく","mang/mặc (giày, quần)"),(13,"脱ぐ","ぬぐ","cởi ra"),(13,"似合う","にあう","hợp, vừa"),
    (14,"春","はる","mùa xuân"),(14,"夏","なつ","mùa hè"),(14,"秋","あき","mùa thu"),(14,"冬","ふゆ","mùa đông"),(14,"月","つき","tháng; mặt trăng"),(14,"今年","ことし","năm nay"),(14,"来年","らいねん","năm sau"),(14,"去年","きょねん","năm ngoái"),(14,"誕生日","たんじょうび","sinh nhật"),(14,"休み","やすみ","ngày nghỉ"),
    (15,"仕事","しごと","công việc"),(15,"会社","かいしゃ","công ty"),(15,"会社員","かいしゃいん","nhân viên công ty"),(15,"医者","いしゃ","bác sĩ"),(15,"銀行員","ぎんこういん","nhân viên ngân hàng"),(15,"働く","はたらく","làm việc"),(15,"忙しい","いそがしい","bận"),(15,"休む","やすむ","nghỉ"),(15,"会議","かいぎ","cuộc họp"),(15,"給料","きゅうりょう","lương"),
    (16,"趣味","しゅみ","sở thích"),(16,"音楽","おんがく","âm nhạc"),(16,"映画","えいが","phim"),(16,"写真","しゃしん","ảnh"),(16,"旅行","りょこう","du lịch"),(16,"泳ぐ","およぐ","bơi"),(16,"聞く","きく","nghe"),(16,"見る","みる","xem"),(16,"作る","つくる","làm, tạo"),(16,"好き","すき","thích"),
    (17,"町","まち","thị trấn"),(17,"駅前","えきまえ","trước ga"),(17,"銀行","ぎんこう","ngân hàng"),(17,"郵便局","ゆうびんきょく","bưu điện"),(17,"病院","びょういん","bệnh viện"),(17,"図書館","としょかん","thư viện"),(17,"公園","こうえん","công viên"),(17,"交差点","こうさてん","ngã tư"),(17,"右","みぎ","bên phải"),(17,"左","ひだり","bên trái"),
    (18,"大きい","おおきい","to"),(18,"小さい","ちいさい","nhỏ"),(18,"新しい","あたらしい","mới"),(18,"古い","ふるい","cũ"),(18,"面白い","おもしろい","thú vị"),(18,"楽しい","たのしい","vui"),(18,"難しい","むずかしい","khó"),(18,"易しい","やさしい","dễ"),(18,"きれい","きれい","đẹp; sạch"),(18,"静か","しずか","yên tĩnh"),
    (19,"メニュー","メニュー","thực đơn"),(19,"注文","ちゅうもん","gọi món"),(19,"料理","りょうり","món ăn; nấu ăn"),(19,"朝ご飯","あさごはん","bữa sáng"),(19,"昼ご飯","ひるごはん","bữa trưa"),(19,"晩ご飯","ばんごはん","bữa tối"),(19,"砂糖","さとう","đường"),(19,"塩","しお","muối"),(19,"ください","ください","xin hãy cho tôi"),(19,"払う","はらう","thanh toán"),
    (20,"電話","でんわ","điện thoại"),(20,"メール","メール","email"),(20,"約束","やくそく","cuộc hẹn; lời hứa"),(20,"会う","あう","gặp"),(20,"話す","はなす","nói chuyện"),(20,"待つ","まつ","đợi"),(20,"送る","おくる","gửi"),(20,"もらう","もらう","nhận"),(20,"一緒に","いっしょに","cùng nhau"),(20,"また","また","lại; hẹn gặp lại"),
    (21,"犬","いぬ","chó"),(21,"猫","ねこ","mèo"),(21,"鳥","とり","chim"),(21,"馬","うま","ngựa"),(21,"牛","うし","bò"),(21,"動物","どうぶつ","động vật"),(21,"ペット","ペット","thú cưng"),(21,"魚","さかな","cá"),(21,"虫","むし","côn trùng"),(21,"うさぎ","うさぎ","thỏ"),
]

# Ví dụ được biên soạn cho lộ trình mở đầu. Các bài còn lại tiếp tục dùng cùng
# cấu trúc dữ liệu này để không phải đổi giao diện hay cơ sở dữ liệu về sau.
# Không sao chép ví dụ từ nguồn tham khảo bên ngoài.
VOCABULARY_EXAMPLES = {
    ("こんにちは", "こんにちは"): ("こんにちは。田中です。", "こんにちは。たなかです。", "Xin chào. Tôi là Tanaka."),
    ("おはよう", "おはよう"): ("おはよう。今日は元気ですか。", "おはよう。きょうは げんき ですか。", "Chào buổi sáng. Hôm nay bạn khỏe không?"),
    ("こんばんは", "こんばんは"): ("こんばんは。今日は寒いですね。", "こんばんは。きょうは さむい ですね。", "Chào buổi tối. Hôm nay trời lạnh nhỉ."),
    ("さようなら", "さようなら"): ("さようなら。また明日。", "さようなら。また あした。", "Tạm biệt. Hẹn gặp lại ngày mai."),
    ("ありがとう", "ありがとう"): ("ありがとう。とても嬉しいです。", "ありがとう。とても うれしい です。", "Cảm ơn. Tôi rất vui."),
    ("すみません", "すみません"): ("すみません、駅はどこですか。", "すみません、えき は どこ ですか。", "Xin lỗi, ga ở đâu ạ?"),
    ("はい", "はい"): ("はい、分かりました。", "はい、わかりました。", "Vâng, tôi hiểu rồi."),
    ("いいえ", "いいえ"): ("いいえ、これは私の本です。", "いいえ、これは わたし の ほん です。", "Không, đây là sách của tôi."),
    ("お願いします", "おねがいします"): ("これをお願いします。", "これを おねがいします。", "Làm ơn cho tôi cái này."),
    ("はじめまして", "はじめまして"): ("はじめまして。山田です。", "はじめまして。やまだ です。", "Rất hân hạnh được gặp. Tôi là Yamada."),
}

# Kho rà soát: chưa xuất hiện trên giao diện cho đến khi một chủ đề có đủ từ và được duyệt.
# JLPT không có danh sách từ vựng N5 chính thức; các mục này là ứng viên N5 tham khảo,
# nghĩa Việt được KanjiAI biên soạn dựa trên JMdict/EDICT.
N5_STAGING_WORDS = [
    ("Đại từ & chỉ định", "これ", "これ", "cái này"), ("Đại từ & chỉ định", "それ", "それ", "cái đó"), ("Đại từ & chỉ định", "あれ", "あれ", "cái kia"), ("Đại từ & chỉ định", "どれ", "どれ", "cái nào"),
    ("Đại từ & chỉ định", "ここ", "ここ", "ở đây"), ("Đại từ & chỉ định", "そこ", "そこ", "ở đó"), ("Đại từ & chỉ định", "あそこ", "あそこ", "ở đằng kia"), ("Đại từ & chỉ định", "どこ", "どこ", "ở đâu"),
    ("Đại từ & chỉ định", "誰", "だれ", "ai"), ("Đại từ & chỉ định", "何", "なに", "cái gì"),
    ("Giao tiếp cơ bản", "どうぞ", "どうぞ", "mời; xin mời"), ("Giao tiếp cơ bản", "大丈夫", "だいじょうぶ", "ổn; không sao"), ("Giao tiếp cơ bản", "分かる", "わかる", "hiểu"), ("Giao tiếp cơ bản", "知る", "しる", "biết"),
    ("Giao tiếp cơ bản", "あります", "あります", "có (đồ vật)"), ("Giao tiếp cơ bản", "います", "います", "có (người; con vật)"), ("Giao tiếp cơ bản", "欲しい", "ほしい", "muốn"), ("Giao tiếp cơ bản", "少し", "すこし", "một ít"),
    ("Sinh hoạt hằng ngày", "起きる", "おきる", "thức dậy"), ("Sinh hoạt hằng ngày", "寝る", "ねる", "ngủ"), ("Sinh hoạt hằng ngày", "洗う", "あらう", "rửa"), ("Sinh hoạt hằng ngày", "シャワー", "シャワー", "vòi sen; tắm vòi sen"),
    ("Sinh hoạt hằng ngày", "洗濯", "せんたく", "giặt giũ"), ("Sinh hoạt hằng ngày", "料理する", "りょうりする", "nấu ăn"), ("Sinh hoạt hằng ngày", "出かける", "でかける", "ra ngoài"), ("Sinh hoạt hằng ngày", "入る", "はいる", "vào"),
    ("Địa điểm công cộng", "スーパー", "スーパー", "siêu thị"), ("Địa điểm công cộng", "レストラン", "レストラン", "nhà hàng"), ("Địa điểm công cộng", "喫茶店", "きっさてん", "quán cà phê"), ("Địa điểm công cộng", "空港", "くうこう", "sân bay"),
    ("Địa điểm công cộng", "ホテル", "ホテル", "khách sạn"), ("Địa điểm công cộng", "デパート", "デパート", "bách hóa"), ("Địa điểm công cộng", "トイレ", "トイレ", "nhà vệ sinh"), ("Địa điểm công cộng", "入口", "いりぐち", "lối vào"),
    ("Đồ dùng hằng ngày", "かばん", "かばん", "túi xách"), ("Đồ dùng hằng ngày", "傘", "かさ", "ô; dù"), ("Đồ dùng hằng ngày", "時計", "とけい", "đồng hồ"), ("Đồ dùng hằng ngày", "鍵", "かぎ", "chìa khóa"),
    ("Đồ dùng hằng ngày", "新聞", "しんぶん", "báo"), ("Đồ dùng hằng ngày", "手紙", "てがみ", "thư"), ("Đồ dùng hằng ngày", "カメラ", "カメラ", "máy ảnh"), ("Đồ dùng hằng ngày", "自転車", "じてんしゃ", "xe đạp"),
    ("Thức ăn & đồ uống", "パン", "パン", "bánh mì"), ("Thức ăn & đồ uống", "卵", "たまご", "trứng"), ("Thức ăn & đồ uống", "牛乳", "ぎゅうにゅう", "sữa bò"), ("Thức ăn & đồ uống", "コーヒー", "コーヒー", "cà phê"),
    ("Thức ăn & đồ uống", "ジュース", "ジュース", "nước ép"), ("Thức ăn & đồ uống", "りんご", "りんご", "táo"), ("Thức ăn & đồ uống", "みかん", "みかん", "quýt"), ("Thức ăn & đồ uống", "カレー", "カレー", "cà ri"),
    ("Miêu tả cơ bản", "早い", "はやい", "sớm; nhanh"), ("Miêu tả cơ bản", "遅い", "おそい", "muộn; chậm"), ("Miêu tả cơ bản", "近い", "ちかい", "gần"), ("Miêu tả cơ bản", "遠い", "とおい", "xa"),
    ("Miêu tả cơ bản", "暖かい", "あたたかい", "ấm"), ("Miêu tả cơ bản", "寒い", "さむい", "lạnh"), ("Miêu tả cơ bản", "元気", "げんき", "khỏe; năng động"), ("Miêu tả cơ bản", "有名", "ゆうめい", "nổi tiếng"),
    ("Giao tiếp cơ bản", "どういたしまして", "どういたしまして", "không có gì"), ("Giao tiếp cơ bản", "ちょっと", "ちょっと", "một chút; xin lỗi"),
    ("Địa điểm công cộng", "出口", "でぐち", "lối ra"), ("Địa điểm công cộng", "交番", "こうばん", "đồn cảnh sát"),
    ("Đồ dùng hằng ngày", "眼鏡", "めがね", "kính mắt"), ("Đồ dùng hằng ngày", "地図", "ちず", "bản đồ"),
    ("Thức ăn & đồ uống", "そば", "そば", "mì soba"), ("Thức ăn & đồ uống", "お弁当", "おべんとう", "cơm hộp"),
    ("Sinh hoạt hằng ngày", "乗る", "のる", "lên; đi bằng (xe)"), ("Sinh hoạt hằng ngày", "降りる", "おりる", "xuống (xe)"),
    ("Miêu tả cơ bản", "重い", "おもい", "nặng"), ("Miêu tả cơ bản", "軽い", "かるい", "nhẹ"),
]

# Khi một nhóm đã đủ 10 từ, nó được duyệt thành bài học con và mở được flashcard.
STAGING_PROMOTIONS = {
    "Đại từ, chỉ định & nghi vấn": ("Chỉ định & câu hỏi", "Từ để chỉ người, vật, nơi chốn và đặt câu hỏi.", 22),
    "Chào hỏi & lịch sự": ("Giao tiếp thiết yếu", "Các câu đáp và cách giao tiếp lịch sự hằng ngày.", 23),
    "Địa điểm công cộng": ("Địa điểm công cộng", "Những địa điểm và biển chỉ dẫn thường gặp.", 24),
    "Nhà cửa, đồ dùng & học tập": ("Đồ dùng mang theo", "Vật dụng cá nhân dùng khi đi học và ra ngoài.", 25),
    "Thức ăn & đồ uống": ("Món ăn & đồ uống", "Thức ăn, đồ uống và món quen thuộc.", 26),
    "Động từ hành động": ("Hành động hằng ngày", "Các động từ dùng trong sinh hoạt và di chuyển.", 27),
    "Tính từ & miêu tả": ("Miêu tả khoảng cách & trạng thái", "Tính từ chỉ thời gian, khoảng cách, thời tiết và trạng thái.", 28),
    "Đơn vị đếm": ("Đếm đồ vật & con người", "Đơn vị đếm nền tảng dùng trong giao tiếp.", 29),
    "Con người & nghề nghiệp": ("Con người xung quanh", "Cách gọi người, quan hệ và quốc tịch.", 30),
    "Di chuyển & phương tiện": ("Phương tiện & lộ trình", "Phương tiện, vé và hành động khi di chuyển.", 31),
    "Nhà cửa, đồ dùng & học tập": ("Đồ dùng trong nhà", "Những đồ dùng và khu vực quen thuộc ở nhà.", 32),
    "Quần áo, mua sắm & màu sắc": ("Trang phục & phụ kiện", "Trang phục, phụ kiện và màu sắc.", 33),
    "Thiên nhiên & thời tiết": ("Cảnh vật & bầu trời", "Cảnh vật, bầu trời và thời tiết.", 34),
    "Động từ hành động": ("Thao tác hằng ngày", "Động từ chỉ thao tác với đồ vật và hoạt động thường ngày.", 35),
    "Động từ trạng thái & sở thích": ("Trạng thái & học tập", "Động từ chỉ trạng thái, ghi nhớ và học hỏi.", 36),
    "Thời gian & lịch": ("Ngày trong tuần & buổi", "Các ngày trong tuần, buổi trong ngày và thời điểm.", 37),
    "Lời chào trong tình huống": ("Lời chào trong tình huống", "Lời chào và phép lịch sự trong các tình huống quen thuộc.", 38, "Chào hỏi & lịch sự"),
    "Giá & thanh toán": ("Giá & thanh toán", "Từ dùng khi xem giá, mua bán và thanh toán.", 39, "Quần áo, mua sắm & màu sắc"),
    "Hoạt động giải trí": ("Hoạt động giải trí", "Các hoạt động thể thao và giải trí cơ bản.", 40, "Động từ trạng thái & sở thích"),
    "Sức khỏe thường gặp": ("Sức khỏe thường gặp", "Từ mô tả cơ thể, bệnh nhẹ và tình trạng sức khỏe.", 41, "Cơ thể & sức khỏe"),
    "Món ăn cơ bản": ("Món ăn cơ bản", "Tên các món ăn và đồ uống quen thuộc.", 42, "Thức ăn & đồ uống"),
    "Địa điểm học & làm": ("Địa điểm học & làm", "Các địa điểm liên quan đến học tập, công việc và dịch vụ.", 43, "Địa điểm công cộng"),
    "Tính từ cảm xúc": ("Tính từ cảm xúc", "Tính từ miêu tả cảm xúc, độ sáng và hương vị.", 44, "Tính từ & miêu tả"),
    "Ngôn ngữ & quốc gia": ("Ngôn ngữ & quốc gia", "Tên ngôn ngữ, quốc gia và chữ viết cơ bản.", 45, "Con người & nghề nghiệp"),
    "Lớp học & kiểm tra": ("Lớp học & kiểm tra", "Từ dùng trong giờ học, bài kiểm tra và tài liệu.", 46, "Nhà cửa, đồ dùng & học tập"),
    "Động vật khác": ("Động vật khác", "Tên một số động vật thường gặp.", 47, "Động vật"),
    "Việc nhà": ("Việc nhà", "Động từ thường dùng khi làm việc nhà.", 48, "Động từ hành động"),
    "Thiết bị trong nhà": ("Thiết bị trong nhà", "Đồ dùng, thiết bị và vật dụng thường gặp trong nhà.", 49, "Nhà cửa, đồ dùng & học tập"),
    "Phương hướng & vị trí": ("Phương hướng & vị trí", "Từ chỉ phương hướng và vị trí khi hỏi đường.", 50, "Di chuyển & phương tiện"),
    "Thời tiết thay đổi": ("Thời tiết thay đổi", "Hiện tượng thời tiết và cảnh vật theo mùa.", 51, "Thiên nhiên & thời tiết"),
    "Chăm sóc cá nhân": ("Chăm sóc cá nhân", "Đồ dùng và hoạt động chăm sóc cơ thể.", 52, "Cơ thể & sức khỏe"),
    "Trạng từ & mức độ": ("Trạng từ & mức độ", "Từ chỉ mức độ, tần suất và thời điểm thường dùng trong câu N5.", 53, "Trạng từ & mức độ"),
}

N5_STAGING_WORDS += [
    ("Đơn vị đếm", "ひとつ", "ひとつ", "một cái"), ("Đơn vị đếm", "ふたつ", "ふたつ", "hai cái"), ("Đơn vị đếm", "みっつ", "みっつ", "ba cái"), ("Đơn vị đếm", "よっつ", "よっつ", "bốn cái"), ("Đơn vị đếm", "一人", "ひとり", "một người"),
    ("Đơn vị đếm", "二人", "ふたり", "hai người"), ("Đơn vị đếm", "枚", "まい", "đơn vị đếm vật mỏng"), ("Đơn vị đếm", "冊", "さつ", "đơn vị đếm sách"), ("Đơn vị đếm", "個", "こ", "đơn vị đếm đồ vật"), ("Đơn vị đếm", "匹", "ひき", "đơn vị đếm con vật nhỏ"),
    ("Con người & nghề nghiệp", "女", "おんな", "phụ nữ"), ("Con người & nghề nghiệp", "女の人", "おんなのひと", "người phụ nữ"), ("Con người & nghề nghiệp", "男の人", "おとこのひと", "người đàn ông"), ("Con người & nghề nghiệp", "お客さん", "おきゃくさん", "khách"), ("Con người & nghề nghiệp", "夫", "おっと", "chồng"),
    ("Con người & nghề nghiệp", "妻", "つま", "vợ"), ("Con người & nghề nghiệp", "奥さん", "おくさん", "vợ của người khác"), ("Con người & nghề nghiệp", "主人", "しゅじん", "chồng của tôi"), ("Con người & nghề nghiệp", "皆さん", "みなさん", "mọi người"), ("Con người & nghề nghiệp", "外国人", "がいこくじん", "người nước ngoài"),
    ("Di chuyển & phương tiện", "バス", "バス", "xe buýt"), ("Di chuyển & phương tiện", "タクシー", "タクシー", "taxi"), ("Di chuyển & phương tiện", "飛行機", "ひこうき", "máy bay"), ("Di chuyển & phương tiện", "船", "ふね", "tàu thuyền"), ("Di chuyển & phương tiện", "地下鉄", "ちかてつ", "tàu điện ngầm"),
    ("Di chuyển & phương tiện", "乗り場", "のりば", "điểm lên xe"), ("Di chuyển & phương tiện", "切符", "きっぷ", "vé"), ("Di chuyển & phương tiện", "運転", "うんてん", "lái xe"), ("Di chuyển & phương tiện", "走る", "はしる", "chạy"), ("Di chuyển & phương tiện", "曲がる", "まがる", "rẽ"),
    ("Nhà cửa, đồ dùng & học tập", "洗面所", "せんめんじょ", "nhà rửa mặt"), ("Nhà cửa, đồ dùng & học tập", "お風呂", "おふろ", "bồn tắm; phòng tắm"), ("Nhà cửa, đồ dùng & học tập", "庭", "にわ", "sân vườn"), ("Nhà cửa, đồ dùng & học tập", "箱", "はこ", "cái hộp"), ("Nhà cửa, đồ dùng & học tập", "ごみ箱", "ごみばこ", "thùng rác"),
    ("Nhà cửa, đồ dùng & học tập", "皿", "さら", "cái đĩa"), ("Nhà cửa, đồ dùng & học tập", "コップ", "コップ", "cốc"), ("Nhà cửa, đồ dùng & học tập", "ナイフ", "ナイフ", "dao"), ("Nhà cửa, đồ dùng & học tập", "フォーク", "フォーク", "nĩa"), ("Nhà cửa, đồ dùng & học tập", "電気", "でんき", "điện; đèn điện"),
    ("Quần áo, mua sắm & màu sắc", "黄色", "きいろ", "màu vàng"), ("Quần áo, mua sắm & màu sắc", "茶色", "ちゃいろ", "màu nâu"), ("Quần áo, mua sắm & màu sắc", "灰色", "はいいろ", "màu xám"), ("Quần áo, mua sắm & màu sắc", "手袋", "てぶくろ", "găng tay"), ("Quần áo, mua sắm & màu sắc", "靴下", "くつした", "tất"),
    ("Quần áo, mua sắm & màu sắc", "ネクタイ", "ネクタイ", "cà vạt"), ("Quần áo, mua sắm & màu sắc", "コート", "コート", "áo khoác dài"), ("Quần áo, mua sắm & màu sắc", "ジーンズ", "ジーンズ", "quần jean"), ("Quần áo, mua sắm & màu sắc", "サイズ", "サイズ", "kích cỡ"), ("Quần áo, mua sắm & màu sắc", "売る", "うる", "bán"),
    ("Thiên nhiên & thời tiết", "海", "うみ", "biển"), ("Thiên nhiên & thời tiết", "森", "もり", "rừng"), ("Thiên nhiên & thời tiết", "池", "いけ", "ao"), ("Thiên nhiên & thời tiết", "星", "ほし", "ngôi sao"), ("Thiên nhiên & thời tiết", "太陽", "たいよう", "mặt trời"),
    ("Thiên nhiên & thời tiết", "雲", "くも", "mây"), ("Thiên nhiên & thời tiết", "曇り", "くもり", "trời nhiều mây"), ("Thiên nhiên & thời tiết", "涼しい", "すずしい", "mát mẻ"), ("Thiên nhiên & thời tiết", "季節", "きせつ", "mùa"), ("Thiên nhiên & thời tiết", "光", "ひかり", "ánh sáng"),
    ("Động từ hành động", "開ける", "あける", "mở"), ("Động từ hành động", "閉める", "しめる", "đóng"), ("Động từ hành động", "立つ", "たつ", "đứng"), ("Động từ hành động", "座る", "すわる", "ngồi"), ("Động từ hành động", "持つ", "もつ", "cầm; mang"),
    ("Động từ hành động", "置く", "おく", "đặt"), ("Động từ hành động", "使う", "つかう", "dùng"), ("Động từ hành động", "消す", "けす", "tắt; xóa"), ("Động từ hành động", "つける", "つける", "bật; gắn"), ("Động từ hành động", "止まる", "とまる", "dừng"),
    ("Động từ trạng thái & sở thích", "住む", "すむ", "sống; cư trú"), ("Động từ trạng thái & sở thích", "要る", "いる", "cần"), ("Động từ trạng thái & sở thích", "できる", "できる", "có thể; hoàn thành"), ("Động từ trạng thái & sở thích", "覚える", "おぼえる", "ghi nhớ"), ("Động từ trạng thái & sở thích", "忘れる", "わすれる", "quên"),
    ("Động từ trạng thái & sở thích", "教える", "おしえる", "dạy; chỉ cho"), ("Động từ trạng thái & sở thích", "習う", "ならう", "học từ ai"), ("Động từ trạng thái & sở thích", "結婚する", "けっこんする", "kết hôn"), ("Động từ trạng thái & sở thích", "遊ぶ", "あそぶ", "chơi"), ("Động từ trạng thái & sở thích", "かかる", "かかる", "mất; tốn (thời gian/tiền)"),
]

N5_STAGING_WORDS += [
    ("Thiết bị trong nhà", "電子レンジ", "でんしレンジ", "lò vi sóng"), ("Thiết bị trong nhà", "洗濯機", "せんたくき", "máy giặt"), ("Thiết bị trong nhà", "エアコン", "エアコン", "máy điều hòa"), ("Thiết bị trong nhà", "ストーブ", "ストーブ", "lò sưởi"), ("Thiết bị trong nhà", "カーテン", "カーテン", "rèm cửa"),
    ("Thiết bị trong nhà", "鏡", "かがみ", "gương"), ("Thiết bị trong nhà", "布団", "ふとん", "chăn đệm"), ("Thiết bị trong nhà", "棚", "たな", "kệ"), ("Thiết bị trong nhà", "電池", "でんち", "pin"), ("Thiết bị trong nhà", "コンセント", "コンセント", "ổ cắm điện"),
    ("Phương hướng & vị trí", "まっすぐ", "まっすぐ", "thẳng"), ("Phương hướng & vị trí", "近く", "ちかく", "gần; khu vực gần"), ("Phương hướng & vị trí", "向こう", "むこう", "phía bên kia"), ("Phương hướng & vị trí", "隣", "となり", "bên cạnh"), ("Phương hướng & vị trí", "前", "まえ", "phía trước"),
    ("Phương hướng & vị trí", "後ろ", "うしろ", "phía sau"), ("Phương hướng & vị trí", "上", "うえ", "phía trên"), ("Phương hướng & vị trí", "下", "した", "phía dưới"), ("Phương hướng & vị trí", "中", "なか", "bên trong"), ("Phương hướng & vị trí", "外", "そと", "bên ngoài"),
    ("Thời tiết thay đổi", "雷", "かみなり", "sấm"), ("Thời tiết thay đổi", "台風", "たいふう", "bão"), ("Thời tiết thay đổi", "気温", "きおん", "nhiệt độ không khí"), ("Thời tiết thay đổi", "湿度", "しつど", "độ ẩm"), ("Thời tiết thay đổi", "霧", "きり", "sương mù"),
    ("Thời tiết thay đổi", "氷", "こおり", "băng"), ("Thời tiết thay đổi", "虹", "にじ", "cầu vồng"), ("Thời tiết thay đổi", "日差し", "ひざし", "ánh nắng"), ("Thời tiết thay đổi", "夕方", "ゆうがた", "chiều tối"), ("Thời tiết thay đổi", "梅雨", "つゆ", "mùa mưa"),
    ("Chăm sóc cá nhân", "歯ブラシ", "はブラシ", "bàn chải đánh răng"), ("Chăm sóc cá nhân", "石鹸", "せっけん", "xà phòng"), ("Chăm sóc cá nhân", "タオル", "タオル", "khăn"), ("Chăm sóc cá nhân", "ひげ", "ひげ", "râu"), ("Chăm sóc cá nhân", "爪", "つめ", "móng tay; móng chân"),
    ("Chăm sóc cá nhân", "化粧", "けしょう", "trang điểm"), ("Chăm sóc cá nhân", "化粧品", "けしょうひん", "mỹ phẩm"), ("Chăm sóc cá nhân", "美容院", "びよういん", "tiệm làm tóc"), ("Chăm sóc cá nhân", "体温", "たいおん", "nhiệt độ cơ thể"), ("Chăm sóc cá nhân", "注射", "ちゅうしゃ", "tiêm; mũi tiêm"),
]

N5_STAGING_WORDS += [
    ("Ngôn ngữ & quốc gia", "日本語", "にほんご", "tiếng Nhật"), ("Ngôn ngữ & quốc gia", "英語", "えいご", "tiếng Anh"), ("Ngôn ngữ & quốc gia", "中国語", "ちゅうごくご", "tiếng Trung"), ("Ngôn ngữ & quốc gia", "韓国語", "かんこくご", "tiếng Hàn"), ("Ngôn ngữ & quốc gia", "フランス語", "フランスご", "tiếng Pháp"),
    ("Ngôn ngữ & quốc gia", "国", "くに", "đất nước"), ("Ngôn ngữ & quốc gia", "言葉", "ことば", "ngôn ngữ; từ ngữ"), ("Ngôn ngữ & quốc gia", "文字", "もじ", "chữ viết; ký tự"), ("Ngôn ngữ & quốc gia", "漢字", "かんじ", "Kanji"), ("Ngôn ngữ & quốc gia", "ひらがな", "ひらがな", "chữ Hiragana"),
    ("Lớp học & kiểm tra", "授業", "じゅぎょう", "giờ học"), ("Lớp học & kiểm tra", "試験", "しけん", "kỳ thi"), ("Lớp học & kiểm tra", "質問", "しつもん", "câu hỏi"), ("Lớp học & kiểm tra", "答え", "こたえ", "câu trả lời"), ("Lớp học & kiểm tra", "黒板", "こくばん", "bảng đen"),
    ("Lớp học & kiểm tra", "消しゴム", "けしゴム", "cục tẩy"), ("Lớp học & kiểm tra", "ペン", "ペン", "bút mực"), ("Lớp học & kiểm tra", "紙", "かみ", "giấy"), ("Lớp học & kiểm tra", "作文", "さくぶん", "bài văn"), ("Lớp học & kiểm tra", "教科書", "きょうかしょ", "sách giáo khoa"),
    ("Động vật khác", "猿", "さる", "khỉ"), ("Động vật khác", "象", "ぞう", "voi"), ("Động vật khác", "ライオン", "ライオン", "sư tử"), ("Động vật khác", "虎", "とら", "hổ"), ("Động vật khác", "熊", "くま", "gấu"),
    ("Động vật khác", "羊", "ひつじ", "cừu"), ("Động vật khác", "亀", "かめ", "rùa"), ("Động vật khác", "蛇", "へび", "rắn"), ("Động vật khác", "きつね", "きつね", "cáo"), ("Động vật khác", "ねずみ", "ねずみ", "chuột"),
    ("Việc nhà", "片付ける", "かたづける", "dọn dẹp; sắp xếp"), ("Việc nhà", "磨く", "みがく", "đánh; chà"), ("Việc nhà", "沸かす", "わかす", "đun sôi"), ("Việc nhà", "捨てる", "すてる", "vứt bỏ"), ("Việc nhà", "直す", "なおす", "sửa"),
    ("Việc nhà", "壊れる", "こわれる", "bị hỏng"), ("Việc nhà", "開く", "あく", "mở ra"), ("Việc nhà", "閉まる", "しまる", "đóng lại"), ("Việc nhà", "乾く", "かわく", "khô"), ("Việc nhà", "濡れる", "ぬれる", "bị ướt"),
]

N5_STAGING_WORDS += [
    ("Sức khỏe thường gặp", "お腹", "おなか", "bụng"), ("Sức khỏe thường gặp", "背中", "せなか", "lưng"), ("Sức khỏe thường gặp", "歯", "は", "răng"), ("Sức khỏe thường gặp", "鼻", "はな", "mũi"), ("Sức khỏe thường gặp", "顔", "かお", "khuôn mặt"),
    ("Sức khỏe thường gặp", "のど", "のど", "cổ họng"), ("Sức khỏe thường gặp", "熱", "ねつ", "sốt"), ("Sức khỏe thường gặp", "風邪", "かぜ", "cảm lạnh"), ("Sức khỏe thường gặp", "けが", "けが", "chấn thương"), ("Sức khỏe thường gặp", "健康", "けんこう", "sức khỏe"),
    ("Món ăn cơ bản", "味噌", "みそ", "tương miso"), ("Món ăn cơ bản", "スープ", "スープ", "súp"), ("Món ăn cơ bản", "ラーメン", "ラーメン", "mì ramen"), ("Món ăn cơ bản", "うどん", "うどん", "mì udon"), ("Món ăn cơ bản", "サラダ", "サラダ", "sa lát"),
    ("Món ăn cơ bản", "ケーキ", "ケーキ", "bánh ngọt"), ("Món ăn cơ bản", "バナナ", "バナナ", "chuối"), ("Món ăn cơ bản", "いちご", "いちご", "dâu tây"), ("Món ăn cơ bản", "ビール", "ビール", "bia"), ("Món ăn cơ bản", "お酒", "おさけ", "rượu"),
    ("Địa điểm học & làm", "大学", "だいがく", "đại học"), ("Địa điểm học & làm", "小学校", "しょうがっこう", "trường tiểu học"), ("Địa điểm học & làm", "中学校", "ちゅうがっこう", "trường trung học cơ sở"), ("Địa điểm học & làm", "高校", "こうこう", "trường trung học phổ thông"), ("Địa điểm học & làm", "工場", "こうじょう", "nhà máy"),
    ("Địa điểm học & làm", "美術館", "びじゅつかん", "bảo tàng mỹ thuật"), ("Địa điểm học & làm", "映画館", "えいがかん", "rạp chiếu phim"), ("Địa điểm học & làm", "本屋", "ほんや", "hiệu sách"), ("Địa điểm học & làm", "薬局", "やっきょく", "nhà thuốc"), ("Địa điểm học & làm", "駐車場", "ちゅうしゃじょう", "bãi đỗ xe"),
    ("Tính từ cảm xúc", "嬉しい", "うれしい", "vui mừng"), ("Tính từ cảm xúc", "悲しい", "かなしい", "buồn"), ("Tính từ cảm xúc", "怖い", "こわい", "đáng sợ"), ("Tính từ cảm xúc", "寂しい", "さびしい", "cô đơn"), ("Tính từ cảm xúc", "強い", "つよい", "mạnh"),
    ("Tính từ cảm xúc", "弱い", "よわい", "yếu"), ("Tính từ cảm xúc", "明るい", "あかるい", "sáng; vui vẻ"), ("Tính từ cảm xúc", "暗い", "くらい", "tối; u ám"), ("Tính từ cảm xúc", "甘い", "あまい", "ngọt"), ("Tính từ cảm xúc", "辛い", "からい", "cay"),
]

N5_STAGING_WORDS += [
    ("Thời gian & lịch", "月曜日", "げつようび", "thứ Hai"), ("Thời gian & lịch", "火曜日", "かようび", "thứ Ba"), ("Thời gian & lịch", "水曜日", "すいようび", "thứ Tư"), ("Thời gian & lịch", "木曜日", "もくようび", "thứ Năm"), ("Thời gian & lịch", "金曜日", "きんようび", "thứ Sáu"),
    ("Thời gian & lịch", "土曜日", "どようび", "thứ Bảy"), ("Thời gian & lịch", "日曜日", "にちようび", "Chủ nhật"), ("Thời gian & lịch", "午前", "ごぜん", "buổi sáng; AM"), ("Thời gian & lịch", "午後", "ごご", "buổi chiều; PM"), ("Thời gian & lịch", "半", "はん", "rưỡi; nửa"),
    ("Lời chào trong tình huống", "いらっしゃいませ", "いらっしゃいませ", "xin chào quý khách"), ("Lời chào trong tình huống", "おめでとうございます", "おめでとうございます", "chúc mừng"), ("Lời chào trong tình huống", "失礼します", "しつれいします", "xin phép; thất lễ"), ("Lời chào trong tình huống", "いただきます", "いただきます", "cảm ơn trước bữa ăn"), ("Lời chào trong tình huống", "ごちそうさまでした", "ごちそうさまでした", "cảm ơn sau bữa ăn"),
    ("Lời chào trong tình huống", "おやすみなさい", "おやすみなさい", "chúc ngủ ngon"), ("Lời chào trong tình huống", "もしもし", "もしもし", "a lô"), ("Lời chào trong tình huống", "いってきます", "いってきます", "tôi đi đây"), ("Lời chào trong tình huống", "いってらっしゃい", "いってらっしゃい", "đi cẩn thận nhé"), ("Lời chào trong tình huống", "ただいま", "ただいま", "tôi về rồi"),
    ("Giá & thanh toán", "値段", "ねだん", "giá tiền"), ("Giá & thanh toán", "円", "えん", "yên Nhật"), ("Giá & thanh toán", "お釣り", "おつり", "tiền thối"), ("Giá & thanh toán", "貸す", "かす", "cho mượn"), ("Giá & thanh toán", "返す", "かえす", "trả lại"),
    ("Giá & thanh toán", "品物", "しなもの", "hàng hóa"), ("Giá & thanh toán", "財布", "さいふ", "ví tiền"), ("Giá & thanh toán", "レジ", "レジ", "quầy tính tiền"), ("Giá & thanh toán", "商品", "しょうひん", "sản phẩm; hàng hóa"), ("Giá & thanh toán", "予約", "よやく", "đặt trước; đặt chỗ"),
    ("Hoạt động giải trí", "スポーツ", "スポーツ", "thể thao"), ("Hoạt động giải trí", "サッカー", "サッカー", "bóng đá"), ("Hoạt động giải trí", "テニス", "テニス", "quần vợt"), ("Hoạt động giải trí", "野球", "やきゅう", "bóng chày"), ("Hoạt động giải trí", "読書", "どくしょ", "đọc sách"),
    ("Hoạt động giải trí", "散歩", "さんぽ", "đi dạo"), ("Hoạt động giải trí", "練習", "れんしゅう", "luyện tập"), ("Hoạt động giải trí", "歌", "うた", "bài hát"), ("Hoạt động giải trí", "歌う", "うたう", "hát"), ("Hoạt động giải trí", "ギター", "ギター", "đàn ghi-ta"),
]

# Bài 53: một nhóm ngữ pháp nhỏ, dùng để ghép câu với các bài trước.
N5_STAGING_WORDS += [
    ("Trạng từ & mức độ", "とても", "とても", "rất"),
    ("Trạng từ & mức độ", "あまり", "あまり", "không ... lắm (thường đi với phủ định)"),
    ("Trạng từ & mức độ", "いつも", "いつも", "luôn luôn"),
    ("Trạng từ & mức độ", "よく", "よく", "thường; tốt"),
    ("Trạng từ & mức độ", "時々", "ときどき", "đôi khi"),
    ("Trạng từ & mức độ", "もう", "もう", "đã; nữa"),
    ("Trạng từ & mức độ", "まだ", "まだ", "vẫn; chưa"),
    ("Trạng từ & mức độ", "一番", "いちばん", "nhất"),
    ("Trạng từ & mức độ", "全然", "ぜんぜん", "hoàn toàn; không hề (thường đi với phủ định)"),
    ("Trạng từ & mức độ", "だいたい", "だいたい", "đại khái; thường thường"),
]
