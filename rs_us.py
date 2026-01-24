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
# 1. 설정 및 종목 리스트
# =========================================================================
INDEX_TICKER = 'SPY'
RS_PERIODS = [180, 90, 60, 30, 10]
END_DATE_DT = datetime.now().date()
END_DATE = END_DATE_DT.strftime('%Y-%m-%d')

US_STOCKS_INFO = {
    'MSFT': 'Microsoft Corporation', 'GOOGL': 'Alphabet Inc.', 'META': 'Meta Platforms, Inc.',
    'NVDA': 'NVIDIA Corporation', 'AAPL': 'Apple Inc.', 'AMD': 'Advanced Micro Devices',
    'AVGO': 'Broadcom Inc.', 'MU': 'Micron Technology', 'LLY': 'Eli Lilly and Company',
    'MRNA': 'Moderna, Inc.', 'PFE': 'Pfizer Inc.', 'JNJ': 'Johnson & Johnson',
    'AMZN': 'Amazon.com, Inc.', 'WMT': 'Walmart Inc.', 'TSLA': 'Tesla, Inc.',
    'GM': 'General Motors', 'F': 'Ford Motor Company', 'MGM': 'MGM Resorts International',
    'MAR': 'Marriott International', 'JPM': 'JPMorgan Chase & Co.', 'V': 'Visa Inc.',
    'BAC': 'Bank of America', 'XOM': 'Exxon Mobil Corporation', 'CVX': 'Chevron Corporation',
    'SLB': 'Schlumberger Limited', 'ALB': 'Albemarle Corporation', 'RIO': 'Rio Tinto Group',
    'NEM': 'Newmont Corporation', 'DOW': 'Dow Inc.', 'NUE': 'Nucor Corporation',
    'CAT': 'Caterpillar Inc.', 'DE': 'John Deere & Co.', 'LMT': 'Lockheed Martin',
    'RTX': 'RTX Corporation'
}

SECTOR_TICKERS = {
    'Tech': ['MSFT', 'GOOGL', 'META', 'NVDA', 'AAPL', 'AMD', 'AVGO', 'MU'],
    'Healthcare': ['LLY', 'MRNA', 'PFE', 'JNJ'],
    'Consumer': ['AMZN', 'WMT', 'TSLA', 'GM', 'F', 'MGM', 'MAR'],
    'Financials': ['JPM', 'V', 'BAC'],
    'Energy/Materials': ['XOM', 'CVX', 'SLB', 'ALB', 'RIO', 'NEM', 'DOW', 'NUE'],
    'Industrials': ['CAT', 'DE', 'LMT', 'RTX'],
}
ALL_US_TICKERS = list(US_STOCKS_INFO.keys())

USER_RS_SORT_ORDER = 'a'
print("자동모드: 정렬기준을 '가중평균(a)로 자동 설정합니다.")

# =========================================================================
# 2. 데이터 다운로드
# =========================================================================
START_DATE_STR = (END_DATE_DT - timedelta(days=max(RS_PERIODS) * 2)).strftime('%Y-%m-%d')
print(f"💰 미국 데이터 다운로드 중... (Index: {INDEX_TICKER})")

try:
    index_data = fdr.DataReader(INDEX_TICKER, start=START_DATE_STR, end=END_DATE)
    index_prices = index_data['Close'].rename(INDEX_TICKER)

    price_list = []
    for t in ALL_US_TICKERS:
        try:
            data = fdr.DataReader(t, start=START_DATE_STR, end=END_DATE)
            if not data.empty: price_list.append(data['Close'].rename(t))
        except:
            continue

    close_prices = pd.concat(price_list, axis=1).ffill()
    index_prices = index_prices.reindex(close_prices.index).ffill()
except Exception as e:
    sys.exit(f"❌ 데이터 로드 실패: {e}")

# =========================================================================
# 3. RS 산식 적용
# =========================================================================
def calculate_rs_v2(period, stocks, index):
    s_ret = (stocks.iloc[-1] / stocks.iloc[-(period + 1)]) - 1
    i_ret = (index.iloc[-1] / index.iloc[-(period + 1)]) - 1
    i_ret_abs = np.where(np.abs(i_ret) == 0, 0.0001, np.abs(i_ret))
    ratio = np.abs(s_ret) / i_ret_abs
    excess = s_ret - i_ret
    rs_val = np.where(excess > 0, ratio, -ratio)
    ranks = pd.Series(rs_val, index=stocks.columns).rank(pct=True)
    scores = (ranks * 98 + 1).round(0).astype('Int64')
    return scores, round(i_ret * 100, 1)

rs_results, idx_rets = {}, {}
for p in RS_PERIODS:
    scores, ret = calculate_rs_v2(p, close_prices, index_prices)
    rs_results[f'RS_{p}D'], idx_rets[p] = scores, ret

rs_df = pd.DataFrame(rs_results)
rs_df['W_RS_Avg'] = rs_df.apply(lambda r: sum(r[c] * 0.2 for c in rs_df.columns if pd.notna(r[c])), axis=1).round(0).astype('Int64')
rs_df['Ticker'] = rs_df.index
rs_df['Company Name'] = rs_df['Ticker'].map(US_STOCKS_INFO)
rs_df['Sector'] = rs_df['Ticker'].map({t: s for s, ts in SECTOR_TICKERS.items() for t in ts})

ma50_latest = close_prices.rolling(window=50).mean().iloc[-1]
rs_df['Disparity(%)'] = ((close_prices.iloc[-1] / ma50_latest) - 1) * 100
rs_df['Disparity(%)'] = rs_df['Disparity(%)'].astype(float).round(1)

final_df = rs_df.sort_values(by='W_RS_Avg', ascending=False).reset_index(drop=True)
final_df.index = final_df.index + 1

# =========================================================================
# 4. 파이어베이스 전송 및 로컬 파일 저장
# =========================================================================
print("\n🇺🇸 [미국 RS] 데이터 전송 및 파일 생성 시작...")

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    us_rank_list = []
    for idx, row in final_df.iterrows():
        us_rank_list.append({
            "rank": int(idx),
            "code": str(row['Ticker']),
            "name": str(row['Company Name']),
            "rs_180": int(row['RS_180D']),
            "rs_90": int(row['RS_90D']),
            "rs_60": int(row['RS_60D']),
            "rs_30": int(row['RS_30D']),
            "rs_10": int(row['RS_10D']),
            "rs_avg": int(row['W_RS_Avg']),
            "disparity": float(row['Disparity(%)'])
        })
    
    # 전체 데이터 구성
    final_payload = {
        "update_time": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "sort_standard": USER_RS_SORT_ORDER,
        "rankings": us_rank_list
    }

    # 1. 파이어베이스 업로드
    db.collection('rs_data').document('us_latest').set(final_payload)
    
    # 2. 🆕 로컬 파일 저장 (리액트 배포용)
    with open('rs_us.json', 'w', encoding='utf-8') as f:
        json.dump(final_payload, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*50)
    print("✅ [미국 RS] 파이어베이스 및 rs_us.json 저장 완료!")
    print("=" *50)

except Exception as e:
    print(f"\n❌ 전송 실패: {e}")
