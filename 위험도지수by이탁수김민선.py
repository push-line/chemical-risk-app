import streamlit as st
import requests
import numpy as np
import pandas as pd
import datetime
import time

API_KEY = "32ce12499c694975782b1fd761dc79c1"

city_dict = {
    "서울": {"city": "Seoul", "lat": 37.5665, "lon": 126.9780},
    "인천시 서구": {"lat": 37.5562, "lon": 126.6757},
    "인천시 중구": {"lat": 37.4738, "lon": 126.6216},
    "인천시 남동구": {"lat": 37.4470, "lon": 126.7315},
    "인천시 부평구": {"lat": 37.5081, "lon": 126.7218},
    "경기도 시흥시": {"city": "Siheung", "lat": 37.3800, "lon": 126.8022},
    "경기도 파주시": {"city": "Paju", "lat": 37.7599, "lon": 126.7802},
    "경기도 김포시": {"city": "Gimpo", "lat": 37.6150, "lon": 126.7159},
    "경기도 고양시": {"city": "Goyang", "lat": 37.6584, "lon": 126.8320},
    "경기도 안산시": {"city": "Ansan", "lat": 37.3219, "lon": 126.8309},
    "경기도 부천시": {"city": "Bucheon", "lat": 37.5034, "lon": 126.7660},
}

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
    12: {"N": 56, "death_d": 3, "death_o": 0, "inj_d": 86, "inj_o": 5, "Tm": 0.7, "Hm": 68.8},
}


def calculate_risk(info, T, H):
    deaths = info["death_d"] + info["death_o"]
    injuries_direct = info["inj_d"]
    injuries_other = info["inj_o"]
    incidents = info["N"]
    Tm = info["Tm"]
    Hm = info["Hm"]

    alpha = 0.02
    beta = 0.005

    score = deaths * 100 + injuries_direct * 40 + injuries_other * 10
    BR = score * (1 + 0.05 * incidents)
    ER = score * (1 + alpha * (T - Tm) + beta * (H - Hm)) * (1 + 0.05 * incidents)

    risk_index = ((ER - BR) / BR) * 100
    risk_index = np.clip(risk_index, 0, 100)

    return round(BR, 1), round(ER, 1), round(risk_index, 1)


def interpret_index(risk):
    if risk <= 5:
        return "🟢 정상 (조치 불필요)"
    elif risk <= 15:
        return "🟡 주의 (모니터링 강화)"
    elif risk <= 30:
        return "🟠 경계 (점검 필요)"
    else:
        return "🔴 심각 (즉각 조치)"


def get_current_weather(info):
    if "city" in info:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={info['city']}&appid={API_KEY}&units=metric"
    else:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={info['lat']}&lon={info['lon']}&appid={API_KEY}&units=metric"
    res = requests.get(url)
    data = res.json()
    temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    return temp, humidity


def get_forecast(info):
    if "city" in info:
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={info['city']}&appid={API_KEY}&units=metric"
    else:
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={info['lat']}&lon={info['lon']}&appid={API_KEY}&units=metric"
    res = requests.get(url)
    data = res.json()

    forecast_list = []
    for item in data["list"]:
        dt = datetime.datetime.fromtimestamp(item["dt"])
        temp = item["main"]["temp"]
        humidity = item["main"]["humidity"]
        forecast_list.append({"date": dt.date(), "temp": temp, "humidity": humidity})

    forecast_df = pd.DataFrame(forecast_list)
    daily_forecast = forecast_df.groupby("date").mean().reset_index()
    return daily_forecast


st.set_page_config(page_title="화학사고 위험지수", page_icon="☣️", layout="wide")
st.title("☣️ 화학사고 위험지수 실시간 확인 by 이탁수&김민선")

st.markdown("<h3>🌎 도시를 선택하세요</h3>", unsafe_allow_html=True)
city_kor = st.selectbox("", list(city_dict.keys()), index=1)
city_info = city_dict[city_kor]

today = datetime.date.today()
month = today.month
info = monthly_data[month]

temp, humidity = get_current_weather(city_info)
br, er, risk = calculate_risk(info, temp, humidity)
level = interpret_index(risk)

col1, col2, col3 = st.columns([1, 2, 3])

with col1:
    st.markdown("### 🌡️ 현재 기상")
    st.metric("온도", f"{temp}°C")
    st.metric("습도", f"{humidity}%")

with col2:
    st.markdown("### 💥 현재 위험지수")
    st.markdown(
        f"""
        <div style='
            font-size: 36px;
            font-weight: bold;
            color: {"red" if risk > 30 else "orange" if risk > 15 else "gold" if risk > 5 else "green"};
            text-align: center;
            border: 3px solid #ddd;
            padding: 1rem;
            border-radius: 15px;
            background-color: #f9f9f9;
        '>
        위험지수: {risk}%<br>({level})
        </div>
        """,
        unsafe_allow_html=True
    )
with col3:
    st.markdown("<h6>🛡️위험지수→평년 대비 현재의 온습도에 따른 화학사고 발생 위험도(서부 관내 화학사고 발생 데이터 활용)</h6>", unsafe_allow_html=True)
    st.markdown("""  
    | 위험지수 범위 | 등급 | 설명 |
|:------------|:----|:-----|
| 0% ~ 5%    | 🟢 정상 | 조치 불필요 |
| 5% ~ 15%   | 🟡 주의 | 모니터링 강화 |
| 15% ~ 30%  | 🟠 경계 | 점검 필요 |
| 30% 이상   | 🔴 심각 | 즉각 조치 필요 |
""")

# 🔥 5일간 평균 예측
st.markdown("### 📅 5일간 위험지수 예보")
forecast_df = get_forecast(city_info)

risk_list = []
for idx, row in forecast_df.iterrows():
    br_, er_, risk_ = calculate_risk(info, row["temp"], row["humidity"])
    level_ = interpret_index(risk_)
    risk_list.append({
        "날짜": row["date"],
        "예상 온도(°C)": round(row["temp"], 1),
        "예상 습도(%)": round(row["humidity"], 1),
        "예상 위험지수(%)": risk_,
        "예상 등급": level_
    })

risk_forecast_df = pd.DataFrame(risk_list)
st.dataframe(risk_forecast_df)


# 📜 출처 명시
st.caption("※ 본 데이터는 OpenWeatherMap API를 기반으로 수집되었습니다.")

# 🚀 자동 새로고침 (1초)
time.sleep(1)
st.rerun()
