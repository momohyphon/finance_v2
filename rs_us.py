import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import FinanceDataReader as fdr
import sys
import os
import firebase_admin
from firebase_admin import credentials, firestore
import json
import pytz

# =========================================================================
# 0. 한국 시간(KST) 설정
# =========================================================================
kst = pytz.timezone('Asia/Seoul')
now_kst = datetime.now(kst)
END_DATE = now_kst.strftime('%Y-%m-%d')
NOW_STR = now_kst.strftime('%Y-%m-%d %H:%M')

# =========================================================================
# 1. 설정 및 종목 리스트
# =========================================================================
INDEX_TICKER = 'SPY'
RS_PERIODS = [180, 90, 60, 30, 10]

US_STOCKS_INFO = {
    # 원전 & 에너지
    'GEV': 'GE Vernova Inc.', 'OKLO': 'Oklo Inc.', 'SMR': 'NuScale Power Corp.',
    'BWXT': 'BWX Technologies', 'VST': 'Vistra Corp.', 'TLN': 'Talen Energy Corp.',
    'CEG': 'Constellation Energy', 'CVX': 'Chevron Corporation', 'XOM': 'Exxon Mobil',
    
    # 반도체 & 빅테크
    'NVDA': 'NVIDIA Corp.', 'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corp.',
    'GOOGL': 'Alphabet Inc. (A)', 'AMZN': 'Amazon.com Inc.', 'META': 'Meta Platforms',
    'TSLA': 'Tesla, Inc.', 'AVGO': 'Broadcom Inc.', 'ASML': 'ASML Holding',
    'AMD': 'Advanced Micro Devices', 'MU': 'Micron Technology', 'AMAT': 'Applied Materials',
    'LRCX': 'Lam Research', 'KLAC': 'KLA Corporation', 'QCOM': 'Qualcomm Inc.',
    'TXN': 'Texas Instruments', 'INTU': 'Intuit Inc.', 'ADBE': 'Adobe Inc.',
    'PANW': 'Palo Alto Networks', 'SNPS': 'Synopsys, Inc.', 'CDNS': 'Cadence Design Systems',
    'ORCL': 'Oracle Corporation', 'CRM': 'Salesforce, Inc.', 'NFLX': 'Netflix, Inc.', 'IBM': 'IBM Corporation',
    
    # 제약 & 바이오
    'LLY': 'Eli Lilly & Co.', 'JNJ': 'Johnson & Johnson', 'ABBV': 'AbbVie Inc.',
    'MRK': 'Merck & Co.', 'PFE': 'Pfizer Inc.', 'MRNA': 'Moderna, Inc.',
    'VRTX': 'Vertex Pharma', 'REGN': 'Regeneron Pharma', 'ISRG': 'Intuitive Surgical',
    'GILD': 'Gilead Sciences', 'UNH': 'UnitedHealth Group',
    
    # 금융 & 소비재
    'JPM': 'JPMorgan Chase', 'V': 'Visa Inc.', 'MA': 'Mastercard Inc.',
    'WMT': 'Walmart Inc.', 'PG': 'Procter & Gamble', 'COST': 'Costco Wholesale',
    'HD': 'Home Depot', 'KO': 'Coca-Cola Company', 'PEP': 'PepsiCo, Inc.',
    'DIS': 'Walt Disney', 'GS': 'Goldman Sachs', 'AXP': 'American Express',
    
    # 산업재 & 원재료
    'FCX': 'Freeport-McMoRan', 'ALB': 'Albemarle Corp.', 'NEM': 'Newmont Corp.',
    'RIO': 'Rio Tinto', 'DOW': 'Dow Inc.', 'LIN': 'Linde plc',
    'RTX': 'RTX Corporation', 'LMT': 'Lockheed Martin', 'DE': 'John Deere & Co.',
    'GE': 'General Electric', 'BA': 'Boeing Company', 'CAT': 'Caterpillar Inc.', 'HON': 'Honeywell International'
}

