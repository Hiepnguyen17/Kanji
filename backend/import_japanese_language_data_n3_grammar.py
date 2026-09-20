"""Import the complete Japanese Language Data N3 grammar inventory.

The source inventory is CC BY-SA 4.0.  KanjiAI supplies the Vietnamese lesson
sequence, explanations, notes, and translations of the selected examples.
Run once after cloning Japanese Language Data locally:

  python backend/import_japanese_language_data_n3_grammar.py \
    --source .grammar-data-source/grammar-curated/n3.json
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

from database import DB_PATH


LESSONS = [
    ("Khi và thời điểm", "Xác định lúc sự việc xảy ra, vừa xảy ra hay đang trong một khoảng thời gian."),
    ("Vẻ ngoài và suy đoán", "Nói điều có vẻ đúng dựa vào dấu hiệu, thông tin nghe được hoặc cảm nhận."),
    ("Chuẩn bị, thử và kết quả", "Diễn tả làm trước, thử làm, kết quả còn lại và hành động đã hoàn tất."),
    ("Mục đích và nguyên nhân", "Nói mục tiêu, nguyên nhân, lý do tích cực hoặc tiêu cực."),
    ("Nhượng bộ và đối lập", "Nối hai ý trái mong đợi, so sánh và nhấn mạnh sự đối lập."),
    ("Danh từ hóa và câu hỏi gián tiếp", "Dùng こと・の để danh từ hóa và diễn đạt điều chưa chắc chắn."),
    ("Quan điểm và quan hệ", "Nêu chủ đề, góc nhìn, tiêu chí và quan hệ giữa các sự việc."),
    ("Khuyên bảo, nghĩa vụ và giả định", "Khuyên ai đó, nói nghĩa vụ, hối tiếc và điều kiện."),
    ("Bị động, sai khiến và trạng thái", "Mô tả bị bắt làm, giữ nguyên trạng thái hoặc không làm việc gì."),
    ("Mức độ, giới hạn và nhấn mạnh", "Nói mức độ, giới hạn, sự độc quyền và ý nhấn mạnh."),
    ("Tiếp diễn, thay đổi và xu hướng", "Diễn tả thay đổi theo thời gian, sự tiếp diễn và khuynh hướng."),
    ("Vai trò, đối tượng và văn phong trang trọng", "Dùng mẫu trang trọng để nêu vai trò, đối tượng, nơi chốn và đối tượng hướng tới."),
    ("Chỉ có, không chỉ và thay thế", "Nêu phạm vi duy nhất, bổ sung thông tin hoặc nói thay cho ai/cái gì."),
    ("Nói cách khác và ví dụ", "Làm rõ, nói về một chủ đề, đưa ví dụ và điều chỉnh cách diễn đạt."),
    ("Cảm giác, vẻ ngoài và đánh giá", "Diễn tả cảm giác mạnh, ấn tượng bề ngoài và đánh giá tương đối."),
    ("Động từ ghép", "Mở rộng nghĩa động từ với 続ける・直す・合う・出す・込む."),
    ("Khả năng, chắc chắn và không thể tránh", "Nêu khả năng, sự chắc chắn, điều không thể hoặc không thể tránh."),
    ("Khoảng thời gian, tần suất và so sánh", "Nói khoảng thời gian, chu kỳ, thay thế và so sánh."),
    ("Biểu hiện cố định và lịch sự", "Tổng hợp biểu hiện cố định, kính ngữ nhẹ và cách nói tự nhiên."),
]

# The source is deliberately grouped by a learning topic instead of copied as
# one alphabetical list.  Every source id must occur exactly once.
GROUPS = {
    1: {"uchi-ni", "aida-ni", "ta-bakari", "ta-tokoro", "tabi-ni-every-time", "to-tan-moment", "irai-since", "chuu-during", "saichu-in-the-middle", "buri-ni-first-time", "te-hajimete-only-after", "ni-ataru-correspond"},
    2: {"you-da-appearance", "mitai-looks-like", "rashii-seems", "ni-chigainai-must", "ki-ga-suru-feel-like", "kke-casual-wondering"},
    3: {"te-oku", "te-shimau", "te-aru", "te-miru", "te-iku", "te-kuru", "ue-de-upon"},
    4: {"tame-ni", "you-ni-purpose", "okage-sei-de", "n-da-kara-emphatic", "mono-reason-assertion", "mon-casual-because"},
    5: {"noni-although", "kuse-ni-despite", "ni-shitemo-even", "to-wa-kagiranai", "dokoro-ka-far-from", "ippou-de-one-hand", "tatoe-temo"},
    6: {"koto-nominalizer", "no-nominalizer", "ka-dou-ka"},
    7: {"ni-tsuite", "ni-totte", "ni-yotte", "ni-taishite-toward", "ni-kanshite-regarding", "ni-tsurete-as", "to-tomoni-together"},
    8: {"beki-da", "ta-hou-ga-ii", "nakucha-nakya", "ba-yokatta", "ba-hodo", "koto-da-emphatic"},
    9: {"causative-passive", "mama", "zu-ni", "nai-de-without-doing", "zuni-sumu", "pponashi-left"},
    10: {"bakari-only", "hodo-extent", "kurai-extent", "sae-even", "koso-precisely", "kagiri-as-long-as", "kiri-only", "ta-kiri-since-last", "dake-ni-precisely"},
    11: {"ippou-da-keeps", "gimi-tendency", "tsuzukeru-continue", "dashi-suddenly-start", "komi-into", "kakeru-halfway"},
    12: {"ni-kawatte-instead", "toshite-as", "ni-oite-in-at", "muke-targeted-for", "muki-suitable-for", "wo-hajime-including"},
    13: {"darake-full-of", "kiri-only", "dake-atte-as-expected", "bakari-ni-merely", "bakari-ka-not-only", "bakari-de-naku", "dake-de-naku"},
    14: {"to-iu-yori-rather", "to-ieba-speaking-of", "to-itte-mo-although", "to-itta-such-as", "nan-te-how", "nan-ka-dismissive"},
    15: {"ppoi-seems", "ge-looking", "warini-considering", "te-tamaranai-unbearably", "te-naranai-cant-help", "te-shou-ga-nai", "te-shikata-ga-nai", "koto-ni-surprise", "mono-da-general"},
    16: {"nagara", "naoshi-redo", "au-together"},
    17: {"you-ga-nai-no-way", "wake-da-meaning", "wake-dewa-nai", "nai-koto-wa-nai", "wake-ga-nai", "shou-ga-nai", "kko-nai", "hoka-nai-no-choice", "ni-kimatte-iru"},
    18: {"kurai-nara-rather", "tsuide-ni", "chuu-during", "ni-kakete-through", "okini-intervals", "gotoni-each", "igai-other-than", "kawari-ni-instead", "ni-kurabete-compared"},
    19: {"tagaru-third-person-desire", "shidai-depending", "furi-wo-suru-pretend", "dokoro-dewa-nai-no-time", "te-goran-try-casual", "te-koso-only-by", "nai-wake-ni-ikanai", "wake-ni-wa-ikanai"},
}

# Several useful patterns belong to two topics.  The vocabulary app shows each
# grammar pattern once, so these assignments below are the canonical lessons.
for _id in ("kiri-only",): GROUPS[13].discard(_id)

VI = {
"you-da-appearance":"có vẻ / dường như (dựa trên dấu hiệu)","mitai-looks-like":"trông như / có vẻ (thân mật)","rashii-seems":"hình như / nghe nói / đúng là", "te-oku":"làm trước; để nguyên trạng thái", "te-shimau":"làm xong; lỡ làm", "te-aru":"đã được làm và còn ở trạng thái đó", "te-miru":"thử làm", "te-iku":"đi / tiếp diễn xa dần", "te-kuru":"đến / thay đổi tiến gần", "nagara":"vừa… vừa…", "uchi-ni":"trong khi; trước khi trạng thái đổi", "aida-ni":"trong lúc / trong khoảng", "ta-bakari":"vừa mới", "ta-tokoro":"vừa đúng lúc; sắp; đang", "tame-ni":"vì / nhằm mục đích", "you-ni-purpose":"để / sao cho", "noni-although":"mặc dù", "okage-sei-de":"nhờ / tại vì", "bakari-only":"chỉ toàn", "kakeru-halfway":"đang dở / sắp nhưng bị gián đoạn", "hodo-extent":"đến mức; không bằng", "kurai-extent":"khoảng; đến mức", "koto-nominalizer":"việc / sự", "no-nominalizer":"việc / sự (cụ thể, cảm nhận được)", "tabi-ni-every-time":"mỗi khi", "ka-dou-ka":"có… hay không", "ni-tsuite":"về / liên quan đến", "ni-totte":"đối với / theo góc nhìn", "ni-yotte":"tùy theo; bằng; bởi", "beki-da":"nên / cần", "ta-hou-ga-ii":"nên làm", "nakucha-nakya":"phải làm (thân mật)", "ba-yokatta":"giá mà đã…; lẽ ra nên", "ba-hodo":"càng… càng…", "causative-passive":"bị bắt / bị ép làm", "mama":"vẫn nguyên / cứ để", "zu-ni":"không làm mà", "tagaru-third-person-desire":"có vẻ muốn (ngôi thứ ba)", "sae-even":"ngay cả", "koso-precisely":"chính là / chính vì", "to-tan-moment":"ngay khoảnh khắc", "shidai-depending":"tùy theo; ngay sau khi", "kagiri-as-long-as":"miễn là / trong phạm vi", "darake-full-of":"đầy / dính toàn (thường tiêu cực)", "furi-wo-suru-pretend":"giả vờ", "kuse-ni-despite":"vậy mà / mặc dù (chê trách)", "wake-da-meaning":"thảo nào; có nghĩa là", "wake-dewa-nai":"không hẳn là", "you-ga-nai-no-way":"không có cách nào", "pponashi-left":"để nguyên; liên tục không ngừng", "ni-shitemo-even":"dù cho", "to-wa-kagiranai":"không hẳn / không phải lúc nào", "nai-koto-wa-nai":"không phải là không; vẫn có thể", "irai-since":"kể từ", "ni-taishite-toward":"đối với / trái với", "ni-kanshite-regarding":"liên quan đến (trang trọng)", "ni-kawatte-instead":"thay / thay mặt", "toshite-as":"với tư cách là", "ni-oite-in-at":"tại / trong (trang trọng)", "muke-targeted-for":"dành cho", "muki-suitable-for":"phù hợp với", "ni-tsurete-as":"cùng với; càng… càng", "to-tomoni-together":"cùng với; đồng thời", "kiri-only":"chỉ có", "ta-kiri-since-last":"kể từ lần cuối… thì", "dake-ni-precisely":"chính vì… nên càng", "dake-atte-as-expected":"đúng như kỳ vọng vì", "bakari-ni-merely":"chỉ vì", "bakari-ka-not-only":"không chỉ… mà còn", "to-iu-yori-rather":"nói đúng hơn là", "to-ieba-speaking-of":"nhắc đến", "to-itte-mo-although":"tuy nói là", "to-itta-such-as":"như là / chẳng hạn", "ppoi-seems":"có vẻ; mang tính", "ge-looking":"trông có vẻ", "dokoro-ka-far-from":"đâu phải…; chứ đừng nói", "dokoro-dewa-nai-no-time":"không phải lúc để; không thể nghĩ đến", "ippou-de-one-hand":"một mặt… mặt khác", "ippou-da-keeps":"cứ ngày càng", "ue-de-upon":"sau khi; trên cơ sở", "warini-considering":"so với / xét theo thì", "te-tamaranai-unbearably":"không chịu nổi", "te-naranai-cant-help":"không sao ngừng được", "chuu-during":"đang trong / suốt", "gimi-tendency":"hơi có xu hướng", "tsuzukeru-continue":"tiếp tục", "naoshi-redo":"làm lại", "au-together":"cùng nhau", "dashi-suddenly-start":"đột nhiên bắt đầu", "komi-into":"làm sâu/kỹ; lao vào", "saichu-in-the-middle":"đúng giữa lúc", "kke-casual-wondering":"nhỉ / ấy nhỉ (nhớ lại)", "mono-reason-assertion":"vì mà (giải thích cảm xúc)", "mon-casual-because":"vì mà (thân mật)", "nai-de-without-doing":"không làm mà", "ni-chigainai-must":"chắc chắn là", "koto-da-emphatic":"nên; điều quan trọng là", "hoka-nai-no-choice":"không còn cách nào ngoài", "koto-ni-surprise":"thật là… / đáng… là", "kurai-nara-rather":"nếu đến mức… thì thà", "ni-kakete-through":"từ… đến; trải qua", "igai-other-than":"ngoài / trừ", "okini-intervals":"cách mỗi", "gotoni-each":"mỗi / cứ mỗi", "kawari-ni-instead":"thay vì", "n-da-kara-emphatic":"vì… mà (nhấn mạnh)", "wake-ga-nai":"không thể nào", "shou-ga-nai":"đành chịu; không còn cách", "te-shou-ga-nai":"không chịu nổi", "te-shikata-ga-nai":"không sao chịu được", "kko-nai":"chắc chắn không thể", "nan-te-how":"biết bao / thật là", "nan-ka-dismissive":"như…; mấy thứ như", "buri-ni-first-time":"sau… mới; … năm rồi", "nai-wake-ni-ikanai":"không thể không", "wake-ni-wa-ikanai":"không thể / không tiện", "tsuide-ni":"nhân tiện", "wo-hajime-including":"bắt đầu từ; bao gồm", "te-koso-only-by":"chỉ khi / chính nhờ", "bakari-de-naku":"không chỉ… mà còn", "dake-de-naku":"không chỉ… mà còn", "ni-kimatte-iru":"chắc chắn là", "zuni-sumu":"không cần phải", "ni-kurabete-compared":"so với", "te-hajimete-only-after":"mãi sau khi… mới", "ni-ataru-correspond":"rơi vào / tương ứng với", "tatoe-temo":"dù cho", "te-goran-try-casual":"thử… xem", "mono-da-general":"vốn là / thường là", "ki-ga-suru-feel-like":"có cảm giác là"}

# One edited Vietnamese translation for every selected source example.  Keeping
# these alongside the import makes the content reviewable and reproducible.
EXAMPLE_VI = {
"you-da-appearance":"Có vẻ như không có ai ở đây.","mitai-looks-like":"Anh ấy trông giống người Nhật.","rashii-seems":"Nghe nói anh ấy không đến.","te-oku":"Tôi đã mua bia trước cho ngày mai.","te-shimau":"Tôi đã làm xong toàn bộ bài tập.","te-aru":"Cánh cửa đã được mở và vẫn đang mở.","te-miru":"Tôi đã thử nấu một món mới.","te-iku":"Bọn trẻ chạy đầy hứng khởi đến trường.","te-kuru":"Anh ấy chạy từ ga đến đây.","nagara":"Tôi học trong khi nghe nhạc.","uchi-ni":"Hãy trải nghiệm nhiều điều khi còn trẻ.","aida-ni":"Trong lúc tôi vắng nhà, có ai đến không?","ta-bakari":"Tôi vừa mới đến Nhật.","ta-tokoro":"Tôi vừa đến ga.","tame-ni":"Tôi tập thể dục mỗi ngày vì sức khỏe.","you-ni-purpose":"Hãy nói to để mọi người nghe rõ.","noni-although":"Tôi đã học rất chăm nhưng lại trượt kỳ thi.","okage-sei-de":"Nhờ bạn mà tôi đã đỗ.","bakari-only":"Con trai tôi chỉ chơi trò chơi điện tử.","kakeru-halfway":"Có một cuốn sách đang đọc dở trên bàn.","hodo-extent":"Hôm nay tôi mệt đến chết đi được.","kurai-extent":"Đi bộ đến ga mất khoảng 20 phút.","koto-nominalizer":"Học tiếng Nhật rất vui.","no-nominalizer":"Tôi đã nhìn thấy anh ấy chạy.","tabi-ni-every-time":"Mỗi khi gặp anh ấy, tôi lại nhớ về quá khứ.","ka-dou-ka":"Tôi không biết anh ấy có đến hay không.","ni-tsuite":"Tôi đang học về văn hóa Nhật Bản.","ni-totte":"Đối với tôi, gia đình là điều quan trọng nhất.","ni-yotte":"Ý kiến khác nhau tùy từng người.","beki-da":"Học sinh nên học tập.","ta-hou-ga-ii":"Bạn nên đi ngủ sớm.","nakucha-nakya":"Tôi phải về nhà ngay thôi.","ba-yokatta":"Lẽ ra tôi nên học nhiều hơn.","ba-hodo":"Càng học tiếng Nhật càng thấy thú vị.","causative-passive":"Tôi bị mẹ bắt ăn rau.","mama":"Tôi đã ngủ quên khi vẫn bật đèn.","zu-ni":"Tôi đi học mà không ăn sáng.","tagaru-third-person-desire":"Trẻ con có vẻ thích ăn đồ ngọt.","sae-even":"Ngay cả trẻ con cũng biết.","koso-precisely":"Lần này nhất định tôi sẽ đỗ.","to-tan-moment":"Ngay khi tôi mở cửa, con mèo đã nhảy vọt ra.","shidai-depending":"Tùy kết quả, tôi sẽ thay đổi kế hoạch.","kagiri-as-long-as":"Còn sống thì còn hy vọng.","darake-full-of":"Đứa trẻ trở về nhà đầy bùn đất.","furi-wo-suru-pretend":"Tôi giả vờ ngủ.","kuse-ni-despite":"Dù chỉ là trẻ con mà nó lại nói năng như người lớn.","wake-da-meaning":"Thảo nào trời lạnh, vì đang có tuyết rơi.","wake-dewa-nai":"Không phải tôi ghét đâu, chỉ là hôm nay không muốn ăn.","you-ga-nai-no-way":"Tôi không biết số điện thoại nên không có cách liên lạc.","pponashi-left":"Tôi ra ngoài mà để đèn bật nguyên.","ni-shitemo-even":"Dù có thất bại, bạn vẫn nên thử thách.","to-wa-kagiranai":"Đồ đắt chưa chắc đã tốt.","nai-koto-wa-nai":"Không phải là không đi được, nhưng tôi không muốn đi lắm.","irai-since":"Kể từ khi đến Nhật, tôi học tiếng Nhật mỗi ngày.","ni-taishite-toward":"Không được có thái độ thất lễ với cha mẹ.","ni-kanshite-regarding":"Bạn có ý kiến gì về vấn đề này không?","ni-kawatte-instead":"Thay mặt giám đốc, tôi xin chào mọi người.","toshite-as":"Anh ấy làm việc với tư cách là bác sĩ.","ni-oite-in-at":"Tại cuộc họp, chúng tôi đã bàn về vấn đề này.","muke-targeted-for":"Tôi đã mua một cuốn sách dành cho trẻ em.","muki-suitable-for":"Công việc này phù hợp với cô ấy.","ni-tsurete-as":"Càng lớn tuổi, tôi càng thấy thời gian trôi nhanh.","to-tomoni-together":"Tôi đón năm mới cùng gia đình.","kiri-only":"Tôi muốn nói chuyện chỉ với hai người.","ta-kiri-since-last":"Anh ấy rời nhà hôm qua rồi vẫn chưa về.","dake-ni-precisely":"Vì là chuyên gia nên phần biểu diễn thật tuyệt vời.","dake-atte-as-expected":"Quả đúng là đã luyện tập 10 năm nên phần biểu diễn xuất sắc.","bakari-ni-merely":"Chỉ vì vội mà tôi quên thứ quan trọng.","bakari-ka-not-only":"Anh ấy không chỉ nói tiếng Anh mà còn nói được tiếng Pháp.","to-iu-yori-rather":"Nói là học thì đúng hơn là anh ấy đang chơi.","to-ieba-speaking-of":"Nhắc đến đồ ăn Nhật thì phải là sushi.","to-itte-mo-although":"Tuy nói là đang học tiếng Nhật nhưng tôi vẫn là người mới.","to-itta-such-as":"Ở Nhật có nhiều loại trái cây như táo và quýt.","ppoi-seems":"Anh ấy vẫn còn trẻ con.","ge-looking":"Cô ấy có vẻ mặt buồn.","dokoro-ka-far-from":"Anh ấy không chỉ không nói được tiếng Nhật mà tiếng Anh cũng không.","dokoro-dewa-nai-no-time":"Kỳ thi sắp tới nên đâu phải lúc để chơi.","ippou-de-one-hand":"Anh ấy hiền nhưng mặt khác cũng có lúc nghiêm khắc.","ippou-da-keeps":"Giá cả cứ tăng mãi.","ue-de-upon":"Hãy suy nghĩ kỹ rồi quyết định.","warini-considering":"Nhà hàng này ngon so với giá tiền.","te-tamaranai-unbearably":"Tôi đói không chịu nổi.","te-naranai-cant-help":"Tôi không sao ngừng nghĩ về anh ấy.","chuu-during":"Bây giờ tôi đang họp.","gimi-tendency":"Dạo này tôi hơi mệt.","tsuzukeru-continue":"Mưa vẫn tiếp tục rơi.","naoshi-redo":"Tôi đã viết lại báo cáo.","au-together":"Chúng ta hãy cùng bàn về vấn đề này.","dashi-suddenly-start":"Trời đột nhiên bắt đầu mưa.","komi-into":"Tôi đã nhảy xuống bể bơi.","saichu-in-the-middle":"Điện thoại reo đúng lúc đang ăn.","kke-casual-wondering":"Ngày mai bắt đầu từ mấy giờ nhỉ?","mono-reason-assertion":"Tôi không muốn đi. Vì tôi mệt mà.","mon-casual-because":"Tôi mệt mà, nên tôi đi ngủ đây.","nai-de-without-doing":"Tôi đi học mà không ăn sáng.","ni-chigainai-must":"Anh ấy chắc chắn là thủ phạm.","koto-da-emphatic":"Vì sức khỏe, nên đi ngủ sớm.","hoka-nai-no-choice":"Đã như vậy thì không còn cách nào ngoài từ bỏ.","koto-ni-surprise":"Thật đáng ngạc nhiên, anh ấy đã đỗ kỳ thi.","kurai-nara-rather":"Nếu phải xin lỗi thì thà ngay từ đầu đừng làm.","ni-kakete-through":"Từ tháng Ba đến tháng Năm, hoa anh đào nở.","igai-other-than":"Ngoài anh ấy ra, không ai biết việc đó.","okini-intervals":"Tôi đi gym cách một ngày một lần.","gotoni-each":"Mỗi năm có một kỳ thi.","kawari-ni-instead":"Tôi uống cà phê thay trà.","n-da-kara-emphatic":"Đã mệt thì hãy đi ngủ sớm.","wake-ga-nai":"Không đời nào anh ấy lại nói điều đó.","shou-ga-nai":"Trời đã mưa rồi. Đành chịu thôi.","te-shou-ga-nai":"Tôi buồn ngủ không chịu nổi.","te-shikata-ga-nai":"Tôi lo cho con không sao chịu được.","kko-nai":"Tôi chắc chắn không thể hiểu nổi bài khó như vậy.","nan-te-how":"Một bông hoa đẹp biết bao!","nan-ka-dismissive":"Người như tôi thì hoàn toàn không làm được.","buri-ni-first-time":"Mười năm rồi tôi mới về quê.","nai-wake-ni-ikanai":"Vì là đám cưới bạn nên tôi không thể không đi.","wake-ni-wa-ikanai":"Vì là cuộc họp quan trọng nên tôi không thể nghỉ.","tsuide-ni":"Nhân tiện đi mua sắm, tôi đã gửi thư.","wo-hajime-including":"Bắt đầu từ giám đốc, toàn bộ nhân viên đều tham dự.","te-koso-only-by":"Chỉ khi nỗ lực mới có thể thành công.","bakari-de-naku":"Anh ấy không chỉ học giỏi mà còn giỏi thể thao.","dake-de-naku":"Cuốn sách này không chỉ hay mà còn giúp học được nhiều điều.","ni-kimatte-iru":"Cái đó chắc chắn là nói dối.","zuni-sumu":"Nhờ được giúp đỡ, tôi không phải thức trắng đêm.","ni-kurabete-compared":"So với năm ngoái, năm nay ấm hơn.","te-hajimete-only-after":"Mãi sau khi đến Nhật, tôi mới hiểu văn hóa Nhật.","ni-ataru-correspond":"Hôm nay đúng vào sinh nhật bố tôi.","tatoe-temo":"Dù trời mưa tôi vẫn đi.","te-goran-try-casual":"Thử đọc cuốn sách này xem, thú vị lắm.","mono-da-general":"Trẻ con vốn là hiếu động.","ki-ga-suru-feel-like":"Tôi có cảm giác trời sắp mưa."}


def vi_formula(value: str) -> str:
    replacements = [
        ("い-adj", "Aい"), ("な-adj", "Aな"),
        ("Verb plain non-past", "Vる"), ("V plain non-past", "Vる"),
        ("Verb (dictionary form)", "Vる"), ("Verb plain form", "Vる"),
        ("V plain", "Vる"), ("Plain form", "TTT"),
        ("Verb ます-stem", "Gốc Vます"), ("V ます-stem", "Gốc Vます"),
        ("Vます-stem", "Gốc Vます"), ("Verb stem", "Gốc Vます"),
        ("V negative stem", "Vない (bỏ い)"), ("V-ない stem", "Vない (bỏ い)"),
        ("Verb-て form", "Vて"), ("V-て form", "Vて"),
        ("Verb-た form", "Vた"), ("V-た form", "Vた"),
        ("Verb-ない form", "Vない"), ("V ない-form", "Vない"),
        ("V 〜ている", "Vている"),
        ("i-adj stem", "Aい (bỏ い)"), ("i-adj root", "Aい (bỏ い)"),
        ("na-adj stem", "Aな"), ("na-adj root", "Aな"),
        ("i-adj", "Aい"), ("na-adj", "Aな"),
        ("Noun", "N"), ("noun", "N"),
    ]
    for old, new in replacements:
        value = value.replace(old, new)
    value = re.sub(r"\bVerb\b", "V", value, flags=re.I)
    value = value.replace("V-て", "Vて").replace("V-た", "Vた").replace("V-ない", "Vない")
    value = value.replace("V ない-thể", "Vない").replace("V-ば thể", "V (thể ば)")
    value = value.replace("V dictionary form", "Vる").replace("V dictionary", "Vる")
    value = value.replace("N-の", "N + の").replace("N の", "N + の")
    value = value.replace("Plain-form clause", "Câu (TTT)").replace("plain form", "TTT")
    value = value.replace("plain", "TTT").replace("V → causative-passive form", "V (thể sai khiến bị động)")
    words = {
        "potential": "khả năng", "intransitive": "nội động từ", "transitive": "ngoại động từ",
        "causative-passive": "sai khiến bị động", "demonstrative": "từ chỉ định",
        "Time period": "Khoảng thời gian", "Number": "Số", "counter": "lượng từ",
        "Phrase": "Cụm câu", "standalone": "đứng độc lập", "root": "gốc",
        "negative": "phủ định", "positive": "tích cực", "extreme statement": "câu nhấn mạnh",
        "continuation": "tiếp diễn", "dictionary": "từ điển", "also": "cũng",
        "stem": "gốc", "or": "hoặc", "and": "và", "adj": "Aい / Aな",
        "form": "thể",
    }
    for old, new in words.items():
        value = re.sub(rf"\b{re.escape(old)}\b", new, value, flags=re.I)
    value = value.replace("V từ điển", "Vる").replace("Vます", "Gốc Vます")
    value = value.replace("Gốc Gốc Vます", "Gốc Vます")
    value = value.replace("gốc Vない", "Vない (bỏ い)")
    value = value.replace("い-Aい / Aな", "Aい").replace("な-Aい / Aな", "Aな")
    value = value.replace("Vて thể", "Vて").replace("Vた thể", "Vた")
    value = value.replace("V-ば thể", "V (thể ば)").replace("V ば-thể", "V (thể ば)")
    value = value.replace("Vない gốc", "Vない (bỏ い)").replace("V phủ định gốc", "Vない (bỏ い)")
    value = value.replace("V ない-thể", "Vない").replace("V gốc", "Gốc Vます")
    value = value.replace("V TTT", "V (TTT)")
    value = value.replace("V thể + ところ", "Vる / Vている / Vた + ところ")
    value = value.replace("ngoại động từ Vて + ある", "Vて (ngoại động từ) + ある")
    value = value.replace("ngoại động từ Vて thể + ある", "Vて (ngoại động từ) + ある")
    value = value.replace("Vる (khả năng / nội động từ / ない-thể) + ように", "Vる (khả năng / nội động từ) / Vない + ように")
    value = value.replace("N / V (〜て thể / TTT) + ばかり", "N / Vて / V (TTT) + ばかり")
    value = value.replace("N / V (TTT) + ほど; cũng A は B ほど [Aい / Aな]-ない", "N / V (TTT) + ほど; N1 + は + N2 + ほど + Aい / Aな + ない")
    value = value.replace("Vない (bỏ い) + ずに", "Vない (bỏ ない) + ずに")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    entries = json.loads(args.source.read_text(encoding="utf-8"))
    source_ids = {entry["id"] for entry in entries}
    assigned = set().union(*GROUPS.values())
    if source_ids != assigned:
        raise ValueError(f"N3 mapping differs from source. Missing={sorted(source_ids-assigned)} extra={sorted(assigned-source_ids)}")
    missing_vi = source_ids - VI.keys()
    if missing_vi:
        raise ValueError(f"Missing Vietnamese explanation: {sorted(missing_vi)}")
    missing_examples = source_ids - EXAMPLE_VI.keys()
    if missing_examples:
        raise ValueError(f"Missing Vietnamese example translation: {sorted(missing_examples)}")
    lesson_for_id = {identifier: number for number, identifiers in GROUPS.items() for identifier in identifiers}
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("DELETE FROM grammar_lessons WHERE level='N3'")
        for order, (title, description) in enumerate(LESSONS, 1):
            db.execute("INSERT INTO grammar_lessons(level,title,description,order_index) VALUES ('N3',?,?,?)", (title, description, order))
        lesson_ids = {order: row_id for row_id, order in db.execute("SELECT id,order_index FROM grammar_lessons WHERE level='N3'")}
        for entry in entries:
            # Source formation notes are English.  Do not surface them as a
            # half-translated note; the formula plus this Vietnamese guidance
            # is clearer until a later editorial pass adds long-form notes.
            note = f"Mẫu này thường dùng với nghĩa “{VI[entry['id']]}”. Chú ý sắc thái và mức độ lịch sự trong câu ví dụ."
            cursor = db.execute("INSERT INTO grammar_patterns(lesson_id,formula,explanation_vi,note) VALUES (?,?,?,?)", (lesson_ids[lesson_for_id[entry['id']]], vi_formula(entry['pattern']), VI[entry['id']], note))
            example = (entry.get("examples") or [None])[0]
            if example:
                db.execute("INSERT INTO grammar_examples(pattern_id,japanese,reading,meaning_vi) VALUES (?,?,?,?)", (cursor.lastrowid, example['japanese'], '', EXAMPLE_VI[entry['id']]))
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n3_grammar_seed_version','n3-full-japanese-language-data-vi-v1')")
    print(f"Imported {len(entries)} N3 patterns into {len(LESSONS)} lessons.")


if __name__ == "__main__":
    main()
