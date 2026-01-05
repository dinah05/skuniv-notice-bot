# 0. 필요한 도구 불러오기
# requests : 학교 서버 (API) 에 요청 보내는 도구
# BeautifulSoup : HTML에서 본문 텍스트만 깔끔하게 추출
# os : 깃허브에 저장된 디스코드 웹훅 불러오기

import requests
from bs4 import BeautifulSoup
import os

# 1. 내가 바꿀 수 있는 설정값 (다른 학교 / 다른 키워드로 바꿀 때, 여기만 수정하면 됨)
# 내가 찾고 싶은 키워드 (이 키워드가 제목 또는 본문에 있으면 알림)
# 테스트용 키워드!!!
KEYWORD = "안내"

# 디스코드 웹훅, 이거 건드리면 안댐
# (참고: 깃허브 Settings > Secrets에 'DISCORD_WEBHOOK'이 꼭 등록되어 있어야 해요!)
try:
    WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
except KeyError:
    # 로컬(내 컴퓨터)에서 테스트할 때 에러 안 나게 임시 처리 (실제 작동시엔 깃허브 시크릿 사용)
    WEBHOOK_URL = "" 
    print("⚠️ 경고: 웹훅 URL을 찾을 수 없습니다. (깃허브 Actions 환경이 아니거나 Secret 설정 누락)")

# 2. 학교 공지사항 목록 가져오기 (HTML 크롤링)
def get_notices():
    url = "https://www.skuniv.ac.kr/notice"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/118.0.5993.118 Safari/537.36"
    }
    res = requests.get(url, headers=headers)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    notices = []

    # 'subject'라는 단어가 들어가는 모든 칸을 찾습니다 (언더바, 하이픈 상관없음)
    rows = soup.select("td[class*='subject']")

    for row in rows[:10]:  # 최신 10개
        title_tag = row.select_one("a")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        href = title_tag.get("href")

        # 링크가 http로 시작하지 않으면 도메인 붙여주기
        if href and not href.startswith("http"):
            notice_url = f"https://www.skuniv.ac.kr{href}"
        else:
            notice_url = href

        notices.append((title, notice_url))

    return notices



# 3. 공지 상세 페이지에 들어가서 본문 텍스트만 가져오는 함수
def get_notice_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/118.0.5993.118 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        content_area = soup.select_one(".view_con")

        if content_area:
            return content_area.get_text(strip=True)
    except Exception:
        pass # 본문 못 가져와도 에러 내지 말고 넘어가기
    return ""


# 4. 디스코드로 알림 보내는 함수 (제목과 본문에 키워드가 포함되어 있는 경우)
def send_discord(title, url, where):
    if not WEBHOOK_URL: # 웹훅 주소가 없으면 전송 시도 안 함
        print("❌ 웹훅 주소가 없어서 메시지를 못 보냈습니다.")
        return

    message = {
        "content": f"📢 **{title}**\n🔍 키워드 발견 위치: {where}\n{url}"
    }
    try:
        res = requests.post(WEBHOOK_URL, json=message)
        print("Discord status:", res.status_code)
        # print("Discord response:", res.text) # 로그가 너무 지저분해져서 주석 처리
        res.raise_for_status()
    except Exception as e:
        print("Discord 알림 전송 실패:", e)

# 5. 실제 실행되는 부분 (디버그용 로그 추가)
# 이번 실행에서 이미 보낸 공지를 기억하기 위한 공간
# 같은 실행 안에서 중복 알림 방지하기 위함
sent_this_run = set()

# 공지 하나씩 확인
print("Checking notices...") # <--- (추가됨) 실행 되는지 확인용 로그
found_notices = get_notices()
print(f"Found {len(found_notices)} notices.") # <--- (추가됨) 몇 개 찾았는지 확인

for title, url in found_notices:

    # 제목에 키워드가 있는 경우
    if KEYWORD in title and url not in sent_this_run:
        print(f"Keyword found in TITLE: {title}") # <--- (추가됨)
        send_discord(title, url, "제목")
        sent_this_run.add(url)
        continue

    # 제목에 없으면 -> 본문 검사
    content = get_notice_content(url)

    if KEYWORD in content and url not in sent_this_run:
        print(f"Keyword found in CONTENT: {title}") # <--- (추가됨)
        send_discord(title, url, "본문")
        sent_this_run.add(url)
