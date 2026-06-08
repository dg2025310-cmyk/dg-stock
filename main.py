import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# ── 페이지 설정
st.set_page_config(
    page_title="한국 · 미국 주식 분석",
    page_icon="📈",
    layout="wide"
)

# ── CSS 스타일
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #FF4B4B, #0068C9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        text-align: center;
        color: gray;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-title">📈 한국 · 미국 주식 분석 대시보드</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="sub-title">yfinance 기반 실시간 주가 데이터 분석</div>',
    unsafe_allow_html=True
)
st.divider()

# ── 종목 딕셔너리
KOREAN_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "POSCO홀딩스": "005490.KS",
    "카카오": "035720.KS",
    "네이버": "035420.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "LG화학": "051910.KS",
    "현대모비스": "012330.KS",
    "삼성SDI": "006400.KS",
}

US_STOCKS = {
    "애플 (AAPL)": "AAPL",
    "마이크로소프트 (MSFT)": "MSFT",
    "엔비디아 (NVDA)": "NVDA",
    "아마존 (AMZN)": "AMZN",
    "구글 (GOOGL)": "GOOGL",
    "메타 (META)": "META",
    "테슬라 (TSLA)": "TSLA",
    "JP모건 (JPM)": "JPM",
    "비자 (V)": "V",
    "존슨앤존슨 (JNJ)": "JNJ",
    "월마트 (WMT)": "WMT",
    "엑슨모빌 (XOM)": "XOM",
    "넷플릭스 (NFLX)": "NFLX",
    "AMD (AMD)": "AMD",
}

INDEX_STOCKS = {
    "S&P 500": "^GSPC",
    "나스닥": "^IXIC",
    "다우존스": "^DJI",
    "코스피": "^KS11",
    "코스닥": "^KQ11",
}

PERIOD_OPTIONS = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
}

# ════════════════════════════════════════════════════════════
# 데이터 로드 함수
# ════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_single_stock(ticker, period):
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period=period)
        if df is None or df.empty:
            return None, None, "데이터가 없습니다."
        df.index = df.index.tz_localize(None)
        info = {}
        try:
            info = tk.info
        except Exception:
            pass
        return df, info, None
    except Exception as e:
        return None, None, str(e)


@st.cache_data(ttl=300)
def load_multiple_stocks(tickers, period):
    result = {}
    for ticker in tickers:
        try:
            tk = yf.Ticker(ticker)
            df = tk.history(period=period)
            if df is not None and not df.empty:
                df.index = df.index.tz_localize(None)
                result[ticker] = df["Close"]
        except Exception:
            continue
    if not result:
        return None, "모든 종목 데이터 로드 실패"
    close_df = pd.DataFrame(result)
    return close_df, None


# ── 유틸 함수
def calc_normalized(df):
    df = df.copy().dropna(how="all")
    result = pd.DataFrame(index=df.index)
    for col in df.columns:
        s = df[col].dropna()
        if len(s) > 0:
            result[col] = df[col] / s.iloc[0] * 100
    return result


def calc_summary(series, name):
    s = series.dropna()
    if len(s) < 2:
        return {}
    dr = s.pct_change().dropna()
    if len(dr) == 0 or dr.std() == 0:
        return {}
    total_r  = (s.iloc[-1] / s.iloc[0] - 1) * 100
    ann_r    = ((1 + dr.mean()) ** 252 - 1) * 100
    vol      = dr.std() * 100
    mdd      = ((s / s.cummax()) - 1).min() * 100
    sharpe   = (dr.mean() / dr.std()) * (252 ** 0.5)
    up_ratio = (dr > 0).mean() * 100
    return {
        "종목": name,
        "현재가": f"{s.iloc[-1]:,.2f}",
        "기간 수익률": f"{total_r:+.2f}%",
        "연환산 수익률": f"{ann_r:+.2f}%",
        "일 변동성": f"{vol:.3f}%",
        "MDD": f"{mdd:.2f}%",
        "샤프 지수": f"{sharpe:.2f}",
        "상승일 비율": f"{up_ratio:.1f}%",
    }


def draw_return_bar(ret_dict, title, margin
