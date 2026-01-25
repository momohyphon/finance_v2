import FinanceDataReader as fdr
from pandas_datareader import data as pdr
import datetime
from datetime import timezone, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import time
import os
import json
import sys

def get_kst_now():
    KST = timezone(timedelta(hours=9))
    return datetime.datetime.now(KST)

# 1. 파이어베이스 초기화 (경로 고정 및 인증 최적화)
if not firebase_admin._apps:
    try:
        # 1순위: 깃허브 액션용(현재 폴더), 2순위: 로컬 절대 경로
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
        else:
            cred = credentials.Certificate(r"c:\Users\gwak\Finance_Final_V2\serviceAccountKey.json")
        
        firebase_admin.initialize_app(cred)
        print("✅ 파이어베이스 인증 성공")
    except Exception as e:
        print(f"❌ 파이어베이스 인증 오류: {e}")
        sys.exit(1)

db = firestore.client()

print("🚀 금융 데이터 자동 업데이트를 시작합니다.")

# 데이터 구조 초기화
finance_payload = {
    "update_time": get_kst_now().strftime("%Y-%m-%d %H:%M"),
    "bonds": {},
    "items": []
}

# 조회 기간 설정 (FRED 데이터용)
start = datetime.datetime.now() - datetime.timedelta(days=10)
end = datetime.datetime.now()

# --- [1] 금리 데이터 수집 ---
print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"📊 업데이트 시간: {get_kst_now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

try:
    # 2년물
    dgs2 = pdr.DataReader('DGS2', 'fred', start, end).dropna()
    l2, p2 = dgs2['DGS2'].iloc[-1], dgs2['DGS2'].iloc[-2]
    c2 = (l2 - p2) / p2 * 100
    print(f" > 미국채 2년 금리:  {l2:.2f}% ({c2:+.2f}%)")

    # 10년물
    tnx = fdr.DataReader('^TNX')['Close'].dropna()
    l10, p10 = tnx.iloc[-1], tnx.iloc[-2]
    c10 = (l10 - p10) / p10 * 100
    print(f" > 미국채 10년 금리: {l10:.2f}% ({c10:+.2f}%)")

    # 30년물
    tyx = fdr.DataReader('^TYX')['Close'].dropna()
    l30, p30 = tyx.iloc[-1], tyx.iloc[-2]
    c30 = (l30 - p30) / p30 * 100
    print(f" > 미국채 30년 금리: {l30:.2f}% ({c30:+.2f}%)")
    print(f"--------------------------------------------------")

    finance_payload["bonds"] = {
        "2Y_val": round(l2, 2), "2Y_chg": round(c2, 2), "2Y_link": "https://finance.yahoo.com/quote/ZT=F/",
        "10Y_val": round(l10, 2), "10Y_chg": round(c10, 2), "10Y_link": "https://finance.yahoo.com/quote/%5ETNX/",
        "30Y_val": round(l30, 2), "30Y_chg": round(c30, 2), "30Y_link": "https://finance.yahoo.com/quote/%5ETYX/"
    }
except Exception as e:
    print(f"⚠️ 금리 데이터 수집 중 오류: {e}")

# --- [2] 주요 지표 데이터 수집 ---
tickers = {
    "달러 인덱스": ("DX=F", "https://finance.yahoo.com/quote/DX-Y.NYB/"),
    "나스닥 지수": ("^IXIC", "https://finance.yahoo.com/quote/^IXIC/"),
    "S&P500 지수": ("^GSPC", "https://finance.yahoo.com/quote/^GSPC/"),
    "나스닥 선물": ("NQ=F", "https://finance.yahoo.com/quote/NQ=F/"),
    "S&P500 선물": ("ES=F", "https://finance.yahoo.com/quote/ES=F/"),
    "WTI 유가": ("CL=F", "https://finance.yahoo.com/quote/CL=F/"),
    "금 가격": ("GC=F", "https://finance.yahoo.com/quote/GC=F/"),
    "비트코인": ("BTC-USD", "https://finance.yahoo.com/quote/BTC-USD/"),
    "반도체(SOXX)": ("SOXX", "https://finance.yahoo.com/quote/SOXX/"),
    "철강(SLX)": ("SLX", "https://finance.yahoo.com/quote/SLX/"),
    "구리 가격": ("HG=F", "https://finance.yahoo.com/quote/HG=F/"),
    "환율(엔화)": ("JPY=X", "https://finance.yahoo.com/quote/JPY%3DX/"),
    "환율(원화)": ("KRW=X", "https://finance.yahoo.com/quote/KRW=X/")
}

for name, (symbol, link) in tickers.items():
    try:
        df = fdr.DataReader(symbol)
        df_c = df['Close'].dropna()
        if len(df_c) < 2: continue
        cur, prev = df_c.iloc[-1], df_c.iloc[-2]
        pct = (cur - prev) / prev * 100
        
        v_str = f"{cur:.2f}" if "환율" not in name else f"{cur:.3f}"
        print(f" > {name:12}: {v_str:>8} ({pct:+.2f}%)")

        finance_payload["items"].append({
            "name": name,
            "price": round(cur, 3) if "환율" in name else round(cur, 2),
            "change": round(pct, 2),
            "Link": link
        })
    except:
        continue

# 3. 데이터 저장 (오빠가 지정한 경로 절대 고정)
try:
    # 컬렉션: market_data / 문서: global_indices
    db.collection('market_data').document('global_indices').set(finance_payload)

    # 로컬 JSON 파일 저장 (GitHub Actions 빌드용)
    with open('market_data.json', 'w', encoding='utf-8') as f:
        json.dump(finance_payload, f, ensure_ascii=False, indent=2)

    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ market_data/global_indices 업데이트 완료!")
except Exception as e:
    print(f"❌ 저장 중 오류 발생: {e}")