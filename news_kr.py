import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import time
import os
import json
import pytz
import sys

# 1. 파이어베이스 초기화 (원본 경로 및 로직 유지)
if not firebase_admin._apps:
    try:
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
        else:
            cred = credentials.Certificate(r"c:\Users\gwak\Finance_Final_V2\serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("✅ 파이어베이스 인증 성공")
    except Exception as e:
        print(f"❌ 파이어베이스 초기화 실패: {e}")
        sys.exit(1)

db = firestore.client()

# 2. RS 데이터에서 상위 종목 가져오기
doc = db.collection('rs_data').document('latest').get()
if not doc.exists:
    print("❌ rs_data/latest 문서가 없습니다.")
    sys.exit(0)

rankings = doc.to_dict().get('rankings', [])
kst = pytz.timezone('Asia/Seoul')
now_str = datetime.now(kst).strftime('%Y-%m-%d %H:%M')
fields_to_add = {}

# 오빠 원본 문구 그대로 유지
print(f"📰 한국 뉴스 30개 수집 시작: {now_str}")

for item in rankings:
    code = item['code']
    name = item['name']
    field_key = f"{code}_{name}"
    
    try:
        url = f"https://news.google.com/rss/search?q={quote_plus(name)}&hl=ko&gl=KR&ceid=KR:ko"
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
            raw_date = i.pubDate.text
            try:
                dt_obj = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %Z')
                dt_obj = dt_obj.replace(tzinfo=pytz.UTC).astimezone(kst)
            except:
                dt_obj = datetime.now(kst)

            articles.append({
                "title": title,
                "link": i.link.text,
                "publisher": i.source.text if i.source else "Google News",
                "time": dt_obj.strftime('%Y-%m-%d %H:%M'),
                "dt_index": dt_obj
            })

        # --- [원본 유지] 최신순 정렬 후 상위 20개 추출 ---
        articles.sort(key=lambda x: x['dt_index'], reverse=True)
        final_articles = articles[:20]

        for a in final_articles: del a['dt_index']

        fields_to_add[field_key] = {
            "update_time": now_str,
            "articles": final_articles
        }
        print(f" > {name}({code}) 최신 뉴스 {len(final_articles)}개 완료")
        time.sleep(0.5)

    except Exception as e:
        print(f" > {name} 오류: {e}")

# 3. 파이어베이스 전송 (오빠가 지정한 경로 고정)
try:
    db.collection('stock_news').document('news_kr').set(fields_to_add)
    with open('news_kr.json', 'w', encoding='utf-8') as f:
        json.dump(fields_to_add, f, ensure_ascii=False, indent=2)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ 모든 한국 뉴스 업데이트 완료")
except Exception as e:
    print(f"❌ 저장 오류: {e}")