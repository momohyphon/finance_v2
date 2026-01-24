import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import time
import os
import sys

# 1. 파이어베이스 인증 (경로 최적화: 깃허브 액션 & 로컬 겸용)
JSON_PATH = r"c:\Users\gwak\Finance_Final_V2\serviceAccountKey.json"

if not firebase_admin._apps:
    try:
        if os.path.exists(JSON_PATH):
            cred = credentials.Certificate(JSON_PATH)
            firebase_admin.initialize_app(cred)
            print("✅ 미국뉴스: 로컬 인증 성공")
        else:
            # 깃허브 액션 서버 환경일 경우
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("✅ 미국뉴스: 깃허브 서버 인증 성공")
    except Exception as e:
        print(f"❌ 파이어베이스 초기화 실패: {e}")
        
db = firestore.client()

# 2. 미국 주식 랭킹 데이터 가져오기
doc = db.collection('rs_data').document('us_latest').get() 
if not doc.exists:
    print("❌ 미국 랭킹 데이터(us_latest)가 없습니다.")
    sys.exit()

rankings = doc.to_dict().get('rankings', [])
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
fields_to_add = {}

print(f"🇺🇸 미국 뉴스 30개 최신순 검색 시작 ({len(rankings)}개 종목)")

for item in rankings:
    code = item.get('code') or item.get('ticker')
    name = item['name']
    field_key = f"{code}_{name}"
    
    try:
        # 미국 뉴스용 RSS (언어: en-US, 지역: US)
        url = f"https://news.google.com/rss/search?q={quote_plus(name)}&hl=en-US&gl=US&ceid=US:en"
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")

        articles = []
        seen_titles = set()
        for i in items:
            title = i.title.text.strip()
            if title in seen_titles:
                continue
            seen_titles.add(title)
            # RSS 날짜 형식 예: "Sat, 24 Jan 2026 07:00:00 GMT"
            raw_date = i.pubDate.text
            try:
                # 글자로 된 날짜를 파이썬 시간 객체로 변환 (정렬용)
                dt_obj = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %Z')
            except:
                dt_obj = datetime.now()

            articles.append({
                "title": title,
                "link": i.link.text,
                "publisher": i.source.text if i.source else "Google News",
                "time": dt_obj.strftime('%Y-%m-%d %H:%M'), # 사람이 읽기 편한 시간
                "dt_index": dt_obj # 정렬을 위한 임시 필드
            })

        # 🔥 [핵심] 시간순으로 정렬 (최신이 맨 위로) 후 30개만 자르기
        articles.sort(key=lambda x: x['dt_index'], reverse=True)
        final_articles = articles[:20]

        # 저장할 때는 정렬용 임시 필드 삭제
        for a in final_articles: del a['dt_index']

        fields_to_add[field_key] = {
            "update_time": now_str,
            "articles": final_articles
        }
        
        print(f"✅ {name}({code}) 최신 뉴스 {len(final_articles)}개 완료")
        time.sleep(0.5) # 구글 차단 방지용

    except Exception as e:
        print(f"❌ {name} 뉴스 에러: {e}")

# 3. 파이어베이스에 한 번에 저장
db.collection('stock_news').document('news_us').set(fields_to_add)
print(f"🚀 [완료] news_us 문서 업데이트 완료!")