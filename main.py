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
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]


# 2. 학교 공지사항 목록 가져오기 (JSON API)
# 서경대 공지사항 API를 호출해서 최신 공지 목록을 가져오는 함수
def get_notices():
    api_url = "https://www.skuniv.ac.kr/notice/noticeListAjax.do"

    # 최신 공지 10개 요청
     params = {
        "pageIndex": 1,
        "pageUnit": 10
     }

    res = requests.get(api_url, params=params)
    res.raise_for_status()

    data = res.json()
    notices = []

    for item in data["resultList"]:
        title = item["nttSj"]  # 공지 제목
        ntt_id = item["nttId"]

        # 공지 상세 페이지 URL
        url = f"https://www.skuniv.ac.kr/notice/view.do?nttId={ntt_id}"

        notices.append((title, url))

    return notices


# 3. 공지 상세 페이지에 들어가서 본문 텍스트만 가져오는 함수
def get_notice_content(url):
    res = requests.get(url)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    # 공지 본문 영역 (서경대 기준)
    content_area = soup.select_one(".view_con")

    if content_area:
        return content_area.get_text(strip=True)

    return ""


# 4. 디스코드로 알림 보내는 함수 (제목과 본문에 키워드가 포함되어 있는 경우)
def send_discord(title, url, where):
    message = {
        "content": f"📢 **{title}**\n🔍 키워드 발견 위치: {where}\n{url}"
    }
    requests.post(WEBHOOK_URL, json=message)


# 5. 실제 실행되는 부분 (디버그용 로그 추가)
# 이번 실행에서 이미 보낸 공지를 기억하기 위한 공간
# 같은 실행 안에서 중복 알림 방지하기 위함
sent_this_run = set()

# 공지 하나씩 확인
for title, url in get_notices():

    # 제목에 키워드가 있는 경우
    if KEYWORD in title and url not in sent_this_run:
        send_discord(title, url, "제목")
        sent_this_run.add(url)
        continue

    # 제목에 없으면 -> 본문 검사
    content = get_notice_content(url)

    if KEYWORD in content and url not in sent_this_run:
        send_discord(title, url, "본문")
        sent_this_run.add(url)
