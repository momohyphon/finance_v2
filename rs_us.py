import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import FinanceDataReader as fdr
from tabulate import tabulate
import plotly.graph_objects as go
import webbrowser
import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore

# =========================================================================
# 1. 설정 및 종목 리스트 (기존 유지)
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

# 정렬 기준 입력
USER_RS_SORT_ORDER = 'a'
print("자동모드: 정렬기준을 '가중평균(a)로 자동 설정합니다.")

# =========================================================================
# 2. 데이터 다운로드 (기존 유지)
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
# 3. RS 산식 적용 (기존 유지)
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


rs_results = {}
idx_rets = {}
for p in RS_PERIODS:
    scores, ret = calculate_rs_v2(p, close_prices, index_prices)
    rs_results[f'RS_{p}D'] = scores
    idx_rets[p] = ret

rs_df = pd.DataFrame(rs_results)
rs_df['W_RS_Avg'] = rs_df.apply(lambda r: sum(r[c] * 0.2 for c in rs_df.columns if pd.notna(r[c])), axis=1).round(
    0).astype('Int64')
rs_df['Ticker'] = rs_df.index
rs_df['Company Name'] = rs_df['Ticker'].map(US_STOCKS_INFO)
rs_df['Sector'] = rs_df['Ticker'].map({t: s for s, ts in SECTOR_TICKERS.items() for t in ts})

#10주선 괴리율 추가
ma50 = close_prices.rolling(window=50).mean()
current_price = close_prices.iloc[-1]
ma50_latest = ma50.iloc[-1]

disparity =((current_price/ ma50_latest) -1) *100
rs_df['Disparity(%)'] = disparity.astype(float).round(1)
# =========================================================================
# 4. 정렬 및 표 출력 (기존 유지)
# =========================================================================
sort_col = 'W_RS_Avg' if USER_RS_SORT_ORDER == 'a' else f'RS_{USER_RS_SORT_ORDER}D'
final_df = rs_df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)
final_df.index = final_df.index + 1

cols = ['Ticker', 'Company Name', 'RS_180D', 'RS_90D', 'RS_60D', 'RS_30D', 'RS_10D', 'W_RS_Avg', 'Disparity(%)', 'Sector']
table_output = tabulate(final_df[cols], headers='keys', tablefmt='pipe', numalign='center', stralign='left')

line_length = len(table_output.split('\n')[0])
print("\n" + "=" * line_length)
print(f"🇺🇸 US Relative Strength (RS) Ranking Analysis")
print(f"📊 {INDEX_TICKER} Returns: " + " | ".join([f"{k}D: {v}%" for k, v in idx_rets.items()]))
print(f"⚖️ Weights: 180D~10D (Equal 20%)")
print("=" * line_length)
print(table_output)
print("=" * line_length)

# =========================================================================
# 5. [수정] 그래프 생성 (임시 메모리 사용 방식)
# =========================================================================
print("\n🇺🇸 {미국 주식} 모든 기간 RS 데이터 전송 시작...")

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
            "rs_180": int(row['RS_180D']), # 기간별 데이터 추가
            "rs_90": int(row['RS_90D']),
            "rs_60": int(row['RS_60D']),
            "rs_30": int(row['RS_30D']),
            "rs_10": int(row['RS_10D']),
            "rs_avg": int(row['W_RS_Avg']),
            "disparity": float(row['Disparity(%)'])
        })
    
    db.collection('rs_data').document('us_latest').set({
        "update_time": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "sort_standard": USER_RS_SORT_ORDER,
        "rankings": us_rank_list
    })
    
    print("\n" + "="*50)
    print("✅ [미국 주식] rs_data/us_latest 업데이트 완료!")
    print("=" *50)
except Exception as e:
    print(f"\n❌ 전송 실패: {e}")