import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import time
import os
import sys

# --- [수정] 파일 경로를 절대 경로로 고정하여 어디서든 실행 가능하게 만듦 ---
# 사용자님의 환경에 맞춘 실제 경로입니다.
JSON_PATH = r"c:\Users\gwak\Finance_Final_V2\serviceAccountKey.json"

if not firebase_admin._apps:
    try:
        # 파일이 실제로 있는지 확인부터 합니다.
        if os.path.exists(JSON_PATH):
            cred = credentials.Certificate(JSON_PATH)
            firebase_admin.initialize_app(cred)
            print("✅ 파이어베이스 인증 성공")
        else:
            print(f"❌ 인증 파일을 찾을 수 없습니다: {JSON_PATH}")
            # 파일 위치가 다를 경우를 대비해 현재 실행 폴더의 파일이라도 시도
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"❌ 파이어베이스 초기화 실패: {e}")

db = firestore.client()

# 2. 메인 실행 루프
print("🚀 한국 뉴스 자동 업데이트를 시작합니다.")


# rs_data/latest 문서 가져오기 (리액트 연동 구조 유지)
doc = db.collection('rs_data').document('latest').get()
if not doc.exists:
    print("❌ rs_data/latest 문서가 없습니다. 1분 후 재시도.")
    sys.exit()

rankings = doc.to_dict().get('rankings', [])
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
fields_to_add = {}

print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"📰 뉴스 수집 시작: {now_str}")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

for item in rankings:
    code = item['code']
    name = item['name']
    field_key = f"{code}_{name}"
    
    try:
        url = f"https://news.google.com/rss/search?q={quote_plus(name)}&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")[:20]

        articles = []
        for i in items:
            articles.append({
                "title": i.title.text,
                "link": i.link.text,
                "publisher": i.source.text if i.source else "Google News",
                "time": i.pubDate.text
            })

        fields_to_add[field_key] = {
            "update_time": now_str,
            "articles": articles
        }
        print(f" > {name}({code}) 완료")
        time.sleep(0.3)
    except Exception as e:
        print(f" > {name} 오류: {e}")

# 리액트가 읽는 문서에 덮어쓰기
db.collection('stock_news').document('news_kr').set(fields_to_add)


