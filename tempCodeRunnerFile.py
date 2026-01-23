import yfinance as yf
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

#파이어베이스 연결

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    
db = firestore.client()

#뉴스 수집할 종목 리스트

ticker_list = ['NVDA', 'AAPL', 'TSLA'] 

#시간표 만들기(년-월-일 시:분으로 변환)
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

print(f"뉴스 수집 시작! 가준시간: {now_str}")

#반복문 돌면서 하나씩 처리

for ticker in ticker_list:
    try:
        stock = yf.Ticker(ticker)
        row_news = stock.news[:5]
        
        refined_news = []
        for n in row_news:
            refined_news.append({
                "title": n.get('title', 'No Title'),
                "link": n.get('link', '#'),
                "publisher": n.get('publisher', 'Unknown'),
               
            })
        db.collection('stock_news').document(ticker).set({
            "ticker": ticker,
            "update_time": datetime.now().strftime('%Y-%m-%d %H:%M'),
            'articles': refined_news
        })
        print(f"{ticker}컬렉션 전송 완료")
    except Exception as e:
        print(f"{ticker}처리중 오류 발생: {e}")
        
print("\n" + "=" *50)
print("모든 뉴스 뎅터 'stock_news' 컬렉션 전송 완료!")
print("=" * 50)
    