SECTOR_TICKERS = {
    'Nuclear/Energy': ['GEV', 'OKLO', 'SMR', 'BWXT', 'VST', 'TLN', 'CEG', 'CVX', 'XOM'],
    'Tech/Semi': ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'META', 'AVGO', 'ASML', 'AMD', 'MU', 'AMAT', 'LRCX', 'KLAC', 'QCOM', 'TXN', 'INTU', 'ADBE', 'PANW', 'SNPS', 'CDNS', 'ORCL', 'CRM', 'NFLX', 'IBM'],
    'Healthcare': ['LLY', 'JNJ', 'ABBV', 'MRK', 'PFE', 'MRNA', 'VRTX', 'REGN', 'ISRG', 'GILD', 'UNH'],
    'Consumer/Finance': ['AMZN', 'TSLA', 'WMT', 'PG', 'COST', 'HD', 'KO', 'PEP', 'DIS', 'JPM', 'V', 'MA', 'GS', 'AXP'],
    'Industrials/Materials': ['FCX', 'ALB', 'NEM', 'RIO', 'DOW', 'LIN', 'RTX', 'LMT', 'DE', 'GE', 'BA', 'CAT', 'HON']
}

ALL_US_TICKERS = list(US_STOCKS_INFO.keys())

USER_RS_SORT_ORDER = 'a'

# =========================================================================
# 2. 데이터 다운로드
# =========================================================================
START_DATE_STR = (now_kst - timedelta(days=max(RS_PERIODS) * 2)).strftime('%Y-%m-%d')
print(f"💰 미국 데이터 다운로드 중... (Index: {INDEX_TICKER} / 기준일: {NOW_STR})")

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
# 3. RS 산식 적용 (✅ 수정됨)
# =========================================================================
def calculate_rs_fixed(period, stocks, index):
    """
    상대강도(RS) 계산 함수 - 수정 버전
    - 시장 대비 초과수익률 사용
    - 초과수익 → 양수, 부진 → 음수
    """
    if len(stocks) < period + 1 or len(index) < period + 1:
        return pd.Series(np.nan, index=stocks.columns), 0
    
    # 수익률 계산
    s_ret = (stocks.iloc[-1] / stocks.iloc[-(period + 1)]) - 1  # 주식 수익률
    i_ret = (index.iloc[-1] / index.iloc[-(period + 1)]) - 1    # 지수 수익률
    
    # ✅ 초과수익률 (단순 뺄셈)
    rs_val = s_ret - i_ret
    
    # 순위를 백분위로 변환 후 1-99점으로 스케일링
    ranks = pd.Series(rs_val, index=stocks.columns).rank(pct=True)
    scores = (ranks * 98 + 1).round(0).astype('Int64')
    
    return scores, round(i_ret * 100, 1)

rs_results = {}
for p in RS_PERIODS:
    scores, _ = calculate_rs_fixed(p, close_prices, index_prices)
    rs_results[f'RS_{p}D'] = scores

rs_df = pd.DataFrame(rs_results)

# 가중평균 계산
rs_df['W_RS_Avg'] = rs_df.apply(
    lambda r: sum(r[c] * 0.2 for c in rs_df.columns if pd.notna(r[c])), 
    axis=1
).round(0).astype('Int64')

rs_df['Ticker'] = rs_df.index
rs_df['Company Name'] = rs_df['Ticker'].map(US_STOCKS_INFO)

# 이격도 계산
ma50_latest = close_prices.rolling(window=50).mean().iloc[-1]
rs_df['Disparity(%)'] = ((close_prices.iloc[-1] / ma50_latest) - 1) * 100
rs_df['Disparity(%)'] = rs_df['Disparity(%)'].astype(float).round(1)

final_df = rs_df.sort_values(by='W_RS_Avg', ascending=False).reset_index(drop=True)
final_df.index = final_df.index + 1

# =========================================================================
# 4. 파이어베이스 전송 및 로컬 파일 저장
# =========================================================================
print(f"\n🇺🇸 [미국 RS] 데이터 전송 및 파일 생성 시작 (시간: {NOW_STR})")

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
    
    final_payload = {
        "update_time": NOW_STR,
        "sort_standard": USER_RS_SORT_ORDER,
        "rankings": us_rank_list
    }

    # 1. 파이어베이스 업로드
    db.collection('rs_data').document('us_latest').set(final_payload)
    
    # 2. 로컬 파일 저장
    with open('rs_us.json', 'w', encoding='utf-8') as f:
        json.dump(final_payload, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ [미국 RS] 파이어베이스 및 rs_us.json 저장 완료! (KST: {NOW_STR})")

except Exception as e:
    print(f"\n❌ 전송 실패: {e}")