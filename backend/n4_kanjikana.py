"""Kanjikana's Vietnamese JLPT N4 inventory, in display order."""

SOURCE = """事|vấn đề
会|cuộc họp
自|bản thân
手|tay
言|nói
者|ai đó
同|giống nhau
方|hướng
目|mắt
理|lý do
力|sức mạnh
場|nơi chốn
思|nghĩ
家|nhà
動|di chuyển
地|mặt đất
体|cơ thể
作|làm
持|giữ
明|sáng
私|riêng tư
発|khởi hành
心|trái tim
意|ý tưởng
度|độ
知|biết
立|đứng
通|đi qua
不|không
員|nhân viên
物|đồ vật
的|mục tiêu
問|câu hỏi
用|sử dụng
新|mới
田|ruộng
代|thay thế
世|thế hệ
死|cái chết
開|mở
社|công ty
無|không có
強|mạnh
教|dạy
野|đồng bằng
正|đúng
業|nghề nghiệp
題|chủ đề
使|sử dụng
考|suy nghĩ
界|thế giới
別|khác biệt
元|gốc, nguyên
以|bằng, từ
待|chờ
安|an toàn
近|gần
真|đúng, thật
少|ít
切|cắt
主|chủ
終|kết thúc
楽|vui, nhạc
音|âm thanh
道|đường
着|mặc, đến
親|cha mẹ
始|bắt đầu
多|nhiều
早|sớm
仕|làm việc
海|biển
悪|xấu
止|dừng
重|nặng
画|tranh
口|miệng
味|mùi vị
空|trống
身|bản thân
運|vận chuyển
帰|trở về
集|tập hợp
急|vội
足|chân
売|bán
起|thức dậy
夜|đêm
料|phí, nguyên liệu
特|đặc biệt
品|sản phẩm
計|đo, tính
店|cửa hàng
送|gửi, tiễn
族|gia đình
文|văn, câu
院|viện
朝|buổi sáng
転|chuyển, quay
公|công cộng
可|có thể
病|bệnh
住|sống, cư trú
屋|nhà, cửa hàng
買|mua
有|có
試|thử
質|chất lượng
医|y khoa
映|phản chiếu
室|phòng
台|đài, bệ
験|kiểm nghiệm
歌|bài hát
去|rời đi
風|gió
歩|đi bộ
広|rộng
週|tuần
写|chép, chụp
花|hoa
黒|đen
答|trả lời
赤|đỏ
色|màu
町|thị trấn
銀|bạc
工|công, thợ
字|chữ
飲|uống
注|chú ý
走|chạy
京|kinh đô
古|cũ
英|Anh
習|học tập
兄|anh trai
服|quần áo
建|xây
青|xanh
研|nghiên cứu
紙|giấy
究|tìm tòi
春|mùa xuân
図|bản đồ
旅|chuyến đi
肉|thịt
夏|mùa hè
弟|em trai
犬|chó
飯|cơm, bữa ăn
館|toà nhà
貸|cho mượn
堂|sảnh, nhà
借|mượn
秋|mùa thu
姉|chị gái
曜|ngày trong tuần
鳥|chim
夕|buổi tối
茶|trà
魚|cá
妹|em gái
勉|cố gắng
洋|đại dương
昼|ban ngày
牛|bò
冬|mùa đông
駅|ga, trạm
漢|Hán, Trung Quốc"""

KANJIKANA_N4 = [tuple(line.split("|", 1)) for line in SOURCE.splitlines()]

assert len(KANJIKANA_N4) == 170

