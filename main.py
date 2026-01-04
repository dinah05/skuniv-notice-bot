# 0. 필요한 도구 불러오기
# requests : 웹 페이지의 내용을 가져오기 위한 도구
# BeautifulSoup : 웹 페이지에서 제목 같은 정보만 뽑아내기 위한 도구
# os : 깃허브에 저장된 환경변수를 읽기 위한 도구


import requests
from bs4 import BeautifulSoup
import os


# 1. 내가 바꿀 수 있는 설정값 (다른 학교 / 다른 키워드로 바꿀 때, 여기만 수정하면 됨)
# 서경대 공지사항 페이지 주소
TARGET_URL = "https://www.skuniv.ac.kr/notice"

# 내가 찾고 싶은 단어 (이 단어가 제목에 있으면 알림)
# 테스트용 키워드!!!
KEYWORD = "안내"

# 디스코드 웹훅, 이거 건드리면 안댐
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]


# 2. 공지 목록을 가져오는 함수
# 학교 공지사항 페이지에 접속해서 공지 제목과 링크를 가져옴
# 웹 사이트가 사람이 접속한 것처럼 보이게 만드는 설정
def get_notices():
    headers = {"User-Agent": "Mozilla/5.0"}
    # 공지 페이지 요청
    res = requests.get(TARGET_URL, headers=headers)
    res.raise_for_status() #에러가 나면 여기서 멈춤

    # HTML 분석 준비
    soup = BeautifulSoup(res.text, "html.parser")
    notices = []

    # 공지사항 목록에서 제목 + 링크만 가져옴
    # [:10] -> 최신 공지 10개만 확인 (너무 많이 검사하지 않기 위햬)
    for item in soup.select("td.title a")[:10]:
        title = item.get_text(strip=True)     # 공지 제목
        link = "https://www.skuniv.ac.kr" + item["href"]     # 공지 링크
        notices.append((title, link))

    return notices


# 3. 공지 상세 페이지에 들어가서 본문 텍스트만 가져오는 함수
def get_notice_content(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
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


# 5. 실제 실행되는 부분
# 이번 실행에서 이미 보낸 공지를 기억하기 위한 공간
# 같은 실행 안에서 중복 알림 방지하기 위함
sent_this_run = set()

# 공지 하나씩 확인
for title, url in get_notices():

    # ① 제목에 키워드가 포함되어 있으면 바로 알림
    if KEYWORD in title and url not in sent_this_run:
        send_discord(title, url, "제목")
        sent_this_run.add(url)
        continue

    # ② 제목에 없으면 → 공지 상세 페이지에 들어가서 본문 검사
    content = get_notice_content(url)

    if KEYWORD in content and url not in sent_this_run:
        send_discord(title, url, "본문")     # 디스코드로 알림 보내기
        sent_this_run.add(url)     # 보냈다고 기록
