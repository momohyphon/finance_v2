import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import time
import os
import sys
import json
import pytz

# 1. 파이어베이스 인증 (경로 최적화)
JSON_PATH = r"c:\Users\gwak\Finance_Final_V2\serviceAccountKey.json"
kst = pytz.timezone('Asia/Seoul') 

if not firebase_admin._apps:
    try:
        # 1순위: 로컬 절대 경로, 2순위: 깃허브 서버(현재 폴더)
        if os.path.exists(JSON_PATH):
            cred = credentials.Certificate(JSON_PATH)
            firebase_admin.initialize_app(cred)
            print("✅ 미국뉴스: 로컬 인증 성공")
        else:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("✅ 미국뉴스: 깃허브 서버 인증 성공")
    except Exception as e:
        print(f"❌ 파이어베이스 초기화 실패: {e}")
        sys.exit(1)
        
db = firestore.client()

# 2. 미국 주식 랭킹 데이터 가져오기 (원본 경로 유지)
try:
    doc = db.collection('rs_data').document('us_latest').get() 
    if not doc.exists:
        print("❌ 미국 랭킹 데이터(us_latest)가 없습니다.")
        sys.exit(0)

    rankings = doc.to_dict().get('rankings', [])
    now_str = datetime.now(kst).strftime('%Y-%m-%d %H:%M')
    fields_to_add = {}

    print(f"🇺🇸 미국 뉴스 최신순 검색 시작 (한국시간 기준: {now_str})")

    for item in rankings:
        code = item.get('code') or item.get('ticker')
        name = item['name']
        field_key = f"{code}_{name}"
        
        try:
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

            # 🔥 오빠 원본 정렬 로직 및 20개 유지
            articles.sort(key=lambda x: x['dt_index'], reverse=True)
            final_articles = articles[:10]

            for a in final_articles: del a['dt_index']

            fields_to_add[field_key] = {
                "update_time": now_str,
                "articles": final_articles
            }
            
            print(f"✅ {name}({code}) 뉴스 {len(final_articles)}개 완료")
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ {name} 뉴스 에러: {e}")

    # 3. 파이어베이스 및 로컬 JSON 저장 (원본 경로 고정)
    if fields_to_add:
        db.collection('stock_news').document('news_us').set(fields_to_add)
        with open('news_us.json', 'w', encoding='utf-8') as f:
            json.dump(fields_to_add, f, ensure_ascii=False, indent=2)
        print(f"🚀 [완료] news_us 업데이트 완료 (KST 기준)")

except Exception as e:
    print(f"❌ 전체 실행 오류: {e}")