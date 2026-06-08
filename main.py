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


def draw_return_bar(ret_dict, title, margin_l=160):
    if not ret_dict:
        return go.Figure()
    ret_df = (
        pd.DataFrame.from_dict(ret_dict, orient="index", columns=["수익률(%)"])
        .sort_values("수익률(%)", ascending=True)
    )
    colors = ["#FF4B4B" if v >= 0 else "#0068C9" for v in ret_df["수익률(%)"]]
    fig = go.Figure(go.Bar(
        x=ret_df["수익률(%)"],
        y=ret_df.index,
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.2f}%" for v in ret_df["수익률(%)"]],
        textposition="outside",
    ))
    fig.update_layout(
        title=title,
        height=max(300, len(ret_df) * 50),
        template="plotly_white",
        xaxis_title="수익률 (%)",
        margin=dict(l=margin_l, r=100),
    )
    return fig


# ════════════════════════════════════════════════════════════
# 탭 구성
# ════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 개별 종목 분석",
    "📊 한국 주요 주식 비교",
    "🌎 미국 주요 주식 비교",
    "🆚 한·미 지수 비교",
])

# ════════════════════════════════════════════════════════════
# TAB 1 — 개별 종목 분석
# ════════════════════════════════════════════════════════════
with tab1:
    st.subheader("🔍 개별 종목 상세 분석")

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        market_choice = st.selectbox(
            "📌 시장 선택",
            ["한국 주식 (KOSPI)", "미국 주식 (US)", "직접 입력"],
            key="t1_market"
        )
    with c2:
        if market_choice == "한국 주식 (KOSPI)":
            sname = st.selectbox("종목 선택", list(KOREAN_STOCKS.keys()), key="t1_ks")
            sel_ticker = KOREAN_STOCKS[sname]
        elif market_choice == "미국 주식 (US)":
            sname = st.selectbox("종목 선택", list(US_STOCKS.keys()), key="t1_us")
            sel_ticker = US_STOCKS[sname]
        else:
            sel_ticker = st.text_input(
                "티커 입력 (예: AAPL, 005930.KS)",
                value="AAPL", key="t1_manual"
            ).upper().strip()
            sname = sel_ticker
    with c3:
        period_t1 = st.selectbox(
            "📅 기간", list(PERIOD_OPTIONS.keys()), index=3, key="t1_period"
        )

    with st.expander("📐 이동평균선 설정"):
        ma1, ma2, ma3, ma4 = st.columns(4)
        show_ma5   = ma1.checkbox("5일",   value=True,  key="ma5")
        show_ma20  = ma2.checkbox("20일",  value=True,  key="ma20")
        show_ma60  = ma3.checkbox("60일",  value=False, key="ma60")
        show_ma120 = ma4.checkbox("120일", value=False, key="ma120")

    with st.spinner(f"📡 {sel_ticker} 데이터 불러오는 중..."):
        df, info, err = load_single_stock(sel_ticker, PERIOD_OPTIONS[period_t1])

    if err or df is None:
        st.error(f"❌ 데이터를 불러올 수 없습니다: {err}")
    else:
        company_name  = info.get("longName", sname) if info else sname
        current_price = df["Close"].iloc[-1]
        prev_price    = df["Close"].iloc[-2]
        chg           = current_price - prev_price
        pct           = (chg / prev_price) * 100
        total_ret     = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100

        st.markdown(f"### 🏢 {company_name} `{sel_ticker}`")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("💰 현재가", f"{current_price:,.2f}", f"{chg:+.2f} ({pct:+.2f}%)")
        m2.metric("📈 기간 최고가", f"{df['High'].max():,.2f}")
        m3.metric("📉 기간 최저가", f"{df['Low'].min():,.2f}")
        m4.metric("📊 평균 거래량", f"{df['Volume'].mean():,.0f}")
        m5.metric("📈 기간 수익률", f"{total_ret:+.2f}%")

        st.divider()

        df = df.copy()
        df["MA5"]   = df["Close"].rolling(5).mean()
        df["MA20"]  = df["Close"].rolling(20).mean()
        df["MA60"]  = df["Close"].rolling(60).mean()
        df["MA120"] = df["Close"].rolling(120).mean()

        fig_candle = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.04, row_heights=[0.72, 0.28],
            subplot_titles=("주가 차트 (캔들스틱)", "거래량")
        )
        fig_candle.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"], high=df["High"],
                low=df["Low"],   close=df["Close"],
                name="주가",
                increasing_line_color="#FF4B4B",
                decreasing_line_color="#0068C9",
            ), row=1, col=1
        )
        ma_cfg = [
            ("MA5",   show_ma5,   "#FFA500", "5일 MA"),
            ("MA20",  show_ma20,  "#1E90FF", "20일 MA"),
            ("MA60",  show_ma60,  "#32CD32", "60일 MA"),
            ("MA120", show_ma120, "#9400D3", "120일 MA"),
        ]
        for col_nm, show, color, label in ma_cfg:
            if show:
                fig_candle.add_trace(
                    go.Scatter(
                        x=df.index, y=df[col_nm],
                        name=label, line=dict(color=color, width=1.5)
                    ), row=1, col=1
                )
        vol_colors = [
            "#FF4B4B" if c >= o else "#0068C9"
            for c, o in zip(df["Close"], df["Open"])
        ]
        fig_candle.add_trace(
            go.Bar(
                x=df.index, y=df["Volume"],
                name="거래량", marker_color=vol_colors, opacity=0.7
            ), row=2, col=1
        )
        fig_candle.update_layout(
            height=620, template="plotly_white",
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_candle, use_container_width=True)

        df["Daily_Ret"] = df["Close"].pct_change()
        df["Cum_Ret"]   = (1 + df["Daily_Ret"]).cumprod() - 1

        fig_ret = make_subplots(
            rows=1, cols=2,
            subplot_titles=("📈 누적 수익률 (%)", "📊 일별 수익률 분포")
        )
        fig_ret.add_trace(
            go.Scatter(
                x=df.index, y=df["Cum_Ret"] * 100,
                fill="tozeroy", name="누적 수익률",
                line=dict(color="#FF4B4B"),
                fillcolor="rgba(255,75,75,0.15)",
            ), row=1, col=1
        )
        fig_ret.add_trace(
            go.Histogram(
                x=df["Daily_Ret"].dropna() * 100,
                nbinsx=40, name="일별 수익률",
                marker_color="#0068C9", opacity=0.75,
            ), row=1, col=2
        )
        fig_ret.update_layout(height=360, template="plotly_white", showlegend=False)
        fig_ret.update_xaxes(title_text="날짜",       row=1, col=1)
        fig_ret.update_xaxes(title_text="수익률 (%)", row=1, col=2)
        fig_ret.update_yaxes(title_text="수익률 (%)", row=1, col=1)
        fig_ret.update_yaxes(title_text="빈도",        row=1, col=2)
        st.plotly_chart(fig_ret, use_container_width=True)

        st.subheader("📋 리스크 · 수익률 요약")
        dr     = df["Daily_Ret"].dropna()
        mean_r = dr.mean() * 100
        std_r  = dr.std()  * 100
        sharpe = (mean_r / std_r) * (252 ** 0.5) if std_r != 0 else 0
        mdd    = ((df["Close"] / df["Close"].cummax()) - 1).min() * 100
        ann_r  = ((1 + dr.mean()) ** 252 - 1) * 100

        rr1, rr2, rr3 = st.columns(3)
        rr1.info(f"""
**📈 수익률**
- 기간 누적 수익률: **{total_ret:+.2f}%**
- 연환산 수익률: **{ann_r:+.2f}%**
- 일평균 수익률: **{mean_r:+.4f}%**
        """)
        rr2.info(f"""
**⚡ 리스크**
- 일 변동성 (표준편차): **{std_r:.4f}%**
- 최대 낙폭 (MDD): **{mdd:.2f}%**
- 총 거래일: **{len(df)}일**
        """)
        rr3.info(f"""
**🏆 종합 지표**
- 샤프 지수 (연환산): **{sharpe:.2f}**
- 상승일 비율: **{(dr > 0).mean()*100:.1f}%**
- 하락일 비율: **{(dr < 0).mean()*100:.1f}%**
        """)

        st.subheader("📄 최근 10일 주가 데이터")
        recent = df[["Open","High","Low","Close","Volume"]].tail(10).copy()
        recent.index = recent.index.strftime("%Y-%m-%d")
        recent.columns = ["시가","고가","저가","종가","거래량"]
        st.dataframe(recent.round(2), use_container_width=True)

        csv = df[["Open","High","Low","Close","Volume"]].to_csv().encode("utf-8-sig")
        st.download_button(
            "⬇️ 전체 데이터 CSV 다운로드",
            csv, f"{sel_ticker}_data.csv", "text/csv"
        )

