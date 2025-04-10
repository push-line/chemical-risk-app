import streamlit as st
import requests
import numpy as np
import pandas as pd
import datetime

# 📌 API 키 및 도시 설정
API_KEY = "32ce12499c694975782b1fd761dc79c1"

# 📌 도시 정보 설정 (OpenWeather용 영문 이름)
city_dict = {
    "서울": "Seoul",
    "인천": "Incheon",
    "부산": "Busan",
    "대구": "Daegu",
    "광주": "Gwangju",
    "대전": "Daejeon",
    "울산": "Ulsan",
    "제주": "Jeju"
}

# 📊 월별 기준 데이터
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

# 📌 위험지수 계산 함수
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

# 🟢 해석 함수
def interpret_index(risk):
    if risk <= 5:
        return "🟢 정상 (조치 불필요)"
    elif risk <= 15:
        return "🟡 주의 (모니터링 강화)"
    elif risk <= 30:
        return "🟠 경계 (점검 필요)"
    else:
        return "🔴 심각 (즉각 조치)"

# 🌤 현재 날씨
def get_current_weather(city_name):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}&units=metric"
    res = requests.get(url)
    data = res.json()
    temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    return temp, humidity

# 📅 5일 예보
def get_forecast(city_name):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={API_KEY}&units=metric"
    res = requests.get(url)
    data = res.json()
    forecast = {}
    for entry in data["list"]:
        date = entry["dt_txt"].split(" ")[0]
        temp = entry["main"]["temp"]
        humidity = entry["main"]["humidity"]
        if date not in forecast:
            forecast[date] = {"temp": [], "humidity": []}
        forecast[date]["temp"].append(temp)
        forecast[date]["humidity"].append(humidity)

    forecast_avg = {}
    for date, vals in forecast.items():
        avg_temp = np.mean(vals["temp"])
        avg_humidity = np.mean(vals["humidity"])
        forecast_avg[date] = {"temp": round(avg_temp, 1), "humidity": round(avg_humidity, 1)}
    return forecast_avg

# 🚀 Streamlit UI
st.title("☣️ 화학사고 위험지수 실시간 확인 by 이탁수&김민선")
st.markdown("현재 기상 정보와 예측을 기반으로 **화학사고 위험지수**를 계산합니다.")

city_kor = st.selectbox("도시를 선택하세요", list(city_dict.keys()), index=1)
city_eng = city_dict[city_kor]

today = datetime.date.today()
month = today.month
info = monthly_data[month]

temp, humidity = get_current_weather(city_eng)
br, er, risk = calculate_risk(info, temp, humidity)
level = interpret_index(risk)

# 📍 현재 기상 정보 (작게 왼쪽에)
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🌡️ 현재 기상")
    st.metric("온도", f"{temp} 도")
    st.metric("습도", f"{humidity} %")

# 💥 중앙에 화학사고 위험지수 강조
with col2:
    st.markdown("### 💥 화학사고 위험지수")
    st.markdown(
        f"""
        <div style='
            font-size: 30px;
            font-weight: bold;
            color: {"red" if risk > 30 else "orange" if risk > 15 else "gold" if risk > 5 else "green"};
            text-align: center;
            border: 2px solid #ddd;
            padding: 1rem;
            border-radius: 10px;
            background-color: #f9f9f9;
        '>
        위험지수: {risk}%<br>({level})
        </div>
        """,
        unsafe_allow_html=True
    )

# 예보 확장
with st.expander("📅이번주 화학사고 위험 예측 보기"):
    forecast_data = get_forecast(city_eng)
    st.write("날짜별 평균 온도/습도 기반 예측:")

    rows = []
    for date, vals in list(forecast_data.items())[:5]:  # 5일만 표시
        month_for_forecast = int(date.split("-")[1])
        info_forecast = monthly_data[month_for_forecast]
        t, h = vals["temp"], vals["humidity"]
        br, er, risk = calculate_risk(info_forecast, t, h)
        level = interpret_index(risk)
        rows.append([date, f"{t}°C", f"{h}%", f"{risk}%", level])

    st.table(pd.DataFrame(rows, columns=["날짜", "예측 온도", "예측 습도", "위험지수", "해석"]))
