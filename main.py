# 0. 필요한 도구 불러오기
import requests
from bs4 import BeautifulSoup
import os

# 1. 설정값
KEYWORD = "안내"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

# 2. 공지 목록 가져오기 (HTML 크롤링)
def get_notices():
    url = "https://www.skuniv.ac.kr/notice"

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        print("공지 페이지 status:", res.status_code)
        res.raise_for_status()
    except Exception as e:
        print("공지 페이지 요청 실패:", e)
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    print("HTML 일부 ↓↓↓")
    print(res.text[:1500])

    # 서경대 공지 목록 구조 기준
    rows = soup.select("table.board_list tbody tr")

    for row in rows[:10]:
        a = row.select_one("td.td_subject a")
        if not a:
            continue

        title = a.get_text(strip=True)
        href = a.get("href")

        if href and not href.startswith("http"):
            notice_url = f"https://www.skuniv.ac.kr{href}"
        else:
            notice_url = href

        notices.append((title, notice_url))

    print("파싱된 공지 수:", len(notices))
    return notices


# 3. 디스코드 알림
def send_discord(title, url):
    if not WEBHOOK_URL:
        print("웹훅 없음 → 디스코드 전송 생략")
        return

    message = {
        "content": f" **{title}**\n{url}"
    }

    try:
        res = requests.post(WEBHOOK_URL, json=message, timeout=10)
        print("Discord status:", res.status_code)
    except Exception as e:
        print("디스코드 전송 실패:", e)


# 4. 실행부
print("공지 확인 시작")
notices = get_notices()
print(f"공지 개수: {len(notices)}")

for title, url in notices:
    print("제목:", title)

    if KEYWORD in title:
        print("키워드 매칭 → 디스코드 전송")
        send_discord(title, url)
    else:
        print("키워드 없음")
