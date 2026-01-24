import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import FinanceDataReader as fdr
from tabulate import tabulate
import sys
import os
import firebase_admin
from firebase_admin import credentials, firestore
import json  # 👈 1. JSON 임포트 추가 완료

# =========================================================================
# 1. 설정 변수 및 종목 리스트 강제 지정
# =========================================================================
INDEX_TICKER = 'KS11'
RS_PERIODS = [180, 90, 60, 30, 10]
TOP_N = 50
END_DATE_DT = datetime.now().date()
END_DATE = END_DATE_DT.strftime('%Y-%m-%d')

print("🔍 한글 종목명 사전 자동 생성 중...")
try:
    krx_list = fdr.StockListing('KRX')[['Code', 'Name']]
    K_NAME_DICT = dict(pd.Series(krx_list.Name.values, index=krx_list.Code.values))
except:
    print("⚠️ 상장사 리스트를 가져오지 못했습니다.")
    K_NAME_DICT = {}

USER_RS_SORT_ORDER = 'a'

raw_data = """
005930,Samsung Electronics
000660,SK hynix
373220,LG Energy Solution
207940,Samsung Biologics
005380,Hyundai Motor Company
329180,HD Hyundai Motor Company
034020,Doosan Energy
012450,Hanwha Aerospace
105560,KB Financial
000270,Kia
068270,Celltrion
035420,NAVER
402340,SK Square
028260,Samsung C&T
055550,Shinhan Holdings
015760,KEPCO
009540,HD Hyundai Heavy Industries
032830,Samsung Life Insurance
051910,LG Chem
012330,Hyundai Mobis
035720,kakao
005490,POSCO Holdings
086790,Hana Financial Group
006400,Samsung SDI
010130,Korea Zinc
000810,Samsung Fire & Marine Insurance
096770,SK Innovation
034730,SK
316140,Woori Financial Group
138040,Meritz Financial Holdings
011200,HMM
003670,POSCO Future M
033780,KT&G
009150,Samsung Electro-Mechanics
024110,Industrial Bank of Korea
066570,LG Electronics
018260,Samsung SDS
352820,hive
030200,KT
003550,LG
086280,Hyundai Glovis
259960,Krafton
042700,Hanmi Semiconductor
017670,SK Telecom
323410,Kakao Bank
010950,S-Oil
326030,SK Biopharm 
047050,POSCO International
090430,Amorepacific
"""

USER_ENGLISH_NAMES = {}
KOSPI_TICKERS = []
extracted_tickers = set()

for line in raw_data.strip().split('\n'):
    parts = line.split(',', 1)
    if len(parts) < 2: continue
    code, name = parts[0].strip(), parts[1].strip()
    if code not in extracted_tickers:
        USER_ENGLISH_NAMES[code] = name
        KOSPI_TICKERS.append(code)
        extracted_tickers.add(code)

KOSPI_TICKERS = KOSPI_TICKERS[:TOP_N]

# =========================================================================
# 2. 데이터 다운로드
# =========================================================================
MAX_LOOKBACK_DAYS = (max(RS_PERIODS) + 60) * 2
START_DATE_STR = (END_DATE_DT - timedelta(days=MAX_LOOKBACK_DAYS)).strftime('%Y-%m-%d')

try:
    index_data = fdr.DataReader(INDEX_TICKER, start=START_DATE_STR, end=END_DATE)
    index_prices_raw = index_data['Close'].rename(INDEX_TICKER)
except Exception as e:
    sys.exit(f"❌ 지수 데이터 로드 실패: {e}")

price_data_list = []
for code in KOSPI_TICKERS:
    try:
        data = fdr.DataReader(code, start=START_DATE_STR, end=END_DATE)
        if not data.empty:
            price_data_list.append(data['Close'].rename(code))
    except:
        continue

close_prices_raw = pd.concat(price_data_list, axis=1)
close_prices_final = close_prices_raw.ffill()
index_prices_final = index_prices_raw.reindex(close_prices_final.index).ffill()

# =========================================================================
# 3. RS 계산 및 출력
# =========================================================================
def calculate_period_rs(period, close_prices, index_prices):
    if len(close_prices) < period + 1:
        return pd.Series(np.nan, index=close_prices.columns), 0
    P_past, P_current = close_prices.iloc[-(period + 1)], close_prices.iloc[-1]
    I_past, I_current = index_prices.iloc[-(period + 1)], index_prices.iloc[-1]
    ret_stock, ret_index = (P_current / P_past) - 1, (I_current / I_past) - 1
    excess = ret_stock - ret_index
    idx_ret_val = abs(ret_index) if abs(ret_index) != 0 else 0.0001
    rs_val = np.where(excess > 0, np.abs(ret_stock) / idx_ret_val, -np.abs(ret_stock) / idx_ret_val)
    rs_series = pd.Series(rs_val, index=close_prices.columns)
    ranks = rs_series.rank(pct=True, method='average')
    scores = (ranks * 98 + 1).round(0).astype('Int64')
    return scores, round(ret_index * 100, 1)

rs_results, idx_rets = {}, {}
for p in RS_PERIODS:
    scores, idx_ret = calculate_period_rs(p, close_prices_final, index_prices_final)
    rs_results[f'RS_{p}D'], idx_rets[p] = scores, idx_ret

rs_df = pd.DataFrame(rs_results)
weights = {'RS_180D': 0.2, 'RS_90D': 0.2, 'RS_60D': 0.2, 'RS_30D': 0.2, 'RS_10D': 0.2}
rs_df['W_RS_Avg'] = rs_df.apply(lambda r: sum(r[c] * w for c, w in weights.items() if pd.notna(r[c])), axis=1).round(0).astype('Int64')
rs_df['Disparity(%)'] = (((close_prices_final.iloc[-1] / close_prices_final.rolling(50).mean().iloc[-1]) - 1) * 100).round(1)
rs_df['Ticker'] = rs_df.index.map(USER_ENGLISH_NAMES)
final_df = rs_df.sort_values(by='W_RS_Avg', ascending=False).reset_index().rename(columns={'index': 'Code'})
final_df.index = final_df.index + 1

# =========================================================================
# 4. 파이어베이스 전송 및 [핵심] 로컬 파일 저장
# =========================================================================
print("\n🚀 [한국 RS] 데이터 전송 및 파일 생성 시작...")

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    kr_rank_list = []
    
    for idx, row in final_df.iterrows():
        kr_rank_list.append({
            "rank": int(idx),
            "code": str(row['Code']),
            "name": K_NAME_DICT.get(str(row['Code']), str(row['Ticker'])),
            "rs_180": int(row['RS_180D']),
            "rs_90": int(row['RS_90D']),
            "rs_60": int(row['RS_60D']),
            "rs_30": int(row['RS_30D']),
            "rs_10": int(row['RS_10D']),
            "rs_avg": int(row['W_RS_Avg']),
            "disparity": float(row['Disparity(%)']),
        })

    # 전체 데이터 구성
    final_payload = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "rankings": kr_rank_list
    }

    # 1. 파이어베이스 업로드
    db.collection('rs_data').document('latest').set(final_payload)

    # 2. 🆕 로컬 파일 저장 (여기서 파일이 생겨야 액션이 성공함!)
    with open('rs_kr.json', 'w', encoding='utf-8') as f:
        json.dump(final_payload, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print("✅ 파이어베이스 전송 & rs_kr.json 파일 생성 성공!")
    print("=" * 50)

except Exception as e:
    print(f"\n❌ 에러 발생: {e}")