# ════════════════════════════════════════════════════════════
# TAB 2 — 한국 주요 주식 수익률 비교 (✅ 전체 자동 표시)
# ════════════════════════════════════════════════════════════
with tab2:
    st.subheader("📊 한국 주요 주식 수익률 비교")

    # ✅ 기간만 선택 가능 / 종목은 전체 자동
    period_t2 = st.selectbox(
        "📅 기간 선택", list(PERIOD_OPTIONS.keys()), index=3, key="t2_period"
    )

    # ✅ 모든 한국 종목 자동 로드
    ks_tickers  = list(KOREAN_STOCKS.values())
    ks_name_map = {v: k for k, v in KOREAN_STOCKS.items()}

    with st.spinner("📡 한국 주식 전체 데이터 불러오는 중... (잠시 기다려주세요)"):
        ks_close, err_ks = load_multiple_stocks(ks_tickers, PERIOD_OPTIONS[period_t2])

    if err_ks or ks_close is None:
        st.error(f"❌ {err_ks}")
    else:
        ks_close = ks_close.rename(columns=ks_name_map)
        ks_close = ks_close.dropna(how="all")

        # 정규화 수익률 차트
        ks_norm = calc_normalized(ks_close)
        colors  = px.colors.qualitative.Set1 + px.colors.qualitative.Set2

        fig_ks = go.Figure()
        for i, col in enumerate(ks_norm.columns):
            fig_ks.add_trace(go.Scatter(
                x=ks_norm.index, y=ks_norm[col],
                name=col,
                line=dict(width=2, color=colors[i % len(colors)])
            ))
        fig_ks.add_hline(y=100, line_dash="dash", line_color="gray",
                         annotation_text="기준 (시작=100)")
        fig_ks.update_layout(
            title="📈 한국 주요 주식 정규화 수익률 (시작=100)",
            height=600, template="plotly_white",
            xaxis_title="날짜", yaxis_title="정규화 가격 (시작=100)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.4)
        )
        st.plotly_chart(fig_ks, use_container_width=True)

        # 수익률 랭킹 바 차트
        ks_ret = {}
        for col in ks_close.columns:
            s = ks_close[col].dropna()
            if len(s) >= 2:
                ks_ret[col] = round((s.iloc[-1] / s.iloc[0] - 1) * 100, 2)

        st.plotly_chart(
            draw_return_bar(ks_ret, "🏆 한국 주식 기간 수익률 랭킹"),
            use_container_width=True
        )

        # 요약 테이블
        st.subheader("📋 종목별 요약 테이블")
        rows = [calc_summary(ks_close[c], c) for c in ks_close.columns]
        rows = [r for r in rows if r]
        if rows:
            st.dataframe(
                pd.DataFrame(rows).set_index("종목"),
                use_container_width=True
            )