# Âm Hán Việt được giữ riêng khỏi nghĩa ngắn để có thể tìm kiếm và hiển thị
# nhất quán trên thẻ Kanji.  Đây là dữ liệu học tập, không phải cách đọc tiếng
# Nhật của chữ.
HAN_VIET_SOURCE = """事|SỰ
会|HỘI
自|TỰ
手|THỦ
言|NGÔN
者|GIẢ
同|ĐỒNG
方|PHƯƠNG
目|MỤC
理|LÝ
力|LỰC
場|TRƯỜNG
思|TƯ
家|GIA
動|ĐỘNG
地|ĐỊA
体|THỂ
作|TÁC
持|TRÌ
明|MINH
私|TƯ
発|PHÁT
心|TÂM
意|Ý
度|ĐỘ
知|TRI
立|LẬP
通|THÔNG
不|BẤT
員|VIÊN
物|VẬT
的|ĐÍCH
問|VẤN
用|DỤNG
新|TÂN
田|ĐIỀN
代|ĐẠI
世|THẾ
死|TỬ
開|KHAI
社|XÃ
無|VÔ
強|CƯỜNG
教|GIÁO
野|DÃ
正|CHÍNH
業|NGHIỆP
題|ĐỀ
使|SỬ
考|KHẢO
界|GIỚI
別|BIỆT
元|NGUYÊN
以|DĨ
待|ĐÃI
安|AN
近|CẬN
真|CHÂN
少|THIỂU
切|THIẾT
主|CHỦ
終|CHUNG
楽|LẠC
音|ÂM
道|ĐẠO
着|TRỨ
親|THÂN
始|THỦY
多|ĐA
早|TẢO
仕|SĨ
海|HẢI
悪|ÁC
止|CHỈ
重|TRỌNG
画|HỌA
口|KHẨU
味|VỊ
空|KHÔNG
身|THÂN
運|VẬN
帰|QUY
集|TẬP
急|CẤP
足|TÚC
売|MẠI
起|KHỞI
夜|DẠ
料|LIỆU
特|ĐẶC
品|PHẨM
計|KẾ
店|ĐIẾM
送|TỐNG
族|TỘC
文|VĂN
院|VIỆN
朝|TRIỀU
転|CHUYỂN
公|CÔNG
可|KHẢ
病|BỆNH
住|TRÚ
屋|ỐC
買|MÃI
有|HỮU
試|THÍ
質|CHẤT
医|Y
映|ÁNH
室|THẤT
台|ĐÀI
験|NGHIỆM
歌|CA
去|KHỨ
風|PHONG
歩|BỘ
広|QUẢNG
週|CHU
写|TẢ
花|HOA
黒|HẮC
答|ĐÁP
赤|XÍCH
色|SẮC
町|ĐINH
銀|NGÂN
工|CÔNG
字|TỰ
飲|ẨM
注|CHÚ
走|TẨU
京|KINH
古|CỔ
英|ANH
習|TẬP
兄|HUYNH
服|PHỤC
建|KIẾN
青|THANH
研|NGHIÊN
紙|CHỈ
究|CỨU
春|XUÂN
図|ĐỒ
旅|LỮ
肉|NHỤC
夏|HẠ
弟|ĐỆ
犬|KHUYỂN
飯|PHẠN
館|QUÁN
貸|THẢI
堂|ĐƯỜNG
借|TÁ
秋|THU
姉|TỶ
曜|DIỆU
鳥|ĐIỂU
夕|TỊCH
茶|TRÀ
魚|NGƯ
妹|MUỘI
勉|MIỄN
洋|DƯƠNG
昼|TRÚ
牛|NGƯU
冬|ĐÔNG
駅|DỊCH
漢|HÁN"""

N4_HAN_VIET = dict(line.split("|", 1) for line in HAN_VIET_SOURCE.splitlines())
assert set(N4_HAN_VIET) == {character for character, _ in KANJIKANA_N4}

# Bộ thủ chính để hiển thị.  Dùng trực tiếp ký tự bộ thủ giúp giao diện không
# phải phụ thuộc vào mã số bộ thủ của một nguồn bên ngoài.
RADICAL_SOURCE = """事|亅
会|人
自|自
手|手
言|言
者|老
同|口
方|方
目|目
理|玉
力|力
場|土
思|心
家|宀
動|力
地|土
体|人
作|人
持|手
明|日
私|禾
発|癶
心|心
意|心
度|广
知|矢
立|立
通|辵
不|一
員|貝
物|牛
的|白
問|口
用|用
新|斤
田|田
代|人
世|一
死|歹
開|門
社|示
無|火
強|弓
教|攴
野|里
正|止
業|木
題|頁
使|人
考|老
界|田
別|刀
元|儿
以|人
待|彳
安|女
近|辵
真|目
少|小
切|刀
主|丶
終|糸
楽|木
音|音
道|辵
着|羊
親|見
始|女
多|夕
早|日
仕|人
海|水
悪|心
止|止
重|里
画|田
口|口
味|口
空|穴
身|身
運|辵
帰|巾
集|隹
急|心
足|足
売|儿
起|走
夜|夕
料|斗
特|牛
品|口
計|言
店|广
送|辵
族|方
文|文
院|阜
朝|月
転|車
公|八
可|口
病|疒
住|人
屋|尸
買|貝
有|月
試|言
質|貝
医|匚
映|日
室|宀
台|口
験|馬
歌|欠
去|厶
風|風
歩|止
広|广
週|辵
写|冖
花|艸
黒|黑
答|竹
赤|赤
色|色
町|田
銀|金
工|工
字|子
飲|食
注|水
走|走
京|亠
古|口
英|艸
習|羽
兄|儿
服|月
建|廴
青|青
研|石
紙|糸
究|穴
春|日
図|囗
旅|方
肉|肉
夏|夂
弟|弓
犬|犬
飯|食
館|食
貸|貝
堂|土
借|人
秋|禾
姉|女
曜|日
鳥|鳥
夕|夕
茶|艸
魚|魚
妹|女
勉|力
洋|水
昼|日
牛|牛
冬|冫
駅|馬
漢|水"""

N4_RADICALS = dict(line.split("|", 1) for line in RADICAL_SOURCE.splitlines())
assert set(N4_RADICALS) == {character for character, _ in KANJIKANA_N4}
