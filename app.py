import streamlit as st
import yfinance as yf
import pandas as pd
import FinanceDataReader as fdr

st.set_page_config(page_title="적정주가 산출 대시보드", layout="wide")

st.title("📊 가치투자 핵심 재무지표 분석기")
st.markdown("---")

@st.cache_data
def load_krx_data():
    df = fdr.StockListing('KRX')
    return df[['Code', 'Name', 'Market']]

krx_df = load_krx_data()

st.sidebar.header("🔍 검색 설정")
user_input = st.sidebar.text_input(
    "기업명을 입력하세요 (띄어쓰기로 구분)", 
    value="삼성전자 현대차"
)

input_list = user_input.replace(',', ' ').split()

def get_yf_ticker(name_or_code):
    if name_or_code.isdigit() and len(name_or_code) == 6:
        matched = krx_df[krx_df['Code'] == name_or_code]
    else:
        matched = krx_df[krx_df['Name'] == name_or_code]
    
    if not matched.empty:
        code = matched.iloc[0]['Code']
        market = matched.iloc[0]['Market']
        name = matched.iloc[0]['Name']
        suffix = ".KS" if market == 'KOSPI' else ".KQ"
        return f"{code}{suffix}", name
    return None, name_or_code

# 재무제표 안전 추출 함수
def get_financial_value(df, key):
    try:
        return df.loc[key].iloc[0] # 가장 최근 결산 연도 데이터
    except:
        return None

if st.sidebar.button("데이터 조회 시작"):
    if not input_list:
        st.warning("조회할 기업명을 입력해주세요.")
    else:
        financial_data = []
        
        with st.spinner('재무 데이터를 정밀 분석 중입니다. 잠시만 기다려주세요...'):
            for item in input_list:
                ticker, company_name = get_yf_ticker(item.strip())
                
                if ticker is None:
                    st.error(f"'{item}' 기업을 찾을 수 없습니다.")
                    continue
                    
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    bs = stock.balance_sheet
                    fin = stock.financials
                    
                    # 1. 기본 지표 추출
                    eps = info.get('trailingEps')
                    roe = info.get('returnOnEquity')
                    bps = info.get('bookValue')
                    
                    # 2. 재무제표 항목 추출
                    current_assets = get_financial_value(bs, 'Current Assets')
                    total_liabilities = get_financial_value(bs, 'Total Liabilities Net Minor Interest')
                    total_equity = get_financial_value(bs, 'Stockholders Equity')
                    net_income = get_financial_value(fin, 'Net Income')
                    
                    # 3. 파생 지표 계산
                    eps_10 = (eps * 10) if eps else None
                    roe_eps = (roe * 100 * eps) if (roe is not None and eps is not None) else None
                    
                    # 4. 데이터셋 구성
                    data = {
                        "기업명": company_name,
                        "유동자산(억)": f"{current_assets // 100000000:,}" if current_assets else "N/A",
                        "총부채(억)": f"{total_liabilities // 100000000:,}" if total_liabilities else "N/A",
                        "목표주가(원)": f"{info.get('targetMeanPrice', 0):,.0f}" if info.get('targetMeanPrice') else "N/A",
                        "BPS(원)": f"{bps:,.0f}" if bps else "N/A",
                        "EPS*10": f"{eps_10:,.0f}" if eps_10 else "N/A",
                        "ROE*EPS": f"{roe_eps:,.0f}" if roe_eps else "N/A",
                        "현재 PER": info.get('trailingPE', 'N/A'),
                        "PBR": info.get('priceToBook', 'N/A'),
                        "EPS(원)": f"{eps:,.0f}" if eps else "N/A",
                        "ROE(%)": f"{roe * 100:.2f}%" if roe else "N/A",
                        "당기순이익(억)": f"{net_income // 100000000:,}" if net_income else "N/A",
                        "자기자본(억)": f"{total_equity // 100000000:,}" if total_equity else "N/A"
                    }
                    financial_data.append(data)
                except Exception as e:
                    st.error(f"{company_name} 데이터를 가져오는 중 오류가 발생했습니다.")

        # 5. 결과 출력 테이블
        if financial_data:
            st.subheader("📌 핵심 투자 지표 분석 결과")
            df = pd.DataFrame(financial_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption("※ 금액 단위가 큰 재무 항목(자산, 부채, 순이익 등)은 가독성을 위해 '억원' 단위로 표기했습니다.")
            st.caption("※ 목표주가는 야후 파이낸스에서 제공하는 애널리스트 평균 컨센서스를 활용합니다.")
        else:
            st.info("검색 결과가 없습니다.")
else:
    st.info("왼쪽 사이드바에서 기업명을 입력하고 '데이터 조회 시작' 버튼을 눌러주세요.")
