"""Import the complete curated JLPT N4 grammar set in Vietnamese.

Source: Japanese Language Data, grammar-curated/n4.json (CC BY-SA 4.0).
The source's English explanations are used as the factual reference; the
learner-facing meanings and notes below are Vietnamese editorial translations.
"""
import argparse
import json
import re
import sqlite3
from pathlib import Path

from database import DB_PATH

LESSONS = [
    "Nhấn mạnh và nhờ vả lịch sự", "Khả năng và giới hạn", "Động từ chỉ lý do",
    "Trạng thái và hoàn thành", "So sánh và kết quả", "Dự định và kế hoạch",
    "Khuyên bảo và phỏng đoán", "Mệnh lệnh và nghĩa vụ", "Theo như và sau khi",
    "Điều kiện ば và なら", "Mục đích và biến đổi", "Bị động", "Nhóm động từ",
    "Nguyên nhân", "Câu hỏi tổng và thử làm", "Kính ngữ cho cấp trên",
    "Vì mục đích và sử dụng vào", "Trông có vẻ và rủi ro", "Quá mức và dễ/khó",
    "Trường hợp và nghịch lý", "Sắp/đang/vừa xong và vừa mới", "Nghe nói và hình như",
    "Sai khiến", "Kính ngữ", "Khiêm nhường ngữ",
]

