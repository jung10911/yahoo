import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr

# 1. 페이지 설정 및 스타일
st.set_page_config(page_title="국내 상장사 재무 분석기", layout="wide")

# 가독성을 위한 상단 제목
st.title("📊 국내 기업 주요 재무정보 대시보드")
st.markdown("---")

# 2. KRX 종목 데이터 로드 (캐싱을 통해 속도 최적화)
@st.cache_data
def load_krx_data():
    df = fdr.StockListing('KRX')
    return df[['Code', 'Name', 'Market']]

krx_df = load_krx_data()

# 3. 사용자 입력 섹션
st.sidebar.header("🔍 검색 설정")
user_input = st.sidebar.text_input(
    "기업명을 입력하세요 (띄어쓰기로 구분)", 
    value="삼성전자 현대차 SK하이닉스"
)

# 쉼표나 공백 모두 대응할 수 있도록 처리
input_list = user_input.replace(',', ' ').split()

# 4. 티커 변환 함수 (야후 파이낸스 규격 맞춤)
def get_yf_ticker(name_or_code):
    if name_or_code.isdigit() and len(name_or_code) == 6:
        matched = krx_df[krx_df['Code'] == name_or_code]
    else:
        matched = krx_df[krx_df['Name'] == name_or_code]
    
    if not matched.empty:
        code = matched.iloc[0]['Code']
        market = matched.iloc[0]['Market']
        name = matched.iloc[0]['Name']
        # 코스피 .KS, 코스닥 .KQ 구분
        suffix = ".KS" if market == 'KOSPI' else ".KQ"
        return f"{code}{suffix}", name
    return None, name_or_code

# 5. 메인 로직 실행
if st.sidebar.button("데이터 조회 시작"):
    if not input_list:
        st.warning("조회할 기업명을 입력해주세요.")
    else:
        financial_data = []
        
        with st.spinner('데이터를 분석 중입니다...'):
            for item in input_list:
                ticker, company_name = get_yf_ticker(item.strip())
                
                if ticker is None:
                    st.error(f"'{item}' 기업을 찾을 수 없습니다.")
                    continue
                    
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    # [핵심] 배당수익률 직접 계산 로직 (야후 API 버그 보정)
                    curr_price = info.get('currentPrice')
                    div_rate = info.get('dividendRate')
                    
                    if curr_price and div_rate:
                        # 주당배당금 / 현재가 * 100
                        calculated_yield = (div_rate / curr_price) * 100
                        div_yield_display = f"{calculated_yield:.2f}%"
                    elif info.get('dividendYield'):
                        # 직접 계산 불가 시 차선책 (소수점 처리)
                        raw_yield = info.get('dividendYield')
                        val = raw_yield if raw_yield > 1 else raw_yield * 100
                        div_yield_display = f"{val:.2f}%"
                    else:
                        div_yield_display = "0.00%"

                    # 데이터 정리
                    data = {
                        "기업명": company_name,
                        "현재가": f"{curr_price:,}" if curr_price else "N/A",
                        "시가총액(억)": f"{info.get('marketCap', 0) // 100000000:,}" if info.get('marketCap') else "N/A",
                        "PER": info.get('forwardPE', 'N/A'),
                        "PBR": info.get('priceToBook', 'N/A'),
                        "ROE": f"{info.get('returnOnEquity', 0) * 100:.2f}%" if info.get('returnOnEquity') else "N/A",
                        "부채비율": f"{info.get('debtToEquity', 0):.2f}" if info.get('debtToEquity') else "N/A",
                        "배당수익률": div_yield_display
                    }
                    financial_data.append(data)
                except Exception:
                    st.error(f"{company_name} 데이터를 가져오는 중 오류가 발생했습니다.")

        # 6. 결과 출력 테이블
        if financial_data:
            st.subheader("📌 기업별 주요 지표 비교")
            df = pd.DataFrame(financial_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 7. 상세 재무제표 (최근 3개년 매출/이익)
            st.markdown("---")
            st.subheader("🔍 연간 실적 요약 (단위: 백만원)")
            
            cols = st.columns(len(financial_data))
            for i, data in enumerate(financial_data):
                with cols[i]:
                    st.write(f"**{data['기업명']}**")
                    try:
                        ticker_code, _ = get_yf_ticker(data['기업명'])
                        # 손익계산서 데이터 추출
                        income = yf.Ticker(ticker_code).financials.loc[['Total Revenue', 'Net Income']]
                        # 단위 조정 (원 -> 백만원) 및 라벨링
                        income = (income / 1000000).astype(float).round(0)
                        income.index = ['매출액', '순이익']
                        st.table(income.iloc[:, :3])
                    except:
                        st.caption("재무제표를 불러올 수 없습니다.")
        else:
            st.info("검색 결과가 없습니다.")
else:
    st.info("왼쪽 사이드바에서 기업명을 입력하고 버튼을 눌러주세요.")