# ════════════════════════════════════════════════════════════
# TAB 3 — 미국 주요 주식 수익률 비교 (✅ 전체 자동 표시)
# ════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🌎 미국 주요 주식 수익률 비교")

    # ✅ 기간만 선택 가능 / 종목은 전체 자동
    period_t3 = st.selectbox(
        "📅 기간 선택", list(PERIOD_OPTIONS.keys()), index=3, key="t3_period"
    )

    # ✅ 모든 미국 종목 자동 로드
    us_tickers  = list(US_STOCKS.values())
    us_name_map = {v: k for k, v in US_STOCKS.items()}

    with st.spinner("📡 미국 주식 전체 데이터 불러오는 중... (잠시 기다려주세요)"):
        us_close, err_us = load_multiple_stocks(us_tickers, PERIOD_OPTIONS[period_t3])

    if err_us or us_close is None:
        st.error(f"❌ {err_us}")
    else:
        us_close = us_close.rename(columns=us_name_map)
        us_close = us_close.dropna(how="all")

        # 정규화 수익률 차트
        us_norm   = calc_normalized(us_close)
        colors_us = px.colors.qualitative.Plotly + px.colors.qualitative.Dark2

        fig_us = go.Figure()
        for i, col in enumerate(us_norm.columns):
            fig_us.add_trace(go.Scatter(
                x=us_norm.index, y=us_norm[col],
                name=col,
                line=dict(width=2, color=colors_us[i % len(colors_us)])
            ))
        fig_us.add_hline(y=100, line_dash="dash", line_color="gray",
                         annotation_text="기준 (시작=100)")
        fig_us.update_layout(
            title="📈 미국 주요 주식 정규화 수익률 (시작=100)",
            height=600, template="plotly_white",
            xaxis_title="날짜", yaxis_title="정규화 가격 (시작=100)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.4)
        )
        st.plotly_chart(fig_us, use_container_width=True)

        # 수익률 랭킹 바 차트
        us_ret = {}
        for col in us_close.columns:
            s = us_close[col].dropna()
            if len(s) >= 2:
                us_ret[col] = round((s.iloc[-1] / s.iloc[0] - 1) * 100, 2)

        st.plotly_chart(
            draw_return_bar(us_ret, "🏆 미국 주식 기간 수익률 랭킹", margin_l=220),
            use_container_width=True
        )

        # 요약 테이블
        st.subheader("📋 종목별 요약 테이블")
        us_rows = [calc_summary(us_close[c], c) for c in us_close.columns]
        us_rows = [r for r in us_rows if r]
        if us_rows:
            st.dataframe(
                pd.DataFrame(us_rows).set_index("종목"),
                use_container_width=True
            )