# Each item is an editorial Vietnamese rendering of the corresponding JLD
# English meaning.  Keep IDs stable so a source update is easy to review.
VI = {
 "potential-form":"có thể làm / có khả năng làm", "passive-form":"bị làm; cũng diễn tả việc bị ảnh hưởng ngoài ý muốn", "causative-form":"bắt hoặc cho phép ai làm", "ta-koto-ga-aru":"đã từng làm (kinh nghiệm)", "tsumori-intention":"dự định / có ý định làm", "to-omou":"tôi nghĩ rằng", "to-iu":"nói rằng; được gọi là", "darou-deshou-conjecture":"chắc là / có lẽ", "kamoshirenai-might":"có thể / biết đâu", "hazu-expected":"lẽ ra / chắc hẳn", "tara-conditional":"nếu / khi", "ba-conditional":"nếu (điều kiện giả định)", "to-conditional":"hễ / cứ ... thì (kết quả tự nhiên)", "nara-conditional":"nếu là trường hợp đó; còn về", "volitional-form":"hãy cùng làm / tôi sẽ làm", "te-wa-ikenai-prohibition":"không được làm", "te-mo-ii-permission":"được phép làm", "nakereba-naranai":"phải / cần làm", "nakute-mo-ii":"không cần làm", "node-cause":"vì / do (cách nói mềm và khách quan)", "ga-kedo-although":"nhưng / mặc dù", "n-desu-explanation":"giải thích, nêu lý do hoặc nhấn nhẹ", "ni-naru-become":"trở thành", "ni-suru-decide":"chọn / quyết định là", "hajimeru-auxiliary":"bắt đầu làm", "owaru-finish":"làm xong", "sugiru-too-much":"quá / làm quá mức", "yasui-easy":"dễ làm", "nikui-hard":"khó làm", "noun-modifying-clause":"mệnh đề bổ nghĩa cho danh từ", "tari-tari-suru":"làm những việc như A, B", "jidoushi-tadoushi":"cặp nội động từ và ngoại động từ", "garu-third-person-emotion":"có vẻ muốn / có dấu hiệu cảm thấy (ngôi ba)", "kata-way-of-doing":"cách làm", "you-ni-suru":"cố gắng tạo thói quen / làm sao để", "te-kara-after-doing":"sau khi làm A thì làm B", "mae-ni-before-doing":"trước khi làm A", "ato-de-after-doing":"sau khi làm A", "koto-ga-dekiru":"có thể làm", "koto-ni-suru-decide":"tự quyết định làm / không làm", "koto-ni-naru-be-decided":"được quyết định là / trở thành quyết định", "nasai-command":"hãy làm (mệnh lệnh nhẹ)", "te-hoshii-want-someone":"muốn ai đó làm", "shi-reason-listing":"và; hơn nữa (liệt kê lý do/sự việc)", "you-to-omou-volitional-intent":"nghĩ là sẽ làm / dự định làm", "te-kureru-favor-received":"ai đó làm giúp tôi/nhóm của tôi", "te-morau-request-favor":"nhận sự giúp đỡ; nhờ ai làm", "te-ageru-favor-given":"làm giúp người ngoài nhóm của mình", "ageru-give-outward":"cho (từ phía mình ra bên ngoài)", "kureru-give-toward":"cho tôi / người thuộc nhóm của tôi", "morau-receive":"nhận", "o-v-kudasai-polite-honor":"xin vui lòng làm (lịch sự cao)", "sonkeigo-reru-rareru":"kính ngữ bằng thể bị động", "humble-o-suru":"khiêm nhường ngữ: tôi sẽ làm", "sou-iu-kou-iu":"loại như thế này / thế đó / thế kia", "tai-to-omou-want-to-think":"tôi nghĩ là muốn làm", "ba-ai-in-case":"trong trường hợp / nếu", "zutsu-each-per":"mỗi / theo từng", "tsumori-datta-had-intended":"đã định / vốn định", "hazu-datta-was-supposed":"lẽ ra đã / đáng lẽ", "demo-noun-even":"ngay cả; hay là ... gì đó", "te-itadaku-polite-favor-received":"khiêm nhường: được ai làm giúp", "ba-ii-should":"nên / chỉ cần làm", "yaru-casual-giving":"cho (thân mật, với người dưới/thú cưng/cây)", "v-temo-even-if":"dù cho / ngay cả khi", "irassharu-honorific":"kính ngữ của đi, đến, ở", "ossharu-honorific":"kính ngữ của nói", "goran-ni-naru-honorific":"kính ngữ của xem", "nasaru-honorific":"kính ngữ của làm", "mairu-humble":"khiêm nhường ngữ của đi, đến", "mousu-humble":"khiêm nhường ngữ của nói / tên là", "itadaku-humble-verb":"khiêm nhường ngữ của nhận, ăn, uống", "kudasaru-honorific-verb":"kính ngữ: người trên cho tôi/chúng tôi", "shika-nai":"chỉ có (đi với phủ định)", "ga-suki-kirai":"thích / ghét (dùng trợ từ が)", "ga-wakaru":"hiểu (dùng trợ từ が)", "ga-dekiru":"có thể / làm được (dùng trợ từ が)", "ga-kikoeru-mieru":"nghe thấy / nhìn thấy một cách tự nhiên", "dakara-so":"vì thế / do đó", "sorede-and-then":"vì vậy / rồi thì", "sorekara-after":"sau đó / hơn nữa", "shikashi-but":"nhưng / tuy nhiên (trang trọng)", "kedomo-formal-but":"nhưng / tuy nhiên", "toka-listing":"như là A, B (liệt kê không hết)", "tte-quotation":"rằng / người ta nói là (thân mật)", "soredemo-even-so":"dù vậy / tuy thế", "sou-da-appearance":"trông có vẻ / có vẻ như", "sou-da-hearsay":"nghe nói / có tin rằng", "you-ka-to-omou":"đang cân nhắc làm",
}

