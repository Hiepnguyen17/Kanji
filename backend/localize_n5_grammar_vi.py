"""Apply KanjiAI-authored Vietnamese labels to the 77 imported N5 patterns."""
import argparse
import json
import sqlite3
from pathlib import Path

from database import DB_PATH

MEANINGS = [
    "Là/ở (dạng lịch sự).", "Là/ở (dạng thông thường).", "Đã là/đã ở (dạng lịch sự).", "Không phải/không là (dạng lịch sự).",
    "Đuôi động từ lịch sự ở hiện tại hoặc tương lai.", "Đuôi động từ lịch sự ở quá khứ.", "Phủ định lịch sự ở hiện tại hoặc tương lai.", "Phủ định lịch sự ở quá khứ.",
    "Đánh dấu chủ đề của câu; đọc là wa.", "Đánh dấu chủ ngữ và thường đưa thông tin mới.", "Đánh dấu đối tượng trực tiếp của động từ.", "Chỉ đích đến, nơi tồn tại, thời điểm hoặc đối tượng nhận tác động.",
    "Chỉ phương tiện, công cụ hoặc nơi diễn ra hành động.", "Nối danh từ theo nghĩa và/cùng với.", "Chỉ sở hữu hoặc dùng danh từ này bổ nghĩa cho danh từ kia.", "Chỉ hướng di chuyển; đọc là e.",
    "Chỉ điểm bắt đầu: từ nơi chốn hoặc thời gian.", "Chỉ điểm kết thúc: đến, cho tới.", "Cũng, cũng là.", "Biến câu thành câu hỏi.",
    "Nhỉ/đúng không; tìm sự đồng tình hoặc xác nhận hiểu biết chung.", "Nhấn mạnh hoặc báo cho người nghe thông tin mới.", "Đây/đó/đằng kia/cái nào; đại từ chỉ đồ vật.", "Này/đó/kia/nào + danh từ; từ chỉ định đứng trước danh từ.",
    "Ở đây/ở đó/đằng kia/ở đâu; từ chỉ địa điểm.", "Có/tồn tại đối với vật vô tri.", "Có/tồn tại đối với người và động vật.", "Thể nối て, nền tảng của nhiều cấu trúc ghép.",
    "Hãy làm...; lời yêu cầu lịch sự.", "Đang làm... hoặc ở trạng thái đã làm xong.", "Thể phủ định thông thường của động từ.", "Thể quá khứ thông thường của động từ.",
    "Tính từ い ở hiện tại, dạng khẳng định.", "Phủ định tính từ い: không...", "Quá khứ tính từ い: đã...", "Tính từ な ở hiện tại.",
    "Tính từ な bổ nghĩa trực tiếp cho danh từ.", "Phủ định tính từ な.", "Quá khứ tính từ な.", "Chúng ta hãy...; thể ý chí lịch sự.",
    "Chúng ta cùng... nhé? / Tôi làm... nhé?", "Muốn làm...; mong muốn của người nói.", "Muốn có...; mong muốn của người nói.", "A ... hơn B; cấu trúc so sánh.",
    "Nhất; mức độ cao nhất trong một nhóm.", "Cách đếm chung cho đồ vật nhỏ: một, hai, ba...", "Cách đếm người.", "Từ để hỏi cơ bản: gì, ai, ở đâu, khi nào, thế nào, tại sao.",
    "Xin đừng làm...; lời yêu cầu phủ định lịch sự.", "X, Y, v.v.; liệt kê không đầy đủ.", "Bạn có muốn... không?; lời mời lịch sự.", "Đã làm rồi.",
    "Chưa / vẫn còn, tùy theo dạng động từ đi sau.", "Khi/vào thời điểm...", "Cùng với...", "Chỉ, chỉ có...",
    "Dạng trạng từ của tính từ い.", "Dạng trạng từ của tính từ な.", "Thể て của tính từ い; dùng để nối hoặc nêu nguyên nhân.", "Thể て của tính từ な và danh từ; dùng để nối hoặc nêu nguyên nhân.",
    "Cả X lẫn Y / không X cũng không Y.", "X và Y; liệt kê đầy đủ danh từ.", "Vị trí tương đối: trên, dưới, trong, trước, sau, cạnh, bên cạnh...",
    "Bao nhiêu / mấy tuổi.", "Bao nhiêu tiền / bao nhiêu.", "Mấy giờ.", "Thứ mấy / các ngày trong tuần.",
    "Cách đếm giờ.", "Cách đếm phút.", "Cách nói tuổi.", "Cách đếm tiền yên.",
    "Cách đếm vật dài, thon.", "Cách đếm vật mỏng, phẳng.", "Mỗi/từng, dùng với đơn vị thời gian.", "Đơn vị thời lượng: giờ.",
    "Đuôi lịch sự của tính từ い.", "Vì/do... nên...",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    entries = json.loads(args.source.read_text(encoding="utf-8"))
    if len(entries) != len(MEANINGS):
        raise ValueError("Source N5 count changed; review the Vietnamese mapping.")
    with sqlite3.connect(DB_PATH) as db:
        for entry, meaning in zip(entries, MEANINGS):
            db.execute("""UPDATE grammar_patterns SET explanation_vi=?, note=?
                WHERE id IN (SELECT p.id FROM grammar_patterns p JOIN grammar_lessons l ON l.id=p.lesson_id
                WHERE l.level='N5' AND p.formula=?)""", (meaning, "Xem cấu trúc và ví dụ để nhận biết cách dùng trong câu.", entry["pattern"]))
    print(f"Localized {len(entries)} N5 pattern meanings and notes into Vietnamese.")

if __name__ == "__main__":
    main()
