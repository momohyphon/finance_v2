import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import time
import os
import sys

JSON_PATH = r"c:\Users\gwak\Finance_Final_V2\serviceAccountKey.json"

# 1. 파이어베이스 연결
if not firebase_admin._apps:
    try:
        if os.path.exists(JSON_PATH):
            cred = credentials.Certificate(JSON_PATH)
            firebase_admin.initialize_app(cred)
            print("미국뉴스: 파이어베이스 인증 성공")
        else:
            cred = credentials.Certificate("serviceAccountKey.JSON")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"파이어베이스 초기화 실패: {e}")
        
db = firestore.client()


    
# 2. 미국 주식 랭킹 데이터에서 종목 리스트 가져오기 (오빠의 US용 latest 경로 확인)
doc = db.collection('rs_data').document('us_latest').get() 
if not doc.exists:
    print("❌ 미국 랭킹 데이터가 없습니다.")
    sys.exit()

rankings = doc.to_dict().get('rankings', [])
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

# 📢 [핵심] news_us 문서 하나에 다 집어넣을 딕셔너리
fields_to_add = {}

print(f"🇺🇸 미국 뉴스 검색 시작 ({len(rankings)}개 종목)")

for item in rankings:
    # 미국 데이터 필드명에 맞춰 ticker 또는 code 사용
    code = item.get('code') or item.get('ticker')
    name = item['name']
    
    # 📢 [필터 표시] 필드 이름을 '종목코드_종목명'으로 설정
    field_key = f"{code}_{name}"
    
    try:
        # 미국 뉴스용 RSS (언어: en-US, 지역: US)
        url = f"https://news.google.com/rss/search?q={quote_plus(name)}&hl=en-US&gl=US&ceid=US:en"
        res = requests.get(url, timeout=10)
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

        # 📢 딕셔너리에 필드명으로 데이터 저장
        fields_to_add[field_key] = {
            "update_time": now_str,
            "articles": articles
        }
        
        print(f"✅ 필드 준비: {field_key}")
        time.sleep(0.3) # 차단 방지

    except Exception as e:
        print(f"❌ {name} 뉴스 에러: {e}")

# ==========================================================
# 📢 [최종 반영] stock_news 컬렉션 -> 'news_us' 문서 딱 하나에 모든 필드 꽂기
# ==========================================================
db.collection('stock_news').document('news_us').set(fields_to_add)
print(f"🚀 [완료] news_us 문서에 모든 미국 종목 필드가 추가되었습니다!")


    