# ════════════════════════════════════════════════════════════
# TAB 4 — 한·미 지수 비교 (✅ 전체 자동 표시)
# ════════════════════════════════════════════════════════════
with tab4:
    st.subheader("🆚 한국 · 미국 주요 지수 비교")

    # ✅ 기간만 선택 가능 / 지수는 전체 자동
    period_t4 = st.selectbox(
        "📅 기간 선택", list(PERIOD_OPTIONS.keys()), index=3, key="t4_period"
    )

    # ✅ 모든 지수 자동 로드
    idx_tickers  = list(INDEX_STOCKS.values())
    idx_name_map = {v: k for k, v in INDEX_STOCKS.items()}

    with st.spinner("📡 지수 데이터 불러오는 중..."):
        idx_close, err_idx = load_multiple_stocks(idx_tickers, PERIOD_OPTIONS[period_t4])

    if err_idx or idx_close is None:
        st.error(f"❌ {err_idx}")
    else:
        idx_close = idx_close.rename(columns=idx_name_map)
        idx_close = idx_close.dropna(how="all")

        idx_norm   = calc_normalized(idx_close)
        idx_colors = ["#FF4B4B", "#0068C9", "#FFA500", "#32CD32", "#9400D3"]

        fig_idx = go.Figure()
        for i, col in enumerate(idx_norm.columns):
            fig_idx.add_trace(go.Scatter(
                x=idx_norm.index, y=idx_norm[col],
                name=col,
                line=dict(width=2.5, color=idx_colors[i % len(idx_colors)])
            ))
        fig_idx.add_hline(y=100, line_dash="dash", line_color="gray",
                          annotation_text="기준 (시작=100)")
        fig_idx.update_layout(
            title="🌍 한·미 주요 지수 정규화 비교 (시작=100)",
            height=500, template="plotly_white",
            xaxis_title="날짜", yaxis_title="정규화 지수 (시작=100)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3)
        )
        st.plotly_chart(fig_idx, use_container_width=True)

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📊 지수 수익률 요약")
            idx_rows = [calc_summary(idx_close[c], c) for c in idx_close.columns]
            idx_rows = [r for r in idx_rows if r]
            if idx_rows:
                idx_sum = pd.DataFrame(idx_rows).set_index("종목")
                idx_sum.index.name = "지수"
                st.dataframe(idx_sum, use_container_width=True)

        with col_right:
            st.subheader("🔗 지수 간 상관관계")
            ret_corr = idx_close.pct_change().dropna()
            if ret_corr.shape[1] >= 2:
                corr = ret_corr.corr().round(3)
                fig_corr = go.Figure(go.Heatmap(
                    z=corr.values,
                    x=corr.columns.tolist(),
                    y=corr.index.tolist(),
                    colorscale="RdYlGn",
                    zmin=-1, zmax=1,
                    text=corr.values.round(2),
                    texttemplate="%{text}",
                    textfont=dict(size=13),
                ))
                fig_corr.update_layout(
                    height=350, template="plotly_white",
                    title="상관관계 히트맵"
                )
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("ℹ️ 상관관계는 2개 이상의 지수가 필요합니다.")

# ── 푸터
st.divider()
st.caption(
    "📌 본 앱은 교육 목적으로 제작되었습니다. "
    "투자 결정에 활용하지 마세요. | 데이터 출처: Yahoo Finance"
)
