import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr

# 페이지 설정
st.set_page_config(page_title="국내 상장사 재무 분석기", layout="wide")

# KRX 종목 데이터 캐싱 (매번 다운로드하지 않도록 속도 향상)
@st.cache_data
def load_krx_data():
    df = fdr.StockListing('KRX')
    return df[['Code', 'Name', 'Market']]

krx_df = load_krx_data()

st.title("📊 국내 기업 주요 재무정보 분석")
st.info("기업명(또는 6자리 종목코드)을 띄어쓰기로 구분하여 입력하세요. (예: 삼성전자 에코프로 로보티즈)")

# 1. 사용자 입력
user_input = st.text_input("기업명 입력", value="삼성전자 SK하이닉스 현대차")
input_list = user_input.replace(',', ' ').split()

# 기업명 -> yfinance 티커 변환 함수
def get_yf_ticker(name_or_code):
    # 입력값이 6자리 숫자인 경우 (코드 직접 입력)
    if name_or_code.isdigit() and len(name_or_code) == 6:
        matched = krx_df[krx_df['Code'] == name_or_code]
    else:
        # 기업명으로 검색
        matched = krx_df[krx_df['Name'] == name_or_code]
    
    if not matched.empty:
        code = matched.iloc[0]['Code']
        market = matched.iloc[0]['Market']
        
        # 야후 파이낸스용 티커 생성 (코스피: .KS, 코스닥: .KQ)
        if market == 'KOSPI':
            return f"{code}.KS", matched.iloc[0]['Name']
        elif market in ['KOSDAQ', 'KOSDAQ GLOBAL']:
            return f"{code}.KQ", matched.iloc[0]['Name']
        else:
            return f"{code}.KS", matched.iloc[0]['Name']
            
    return None, name_or_code

if st.button("데이터 가져오기"):
    if not input_list:
        st.warning("조회할 기업을 입력해주세요.")
    else:
        financial_data = []
        
        with st.spinner('데이터를 불러오는 중입니다...'):
            for item in input_list:
                ticker, company_name = get_yf_ticker(item)
                
                if ticker is None:
                    st.error(f"'{item}' 기업을 찾을 수 없습니다. 정확한 상장사명을 입력해주세요.")
                    continue
                    
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    # 국내 주식에 맞춘 핵심 재무 지표 추출
                    data = {
                        "기업명": company_name,
                        "종목코드": ticker.replace('.KS', '').replace('.KQ', ''),
                        "현재가(KRW)": f"{info.get('currentPrice', 0):,}" if info.get('currentPrice') else 'N/A',
                        "시가총액(억원)": f"{info.get('marketCap', 0) // 100000000:,}" if info.get('marketCap') else 'N/A',
                        "PER (Forward)": info.get('forwardPE', 'N/A'),
                        "PBR": info.get('priceToBook', 'N/A'),
                        "ROE": f"{info.get('returnOnEquity', 0) * 100:.2f}%" if info.get('returnOnEquity') else 'N/A',
                        "부채비율(D/E)": info.get('debtToEquity', 'N/A'),
                        "배당수익률": f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else 'N/A'
                    }
                    financial_data.append(data)
                except Exception as e:
                    st.error(f"{company_name} 데이터를 가져오는데 실패했습니다.")

        # 2. 데이터 출력
        if financial_data:
            df = pd.DataFrame(financial_data)
            st.subheader("📌 주요 재무 지표 비교")
            st.dataframe(df, use_container_width=True)
            
            st.divider()
            st.subheader("🔍 기업별 연간 손익계산서 요약")
            cols = st.columns(len(input_list))
            for i, item in enumerate(input_list):
                with cols[i]:
                    ticker, company_name = get_yf_ticker(item)
                    if ticker:
                        st.write(f"**{company_name}**")
                        try:
                            # 야후 파이낸스에서 매출과 순이익 정보 추출
                            income_stmt = yf.Ticker(ticker).financials.loc[['Total Revenue', 'Net Income']]
                            # 보기 편하게 단위 조정 (백만 원 단위로 변환)
                            income_stmt = (income_stmt / 1000000).astype(float).round(0)
                            income_stmt.index = ['매출액(백만원)', '당기순이익(백만원)']
                            st.table(income_stmt.iloc[:, :3]) 
                        except:
                            st.write("상세 재무 정보를 불러올 수 없습니다.")
