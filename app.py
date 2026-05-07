import streamlit as st
import yfinance as yf
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="기업 재무정보 분석기", layout="wide")

st.title("📊 기업별 주요 재무정보 분석 (Yahoo Finance)")
st.info("기업 티커(Ticker)를 공백(스페이스)으로 구분하여 입력하세요. (예: TSLA AAPL NVDA)")

# 1. 사용자 입력 (쉼표 없이 공백으로도 가능하게 처리)
user_input = st.text_input("기업 티커 입력", value="AAPL TSLA MSFT")
tickers = user_input.replace(',', ' ').split() # 쉼표가 있어도, 없어도 작동하게 처리

if st.button("데이터 가져오기"):
    if not tickers:
        st.warning("조회할 티커를 입력해주세요.")
    else:
        financial_data = []
        
        with st.spinner('데이터를 불러오는 중입니다...'):
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker.upper())
                    info = stock.info
                    
                    # 핵심 재무 지표 추출
                    data = {
                        "기업명": info.get('shortName', 'N/A'),
                        "티커": ticker.upper(),
                        "현재가": f"{info.get('currentPrice', 0):,.2f} {info.get('currency', '')}",
                        "시가총액": f"{info.get('marketCap', 0):,}",
                        "PER (Forward)": info.get('forwardPE', 'N/A'),
                        "PBR": info.get('priceToBook', 'N/A'),
                        "ROE": f"{info.get('returnOnEquity', 0) * 100:.2;f}%" if info.get('returnOnEquity') else 'N/A',
                        "EPS (Trailing)": info.get('trailingEps', 'N/A'),
                        "부채비율(D/E)": info.get('debtToEquity', 'N/A'),
                        "배당수익률": f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else 'N/A'
                    }
                    financial_data.append(data)
                except Exception as e:
                    st.error(f"{ticker} 데이터를 가져오는데 실패했습니다: {e}")

        # 2. 데이터 출력
        if financial_data:
            df = pd.DataFrame(financial_data)
            st.subheader("📌 주요 재무 지표 비교")
            st.dataframe(df, use_container_width=True)
            
            # 개별 기업 상세 분석 (선택)
            st.divider()
            st.subheader("🔍 기업별 연간 손익계산서 요약")
            cols = st.columns(len(tickers))
            for i, ticker in enumerate(tickers):
                with cols[i]:
                    st.write(f"**{ticker.upper()}**")
                    try:
                        income_stmt = yf.Ticker(ticker).financials.loc[['Total Revenue', 'Net Income']]
                        st.table(income_stmt.iloc[:, :3]) # 최근 3개년치
                    except:
                        st.write("재무제표 정보를 불러올 수 없습니다.")
