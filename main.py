# 0. 필요한 도구 불러오기
# requests : 학교 서버 (API) 에 요청 보내는 도구
# BeautifulSoup : HTML에서 본문 텍스트만 깔끔하게 추출
# os : 깃허브에 저장된 디스코드 웹훅 불러오기

import requests
from bs4 import BeautifulSoup
import os

# 1. 내가 바꿀 수 있는 설정값 (다른 학교 / 다른 키워드로 바꿀 때, 여기만 수정하면 됨)
# 내가 찾고 싶은 키워드 (이 키워드가 제목에 있으면 알림)
KEYWORD = "안내"

# 디스코드 웹훅
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK", "")

# 키워드 판별 함수 (공백/줄바꿈 무시)
def contains_keyword(text, keyword):
    return keyword.replace(" ", "") in text.replace(" ", "").replace("\n", "")

# 2. 학교 공지사항 목록 가져오기 (HTML 크롤링)
def get_notices():
    url = "https://www.skuniv.ac.kr/notice"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    res = requests.get(url, headers=headers)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    notices = []

    rows = soup.select("td[class*='subject'] a")

    for row in rows[:10]:  # 최신 10개
        title = row.get_text(strip=True)
        href = row.get("href")

        if href and not href.startswith("http"):
            notice_url = f"https://www.skuniv.ac.kr{href}"
        else:
            notice_url = href

        notices.append((title, notice_url))

    print("파싱된 공지 목록:", notices)

    return notices
    
# 3. 디스코드로 알림 보내는 함수
def send_discord(title, url):
    if not WEBHOOK_URL:
        print("웹훅 없음")
        return

    message = {
        "content": f"📢 **{title}**\n{url}"
    }
    requests.post(WEBHOOK_URL, json=message)

# 4. 실행부
notices = get_notices()

print(f"공지 개수: {len(notices)}")

for title, url in notices:
    print("제목:", title)

    if "안내" in title:
        print("안내 키워드 매칭됨 → 디스코드 전송")
        send_discord(title, url)
    else:
        print("키워드 불일치")

