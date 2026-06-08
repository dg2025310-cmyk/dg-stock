import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 제목 설정
st.title("📊 나의 첫 번째 대시보드")
st.write("안녕하세요! Streamlit으로 만든 대시보드입니다.")

# 사이드바
st.sidebar.title("⚙️ 설정")
option = st.sidebar.selectbox(
    "보고 싶은 차트를 선택하세요",
    ["막대 그래프", "선 그래프", "산점도"]
)

# 샘플 데이터 생성
data = pd.DataFrame({
    "과목": ["국어", "영어", "수학", "과학", "사회"],
    "점수": [85, 90, 78, 92, 88]
})

# 선택에 따라 다른 차트 표시
if option == "막대 그래프":
    st.subheader("📊 막대 그래프")
    st.bar_chart(data.set_index("과목"))

elif option == "선 그래프":
    st.subheader("📈 선 그래프")
    st.line_chart(data.set_index("과목"))

elif option == "산점도":
    st.subheader("🔵 산점도")
    fig, ax = plt.subplots()
    ax.scatter(data["과목"], data["점수"], color="blue", s=100)
    ax.set_xlabel("과목")
    ax.set_ylabel("점수")
    st.pyplot(fig)

# 데이터 테이블 표시
st.subheader("📋 데이터 테이블")
st.dataframe(data)

# 통계 정보
st.subheader("📌 통계 정보")
col1, col2, col3 = st.columns(3)
col1.metric("평균 점수", f"{data['점수'].mean():.1f}점")
col2.metric("최고 점수", f"{data['점수'].max()}점")
col3.metric("최저 점수", f"{data['점수'].min()}점")