FORMULAS = {
 "potential-form":"V (thể khả năng)", "passive-form":"V (thể bị động)",
 "causative-form":"V (thể sai khiến)", "ta-koto-ga-aru":"Vた + ことがある",
 "tsumori-intention":"Vる + つもり", "to-omou":"TTT + と思う",
 "to-iu":"Cụm trích dẫn + と言う", "darou-deshou-conjecture":"TTT + だろう / でしょう",
 "kamoshirenai-might":"TTT + かもしれない", "hazu-expected":"TTT + はず",
 "tara-conditional":"Vた + ら", "ba-conditional":"V (thể ば)",
 "to-conditional":"Vる + と", "nara-conditional":"N / TTT + なら",
 "volitional-form":"V (thể ý chí)", "te-wa-ikenai-prohibition":"Vて + はいけない / はいけません",
 "te-mo-ii-permission":"Vて + もいい / もいいです",
 "nakereba-naranai":"Vない (bỏ い) + ければならない",
 "nakute-mo-ii":"Vない (đổi ない thành なく) + てもいい",
 "node-cause":"TTT + ので", "ga-kedo-although":"Câu + が / けど / けれども",
 "n-desu-explanation":"TTT + んです / のです", "ni-naru-become":"N / Aな + に + なる",
 "ni-suru-decide":"N / Aな + に + する", "hajimeru-auxiliary":"Gốc Vます + 始める",
 "owaru-finish":"Gốc Vます + 終わる",
 "sugiru-too-much":"Gốc Vます / Aい (bỏ い) / Aな + すぎる",
 "yasui-easy":"Gốc Vます + やすい", "nikui-hard":"Gốc Vます + にくい",
 "noun-modifying-clause":"Câu (TTT) + N", "tari-tari-suru":"Vた + り + Vた + り + する",
 "jidoushi-tadoushi":"V (ngoại động từ) ↔ V (nội động từ)",
 "garu-third-person-emotion":"Aい (bỏ い) / 〜たい (bỏ い) + がる",
 "kata-way-of-doing":"Gốc Vます + 方", "you-ni-suru":"Vる + ようにする / ようにしている",
 "te-kara-after-doing":"Vて + から", "mae-ni-before-doing":"Vる / N + の + 前に",
 "ato-de-after-doing":"Vた / N + の + 後で", "koto-ga-dekiru":"Vる + ことができる",
 "koto-ni-suru-decide":"Vる / Vない + ことにする",
 "koto-ni-naru-be-decided":"Vる / Vない + ことになる",
 "nasai-command":"Gốc Vます + なさい", "te-hoshii-want-someone":"Vて + ほしい",
 "shi-reason-listing":"TTT + し (+ TTT + し + …)",
 "you-to-omou-volitional-intent":"V (thể ý chí) + と思う",
 "te-kureru-favor-received":"Vて + くれる", "te-morau-request-favor":"Vて + もらう",
 "te-ageru-favor-given":"Vて + あげる",
 "ageru-give-outward":"N (người cho) + が + N (người nhận) + に + N (vật) + を + あげる",
 "kureru-give-toward":"N (người cho) + が + N (người nhận) + に + N (vật) + を + くれる",
 "morau-receive":"N (người nhận) + が + N (người cho) + に / から + N (vật) + を + もらう",
 "o-v-kudasai-polite-honor":"お + Gốc Vます + ください / ご + N (Hán-Nhật) + ください",
 "sonkeigo-reru-rareru":"V (thể bị động dùng làm kính ngữ)",
 "humble-o-suru":"お + Gốc Vます + する / ご + N (Hán-Nhật) + する",
 "sou-iu-kou-iu":"こういう / そういう / ああいう / どういう + N",
 "tai-to-omou-want-to-think":"Gốc Vます + たいと思う",
 "ba-ai-in-case":"V (TTT) / Aい / Aな + な / N + の + 場合(は)",
 "zutsu-each-per":"Số + lượng từ + ずつ", "tsumori-datta-had-intended":"Vる + つもりだった",
 "hazu-datta-was-supposed":"V (TTT) / Aい / Aな + な / N + の + はずだった",
 "demo-noun-even":"N + でも", "te-itadaku-polite-favor-received":"Vて + いただく",
 "ba-ii-should":"V (thể ば) + いい",
 "yaru-casual-giving":"N (người cho) + が + N (người nhận) + に + N (vật) + を + やる",
 "v-temo-even-if":"Vて + も", "irassharu-honorific":"いらっしゃる（行く / 来る / いるの kính ngữ）",
 "ossharu-honorific":"おっしゃる（言うの kính ngữ）",
 "goran-ni-naru-honorific":"ご覧になる（見るの kính ngữ）",
 "nasaru-honorific":"なさる（するの kính ngữ）",
 "mairu-humble":"参る（行く / 来るの khiêm nhường ngữ）",
 "mousu-humble":"申す（言うの khiêm nhường ngữ）",
 "itadaku-humble-verb":"いただく（もらう / 食べる / 飲むの khiêm nhường ngữ）",
 "kudasaru-honorific-verb":"くださる（くれるの kính ngữ）",
 "shika-nai":"N / V (TTT) + しか + vị ngữ phủ định", "ga-suki-kirai":"N + が + 好き / 嫌い",
 "ga-wakaru":"N + が + わかる", "ga-dekiru":"N + が + できる",
 "ga-kikoeru-mieru":"N + が + 聞こえる / 見える", "dakara-so":"だから（đầu câu）",
 "sorede-and-then":"それで（đầu câu）", "sorekara-after":"それから（đầu câu）",
 "shikashi-but":"しかし（đầu câu）", "kedomo-formal-but":"けれども（giữa câu / đầu câu）",
 "toka-listing":"N1 + とか + N2 + (とか)", "tte-quotation":"TTT / cụm trích dẫn + って",
 "soredemo-even-so":"それでも（đầu câu）",
 "sou-da-appearance":"Gốc Vます / Aい (bỏ い) / Aな + そう(だ / です)",
 "sou-da-hearsay":"TTT + そう(だ / です)", "you-ka-to-omou":"V (thể ý chí) + かと思う",
}

