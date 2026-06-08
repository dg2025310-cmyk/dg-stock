import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

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

# ── 종목 딕셔너리 ─────────────────────────────────────────────
KOREAN_STOCKS = {
    "삼성전자":         "005930.KS",
    "SK하이닉스":       "000660.KS",
    "LG에너지솔루션":   "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차":           "005380.KS",
    "기아":             "000270.KS",
    "POSCO홀딩스":      "005
