# 0. 필요한 라이브러리 불러오기
# requests : 웹 페이지 요청
# BeautifulSoup : HTML 파싱
# os : GitHub Secrets 에 저장된 환경변수 사용

import requests
from bs4 import BeautifulSoup
import os


# 1. 설정값 (여기만 바꾸면 됨)

# 제목에 해당 키워드가 포함되면 알림 전송
KEYWORD = "창업"

# 디스코드 웹훅 (GitHub Secrets에 DISCORD_WEBHOOK으로 저장돼 있어야 함)
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK", "")

# 웹사이트 차단 방지용 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


# 2. 키워드 판별 함수
# 공백 / 줄바꿈이 있어도 키워드가 있으면 True
def contains_keyword(text, keyword):
    return keyword.replace(" ", "") in text.replace(" ", "").replace("\n", "")


# 3. 서경대 공지사항 가져오기
def get_notices():
    """
    서경대학교 전체공지 페이지에서
    (제목, 링크) 목록을 가져오는 함수
    """

    url = "https://www.skuniv.ac.kr/notice"

    # 1) 페이지 요청
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        print("공지 페이지 status:", res.status_code)
        res.raise_for_status()
    except Exception as e:
        print("공지 페이지 요청 실패:", e)
        return []

    # 2) HTML 파싱
    soup = BeautifulSoup(res.text, "html.parser")

    notices = []

    # 3) 공지 링크 수집
    # WordPress 기반이라 공지 링크는 a 태그 중
    # /notice/ 가 포함된 링크로 판단
    for a in soup.select("a"):
        title = a.get_text(strip=True)
        href = a.get("href")

        # 제목 없거나 링크 없으면 패스
        if not title or not href:
            continue

        # 공지 링크 조건
        if "/notice/" not in href:
            continue

        # 상대경로 -> 절대경로 변환
        if href.startswith("/"):
            href = "https://www.skuniv.ac.kr" + href

        notices.append((title, href))

    print("파싱된 공지 수:", len(notices))
    return notices


# 4. 디스코드 알림 전송 함수
def send_discord(title, url):
    """
    디스코드 웹훅으로 공지 알림 전송
    """

    if not WEBHOOK_URL:
        print("디스코드 웹훅이 설정되지 않음")
        return

    payload = {
        "content": f"**{title}**\n{url}"
    }

    try:
        res = requests.post(WEBHOOK_URL, json=payload)
        if res.status_code in [200, 204]:
            print("디스코드 전송 성공")
        else:
            print("디스코드 전송 실패:", res.status_code)
    except Exception as e:
        print("디스코드 요청 오류:", e)


# 5. 실행부 (메인 로직)
print("공지 확인 시작")

# 공지 목록 가져오기
notices = get_notices()
print("공지 개수:", len(notices))

# 이번 실행에서 중복 전송 방지
sent_this_run = set()

for title, url in notices:
    print("제목:", title)

    # 키워드 포함 + 아직 안 보낸 공지만 전송
    if contains_keyword(title, KEYWORD) and url not in sent_this_run:
        print("키워드 매칭 → 디스코드 알림 전송")
        send_discord(title, url)
        sent_this_run.add(url)
    else:
        print("조건 불일치 / 이미 전송됨")
        