# One natural Vietnamese rendering for the first curated example of every N4
# pattern.  This prevents the learner-facing screen from showing a generic
# placeholder instead of the meaning of the Japanese sentence.
EXAMPLE_VI = {
"potential-form":"Tôi có thể nói tiếng Nhật.","passive-form":"Tôi được giáo viên khen.","causative-form":"Giáo viên bắt học sinh đọc sách.","ta-koto-ga-aru":"Tôi đã từng đi Nhật.","tsumori-intention":"Năm sau tôi định đi Nhật.","to-omou":"Tôi nghĩ ngày mai trời sẽ mưa.","to-iu":"Anh ấy nói ngày mai sẽ đến.","darou-deshou-conjecture":"Ngày mai có lẽ trời sẽ nắng.","kamoshirenai-might":"Ngày mai có thể trời mưa.","hazu-expected":"Anh ấy lẽ ra sẽ đến hôm nay.","tara-conditional":"Nếu có thời gian, tôi sẽ xem phim.","ba-conditional":"Nếu học mỗi ngày, bạn sẽ giỏi lên.","to-conditional":"Hễ nhấn nút này thì cửa mở.","nara-conditional":"Nếu đi Nhật thì tôi khuyên bạn đến Kyoto.","volitional-form":"Cùng đi nào.","te-wa-ikenai-prohibition":"Không được hút thuốc ở đây.","te-mo-ii-permission":"Tôi ngồi đây được không?","nakereba-naranai":"Ngày mai tôi phải dậy sớm.","nakute-mo-ii":"Ngày mai bạn không cần đến trường.","node-cause":"Vì trời đang mưa nên chúng ta hủy.","ga-kedo-although":"Cuốn sách này khó nhưng thú vị.","n-desu-explanation":"Thật ra tôi bị đau đầu.","ni-naru-become":"Con trai tôi đã trở thành bác sĩ.","ni-suru-decide":"Tôi chọn cà phê.","hajimeru-auxiliary":"Năm ngoái tôi bắt đầu học tiếng Nhật.","owaru-finish":"Tôi đã đọc xong cuốn sách.","sugiru-too-much":"Tôi đã ăn quá nhiều.","yasui-easy":"Cây bút này dễ viết.","nikui-hard":"Chữ này khó đọc.","noun-modifying-clause":"Chiếc bánh ông Tanaka làm hôm qua rất ngon.","tari-tari-suru":"Cuối tuần tôi làm những việc như xem phim và đi mua sắm.","jidoushi-tadoushi":"Tôi đã mở cửa.","garu-third-person-emotion":"Em trai tôi ngay cả mùa hè cũng thấy lạnh.","kata-way-of-doing":"Hãy dạy tôi cách viết chữ Kanji này.","you-ni-suru":"Tôi cố gắng tập thể dục mỗi ngày.","te-kara-after-doing":"Tôi sẽ ra ngoài sau khi ăn cơm.","mae-ni-before-doing":"Trước khi ngủ, tôi đánh răng.","ato-de-after-doing":"Sau khi ăn cơm, tôi đi dạo.","koto-ga-dekiru":"Tôi có thể nói tiếng Nhật.","koto-ni-suru-decide":"Từ ngày mai tôi quyết định tập thể dục mỗi ngày.","koto-ni-naru-be-decided":"Tôi đã được quyết định chuyển công tác đến Tokyo vào tháng sau.","nasai-command":"Hãy dậy nhanh lên.","te-hoshii-want-someone":"Tôi muốn bạn nghe câu chuyện của tôi.","shi-reason-listing":"Phòng này rộng lại yên tĩnh.","you-to-omou-volitional-intent":"Tôi nghĩ ngày mai sẽ dậy sớm.","te-kureru-favor-received":"Bạn tôi đã cho tôi mượn tiền.","te-morau-request-favor":"Tôi đã nhờ bạn dạy tiếng Nhật cho mình.","te-ageru-favor-given":"Tôi đã cho bạn mượn sách.","ageru-give-outward":"Tôi đã tặng quà cho bạn.","kureru-give-toward":"Bạn tôi đã tặng tôi một cuốn sách.","morau-receive":"Tôi đã nhận quà từ bạn.","o-v-kudasai-polite-honor":"Xin hãy đợi.","sonkeigo-reru-rareru":"Giám đốc đã đến cuộc họp.","humble-o-suru":"Tôi sẽ cho thầy mượn sách.","sou-iu-kou-iu":"Tôi thích loại sách như thế này.","tai-to-omou-want-to-think":"Tôi nghĩ mình muốn đi Nhật.","ba-ai-in-case":"Trong trường hợp cháy, hãy nhấn nút này.","zutsu-each-per":"Mỗi người hãy lấy một cái.","tsumori-datta-had-intended":"Hôm qua tôi định học nhưng mệt quá nên đã ngủ.","hazu-datta-was-supposed":"Anh ấy lẽ ra phải đến hôm nay.","demo-noun-even":"Ngay cả trẻ con cũng hiểu.","te-itadaku-polite-favor-received":"Tôi đã được thầy vui lòng giải thích cho.","ba-ii-should":"Nếu không hiểu thì chỉ cần hỏi.","yaru-casual-giving":"Mỗi sáng tôi tưới nước cho hoa.","v-temo-even-if":"Dù trời mưa tôi vẫn đi.","irassharu-honorific":"Thầy hiện đang ở trường.","ossharu-honorific":"Thầy đã nói gì ạ?","goran-ni-naru-honorific":"Xin hãy xem tài liệu này.","nasaru-honorific":"Giám đốc tập thể dục mỗi sáng.","mairu-humble":"Tôi sẽ đến ngay.","mousu-humble":"Tôi tên là Tanaka.","itadaku-humble-verb":"Xin phép được dùng bữa.","kudasaru-honorific-verb":"Thầy đã vui lòng cho tôi cuốn sách.","shika-nai":"Tôi chỉ có 100 yên.","ga-suki-kirai":"Tôi thích mèo.","ga-wakaru":"Tôi hiểu tiếng Nhật.","ga-dekiru":"Bạn biết tiếng Nhật không?","ga-kikoeru-mieru":"Từ xa tôi nghe thấy tiếng nhạc.","dakara-so":"Trời đang mưa. Vì vậy tôi sẽ mang ô.","sorede-and-then":"Tàu bị trễ. Vì vậy tôi đến muộn cuộc họp.","sorekara-after":"Tôi ăn sáng. Sau đó tôi đi học.","shikashi-but":"Trời mưa. Tuy nhiên trận đấu vẫn diễn ra.","kedomo-formal-but":"Dù trời mưa nhưng trận đấu vẫn diễn ra.","toka-listing":"Tôi thích những thứ như thể thao và âm nhạc.","tte-quotation":"Anh ấy bảo rằng ngày mai sẽ đến.","soredemo-even-so":"Tôi mệt. Dù vậy tôi vẫn phải tiếp tục.","sou-da-appearance":"Trông có vẻ trời sắp mưa.","sou-da-hearsay":"Theo dự báo thời tiết, nghe nói ngày mai sẽ mưa.","you-ka-to-omou":"Tôi đang cân nhắc đi du học."}

