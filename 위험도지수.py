import streamlit as st
import requests
from datetime import datetime
import numpy as np

# 🌡️ OpenWeather API 설정
API_KEY = "32ce12499c694975782b1fd761dc79c1"
CITY = "Incheon"
API_URL = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

# 📊 1월~12월 고정 기준 데이터 (엑셀 내용 반영)
monthly_data = {
    1: {"N": 55, "death_d": 2, "death_o": 0, "inj_d": 41, "inj_o": 44, "Tm": -1.5, "Hm": 68.8},
    2: {"N": 57, "death_d": 2, "death_o": 5, "inj_d": 33, "inj_o": 44, "Tm": -0.3, "Hm": 65.7},
    3: {"N": 72, "death_d": 3, "death_o": 1, "inj_d": 49, "inj_o": 27, "Tm": 4.8, "Hm": 65.7},
    4: {"N": 86, "death_d": 2, "death_o": 0, "inj_d": 52, "inj_o": 17, "Tm": 11.7, "Hm": 65.2},
    5: {"N": 102, "death_d": 5, "death_o": 1, "inj_d": 64, "inj_o": 6, "Tm": 17.2, "Hm": 63.8},
    6: {"N": 86, "death_d": 4, "death_o": 0, "inj_d": 50, "inj_o": 3, "Tm": 22.8, "Hm": 83.3},
    7: {"N": 128, "death_d": 3, "death_o": 1, "inj_d": 87, "inj_o": 4, "Tm": 25.6, "Hm": 83.8},
    8: {"N": 106, "death_d": 3, "death_o": 2, "inj_d": 94, "inj_o": 13, "Tm": 26.1, "Hm": 82.0},
    9: {"N": 81, "death_d": 4, "death_o": 1, "inj_d": 132, "inj_o": 36, "Tm": 20.1, "Hm": 83.3},
    10: {"N": 66, "death_d": 0, "death_o": 0, "inj_d": 66, "inj_o": 3, "Tm": 15.3, "Hm": 70.1},
    11: {"N": 78, "death_d": 6, "death_o": 0, "inj_d": 42, "inj_o": 15, "Tm": 7.0, "Hm": 67.8},
    12: {"N": 56, "death_d": 3, "death_o": 0, "inj_d": 86, "inj_o": 5, "Tm": 0.7, "Hm": 68.8}
}
# 📡 날씨 API 호출 함수
def get_weather():
    try:
        res = requests.get(API_URL)
        data = res.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        return temp, humidity
    except:
        return None, None

# ⚙️ 위험도 계산 함수
def calculate_risk(info, T, H):
    # 기준 데이터
    deaths = info["death_d"] + info["death_o"]
    injuries_direct = info["inj_d"]
    injuries_other = info["inj_o"]
    incidents = info["N"]
    Tm = info["Tm"]
    Hm = info["Hm"]

    alpha = 0.02  # 온도 민감도
    beta = 0.005  # 습도 민감도

    # BR: 기본 위험도
    score = deaths * 100 + injuries_direct * 40 + injuries_other * 10
    BR = score * (1 + 0.05 * incidents)

    # ER: 온도/습도 반영 위험도
    ER = score * (1 + alpha * (T - Tm) + beta * (H - Hm)) * (1 + 0.05 * incidents)

    # 위험지수: (ER - BR) / BR × 100 (%)
    risk_index = ((ER - BR) / BR) * 100

    # 위험지수는 최소 0%, 최대 100%로 클리핑
    risk_index = np.clip(risk_index, 0, 100)

    return round(BR, 1), round(ER, 1), round(risk_index, 1)

# 🔎 위험 해석 함수
def interpret_index(percent):
    if percent <= 5:
        return "🟢 정상 (조치 불필요)"
    elif percent <= 15:
        return "🟡 주의 (모니터링 강화)"
    elif percent <= 30:
        return "🟠 경계 (점검 필요)"
    else:
        return "🔴 심각 (즉각 조치)"

# 🌐 Streamlit 앱 시작
st.set_page_config(page_title="화학사고 위험지수", page_icon="☣️")
st.title("☣️ 유해화학물질 사고 예측 시스템")
st.caption(f"도시: {CITY} | OpenWeather 실시간 날씨 기반")

# 현재 월 정보
month = datetime.now().month
info = monthly_data[month]
st.markdown(f"### 📅 현재 기준 월: **{month}월**")

# 날씨 정보 불러오기
temp, humidity = get_weather()

if temp is None or humidity is None:
    st.error("❌ 날씨 데이터를 불러올 수 없습니다. API 키 또는 인터넷 연결을 확인해주세요.")
else:
    st.subheader("📡 현재 날씨")
    st.metric("🌡️ 현재온도 (°C)", f"{temp}")
    st.metric("💧 현재습도 (%)", f"{humidity}")

    # 위험도 계산
    br, er, risk_percent = calculate_risk(info, temp, humidity)

    st.subheader("☣️ 화학사고 위험도 분석")
    st.metric("기본위험도 (BR)", f"{br}")
    st.metric("온/습도 반영 위험도 (ER)", f"{er}")
    st.metric("화학사고 위험지수", f"{risk_percent} %")

    st.success(interpret_index(risk_percent))