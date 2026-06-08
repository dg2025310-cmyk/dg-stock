import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="📈 한국 · 미국 주식 분석",
    page_icon="📈",
    layout="wide"
)

# ── CSS 스타일 ───────────────────────────────────────────────
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
    .card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── 제목 ─────────────────────────────────────────────────────
st.markdown('<div class="main-title">📈 한국 · 미국 주식 분석 대시보드</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">yfinance 기반 실시간 주가 데이터 분석</div>', unsafe_allow_html=True)
st.divider()

# ── 주요 종목 딕셔너리 ────────────────────────────────────────
KOREAN_STOCKS = {
    "삼성전자":     "005930.KS",
    "SK하이닉스":   "000660.KS",
    "LG에너지솔루션":"373220.KS",
    "삼성바이오로직스":"207940.KS",
    "현대차":       "005380.KS",
    "기아":         "000270.KS",
    "POSCO홀딩스":  "005490.KS",
    "카카오":       "035720.KS",
    "네이버(NAVER)":"035420.KS",
    "셀트리온":     "068270.KS",
    "KB금융":       "105560.KS",
    "신한지주":     "055550.KS",
    "LG화학":       "051910.KS",
    "현대모비스":   "012330.KS",
    "삼성SDI":      "006400.KS",
}

US_STOCKS = {
    "애플 (AAPL)":          "AAPL",
    "마이크로소프트 (MSFT)": "MSFT",
    "엔비디아 (NVDA)":       "NVDA",
    "아마존 (AMZN)":         "AMZN",
    "구글 (GOOGL)":          "GOOGL",
    "메타 (META)":           "META",
    "테슬라 (TSLA)":         "TSLA",
    "버크셔해서웨이 (BRK-B)":"BRK-B",
    "JP모건 (JPM)":          "JPM",
    "비자 (V)":              "V",
    "존슨앤존슨 (JNJ)":      "JNJ",
    "월마트 (WMT)":          "WMT",
    "엑슨모빌 (XOM)":        "XOM",
    "넷플릭스 (NFLX)":       "NFLX",
    "AMD (AMD)":             "AMD",
}

INDEX_STOCKS = {
    "