GROUPS = {
    1: {"n-desu-explanation", "te-itadaku-polite-favor-received", "o-v-kudasai-polite-honor"},
    2: {"potential-form", "koto-ga-dekiru", "ga-dekiru", "ga-kikoeru-mieru", "ga-suki-kirai", "ga-wakaru"},
    3: {"shi-reason-listing", "garu-third-person-emotion", "te-kara-after-doing"},
    4: {"jidoushi-tadoushi", "ni-naru-become", "owaru-finish"},
    5: {"darou-deshou-conjecture", "kamoshirenai-might", "hazu-expected"},
    6: {"tsumori-intention", "volitional-form", "you-to-omou-volitional-intent", "koto-ni-suru-decide", "koto-ni-naru-be-decided", "ni-suru-decide"},
    7: {"tara-conditional", "ba-ii-should", "te-mo-ii-permission", "nakute-mo-ii"},
    8: {"nasai-command", "te-wa-ikenai-prohibition", "te-hoshii-want-someone", "nakereba-naranai"},
    9: {"mae-ni-before-doing", "ato-de-after-doing", "tari-tari-suru"},
    10: {"ba-conditional", "nara-conditional", "v-temo-even-if", "ba-ai-in-case", "to-conditional"},
    11: {"you-ni-suru", "you-ka-to-omou"},
    12: {"passive-form"},
    13: {"noun-modifying-clause", "kata-way-of-doing", "sou-iu-kou-iu"},
    14: {"node-cause", "ga-kedo-although", "dakara-so", "sorede-and-then", "sorekara-after", "shikashi-but", "kedomo-formal-but"},
    15: {"tte-quotation", "toka-listing", "to-omou", "to-iu"},
    16: {"sonkeigo-reru-rareru", "irassharu-honorific", "ossharu-honorific", "goran-ni-naru-honorific", "nasaru-honorific", "kudasaru-honorific-verb"},
    17: {"tai-to-omou-want-to-think", "tsumori-datta-had-intended", "ta-koto-ga-aru", "te-morau-request-favor"},
    18: {"sou-da-appearance", "soredemo-even-so", "hazu-datta-was-supposed"},
    19: {"sugiru-too-much", "yasui-easy", "nikui-hard"},
    20: {"demo-noun-even", "shika-nai"},
    21: {"hajimeru-auxiliary", "te-kureru-favor-received", "zutsu-each-per"},
    22: {"sou-da-hearsay"},
    23: {"causative-form"},
    24: {"te-ageru-favor-given", "ageru-give-outward", "kureru-give-toward", "morau-receive", "yaru-casual-giving"},
    25: {"humble-o-suru", "mairu-humble", "mousu-humble", "itadaku-humble-verb"},
}
LESSON_FOR_ID = {pattern_id: order for order, pattern_ids in GROUPS.items() for pattern_id in pattern_ids}

