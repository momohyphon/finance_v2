import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import time
import os

# 1. 파이어베이스 초기화 (깃허브/로컬 공용)
if not firebase_admin._apps:
    try:
        # 1순위: 깃허브 액션용(현재 폴더), 2순위: 오빠 PC 절대 경로
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
        else:
            cred = credentials.Certificate(r"c:\Users\gwak\Finance_Final_V2\serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("✅ 파이어베이스 인증 성공")
    except Exception as e:
        print(f"❌ 파이어베이스 초기화 실패: {e}")

db = firestore.client()

# 2. RS 데이터에서 상위 종목 가져오기
doc = db.collection('rs_data').document('latest').get()
if not doc.exists:
    print("❌ rs_data/latest 문서가 없습니다.")
    exit()

rankings = doc.to_dict().get('rankings', [])
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
fields_to_add = {}

print(f"📰 한국 뉴스 30개 수집 시작: {now_str}")

for item in rankings:
    code = item['code']
    name = item['name']
    field_key = f"{code}_{name}"
    
    try:
        # 구글 뉴스 RSS (검색어 기반)
        url = f"https://news.google.com/rss/search?q={quote_plus(name)}&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")

        articles = []
        seen_titles = set()
        for i in items:
            # RSS 날짜 형식: "Sat, 24 Jan 2026 07:00:00 GMT"
            # 이를 파이썬 날짜 객체로 변환해서 정렬에 사용
            title = i.title.text.strip()
            if title in seen_titles:
                continue
            seen_titles.add(title)
            raw_date = i.pubDate.text
            try:
                dt_obj = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %Z')
            except:
                dt_obj = datetime.now() # 변환 실패 시 현재시간

            articles.append({
                "title": title,
                "link": i.link.text,
                "publisher": i.source.text if i.source else "Google News",
                "time": dt_obj.strftime('%Y-%m-%d %H:%M'), # 리액트에서 보기 편한 형식
                "dt_index": dt_obj # 정렬용 임시 필드
            })

        # --- [핵심] 최신순 정렬 후 상위 30개만 자르기 ---
        articles.sort(key=lambda x: x['dt_index'], reverse=True)
        final_articles = articles[:20]

        # 정렬용 임시 필드 삭제 후 저장
        for a in final_articles: del a['dt_index']

        fields_to_add[field_key] = {
            "update_time": now_str,
            "articles": final_articles
        }
        print(f" > {name}({code}) 최신 뉴스 {len(final_articles)}개 완료")
        time.sleep(0.5) # 구글 차단 방지

    except Exception as e:
        print(f" > {name} 오류: {e}")

# 3. 파이어베이스 전송
db.collection('stock_news').document('news_kr').set(fields_to_add)
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("✅ 모든 한국 뉴스 업데이트 완료")