def vietnamese_formula(formula: str) -> str:
    replacements = [("Plain form", "TTT"), ("V plain non-past", "V thể từ điển"), ("V plain", "V thể từ điển"), ("V-て form", "Vて"), ("V-た form", "Vた"), ("V ない", "Vない"), ("Verb ます-stem", "Vます"), ("Verb stem", "Vます"), ("Verb (dictionary form)", "V thể từ điển"), ("dictionary form", "thể từ điển"), ("Verb", "V"), ("Noun", "N"), ("Quoted phrase", "Cụm được trích dẫn"), ("Clause", "Mệnh đề"), ("Number", "Số"), ("counter", "trợ số"), ("form", "thể")]
    for source, target in replacements:
        formula = formula.replace(source, target)
    formula = formula.replace("V ます-stem", "Vます").replace("V-stem", "Vます").replace("V-ない stem", "gốc Vない")
    formula = formula.replace("V plain non-past", "V thể từ điển").replace("plain thể", "TTT")
    formula = formula.replace("Plain-thể clause", "Mệnh đề TTT").replace("i-adj", "Aい").replace("na-adj", "Aな")
    formula = formula.replace("Aい stem", "gốc Aい").replace("Aな stem", "gốc Aな").replace("〜たい stem", "gốc 〜たい")
    formula = formula.replace("adj stem", "gốc tính từ").replace("adj root", "gốc tính từ")
    formula = formula.replace("mid-sentence", "giữa câu").replace("sentence-initial", "đầu câu")
    formula = formula.replace(" verb", " V").replace(" pairs", " theo cặp")
    for source, target in {"passive":"bị động", "causative":"sai khiến", "potential":"khả năng", "honorific":"kính ngữ", "humble":"khiêm nhường", "Sino-Japanese":"Hán-Nhật", "intransitive":"nội động từ", "transitive":"ngoại động từ", "phrase":"cụm từ", "noun":"N", "or":"hoặc", "of":"của", "vs":"so với"}.items():
        formula = re.sub(rf"\b{source}\b", target, formula, flags=re.I)
    return formula

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    entries = json.loads(args.source.read_text(encoding="utf-8"))
    source_ids = {entry["id"] for entry in entries}
    if source_ids != set(VI) or source_ids != set(LESSON_FOR_ID) or source_ids != set(FORMULAS):
        missing = source_ids - set(LESSON_FOR_ID)
        extra = set(LESSON_FOR_ID) - source_ids
        raise ValueError(f"Phân bài N4 chưa khớp nguồn. Thiếu: {sorted(missing)}. Thừa: {sorted(extra)}")
    if source_ids != set(EXAMPLE_VI):
        raise ValueError("Thiếu bản dịch ví dụ N4; dừng import để không tạo nội dung chung chung.")
    with sqlite3.connect(DB_PATH) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("DELETE FROM grammar_lessons WHERE level='N4'")
        for order, title in enumerate(LESSONS, start=1):
            db.execute("INSERT INTO grammar_lessons(level,title,description,order_index) VALUES ('N4',?,?,?)", (title, f"Bài {order + 25}: {title}." ,order))
        lessons = {order: ident for ident, order in db.execute("SELECT id,order_index FROM grammar_lessons WHERE level='N4'")}
        for entry in entries:
            meaning = VI[entry["id"]]
            note = f"Cách dùng: {meaning}. Hãy đối chiếu cấu trúc và các câu ví dụ bên dưới."
            cursor = db.execute("INSERT INTO grammar_patterns(lesson_id,formula,explanation_vi,note) VALUES (?,?,?,?)", (lessons[LESSON_FOR_ID[entry["id"]]], FORMULAS[entry["id"]], meaning, note))
            pattern_id = cursor.lastrowid
            for example in entry.get("examples", [])[:1]:
                db.execute("INSERT INTO grammar_examples(pattern_id,japanese,reading,meaning_vi) VALUES (?,?,?,?)", (pattern_id, example["japanese"], "", EXAMPLE_VI[entry["id"]]))
        db.execute("INSERT OR REPLACE INTO app_settings(key,value) VALUES ('n4_grammar_seed_version','n4-full-japanese-language-data-vi-v1')")
    print(f"Imported {len(entries)} N4 patterns into {len(LESSONS)} lessons.")

if __name__ == "__main__":
    main()
