import streamlit as st
import requests
import numpy as np
import pandas as pd
import datetime
KST = datetime.timezone(datetime.timedelta(hours=9))
import gspread
from google.oauth2.service_account import Credentials

# 🔥 API 키
SERVICE_KEY = "iN/Sz1zmIiINI5hTBH3m/XQDjB+oMj/8gzDJytzGQs6XPC3xeLs6c1XLCVWH53VObrUfLFWQTXWcEeM0FG3rXg=="
OPENWEATHER_KEY = "32ce12499c694975782b1fd761dc79c1"

# 🔽 도시 정보
city_dict = {
    "서울시": {"nx": 60, "ny": 127, "name": "Seoul,kr"},
    "인천시 강화군": {"nx": 51, "ny": 130, "name": "Incheon,kr"},
    "인천시 계양구": {"nx": 55, "ny": 128, "name": "Incheon,kr"},
    "인천시 남동구": {"nx": 56, "ny": 125, "name": "Incheon,kr"},
    "인천시 동구": {"nx": 55, "ny": 126, "name": "Incheon,kr"},
    "인천시 미추홀구": {"nx": 55, "ny": 125, "name": "Incheon,kr"},
    "인천시 부평구": {"nx": 56, "ny": 126, "name": "Incheon,kr"},
    "인천시 서구": {"nx": 55, "ny": 128, "name": "Incheon,kr"},
    "인천시 연수구": {"nx": 55, "ny": 124, "name": "Incheon,kr"},
    "인천시 중구": {"nx": 54, "ny": 125, "name": "Incheon,kr"},
    "경기도 고양시": {"nx": 57, "ny": 128, "name": "Goyang,kr"},
    "경기도 김포시": {"nx": 55, "ny": 128, "name": "Gimpo-si,kr"},
    "경기도 부천시": {"nx": 56, "ny": 126, "name": "Bucheon,kr"},
    "경기도 시흥시": {"nx": 56, "ny": 125, "name": "Siheung-si,kr"},
    "경기도 안산시": {"nx": 57, "ny": 123, "name": "Ansan,kr"},
    "경기도 파주시": {"nx": 58, "ny": 131, "name": "Paju,kr"},
}

# 🔽 월별 통계
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

# 🔽 위험 계산
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

# 🔽 위험 해석
def interpret_index(risk):
    if risk <= 5:
        return "🟢 정상 "
    elif risk <= 15:
        return "🟡 주의 (모니터링 강화)"
    elif risk <= 30:
        return "🟠 경계 (점검 필요)"
    else:
        return "🔴 심각 (즉각 조치)"

# 🔽 현재 기상 조회 (기상청)
def get_current_weather_kma(nx, ny):
    """
    KST 기준으로 getUltraSrtNcst의 최신 배포분을 안전하게 가져옴.
    - 관측은 매시 정각, 보통 xx:40 즈음 배포
    - :40 이전이면 직전 정시, 이후면 해당 정시를 우선 사용
    - 응답 없으면 한 슬롯 더 과거로 폴백
    """
    now_kst = datetime.now(KST)

    # 1) 우선 시도 슬롯 결정 (:40 rule)
    if now_kst.minute >= 40:
        cand = now_kst.replace(minute=0, second=0, microsecond=0)
    else:
        cand = (now_kst.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1))

    # 2) 후보 2개: cand, cand-1h (배포 지연 대비)
    slots = [cand, cand - timedelta(hours=1)]

    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    base_params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": "100",
        "pageNo": "1",
        "dataType": "JSON",
        "nx": nx,
        "ny": ny,
    }

    for dt_ in slots:
        params = {
            **base_params,
            "base_date": dt_.strftime("%Y%m%d"),
            "base_time": dt_.strftime("%H") + "00",
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            body = data.get("response", {}).get("body")
            if not body:
                continue
            items = body.get("items", {}).get("item", [])
            temp = humidity = None
            for it in items:
                cat = it.get("category")
                if cat == "T1H":
                    temp = float(it["obsrValue"])
                elif cat == "REH":
                    humidity = float(it["obsrValue"])
            if temp is not None and humidity is not None:
                return temp, humidity
        except Exception:
            continue

    # 둘 다 실패 시 None 반환(상위에서 안내/폴백 처리)
    return None, None

# 🔽 5일 예보 (OpenWeather)
def get_forecast_openweather(city_name):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={OPENWEATHER_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
  
    forecast_list = []
    for entry in data["list"]:
        date = entry["dt_txt"].split(" ")[0]
        temp = entry["main"]["temp"]
        humidity = entry["main"]["humidity"]
        forecast_list.append({"date": date, "temp": temp, "humidity": humidity})
    df = pd.DataFrame(forecast_list)
    df["date"] = pd.to_datetime(df["date"])
    return df.groupby(df["date"].dt.date)[["temp", "humidity"]].mean().reset_index()

# ✅ Streamlit 시작
st.set_page_config(page_title="화학사고 위험지수", page_icon="☣️", layout="wide")
st.title("☣️ 화학사고 위험지수 실시간 확인")

# 🔐 구글 인증
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["gspread_service_account"], scopes=SCOPES)
gc = gspread.authorize(credentials)
SPREADSHEET_ID = "1eCxc_5yJAWG1_zjlOkN_dlVcHRCqMtFssZlxzbwSdmY"
worksheet = gc.open_by_key(SPREADSHEET_ID).get_worksheet(0)

# 🔽 방문 기록
today_str = datetime.datetime.now(KST).strftime("%Y-%m-%d")
worksheet.append_row([str(datetime.datetime.now(KST)), today_str])
total = worksheet.acell("A1").value
visitor_count = int(total) + 1 if total and total.strip().isdigit() else 1
worksheet.update("A1", [[visitor_count]])
rows = worksheet.get_all_values()[1:]
today_count = sum(1 for r in rows if len(r) >= 2 and r[1].strip() == today_str)

# ✅ 사용자 선택
st.sidebar.markdown(f"📅총 방문자 수: **{visitor_count}명**")
st.sidebar.markdown(f"🔍오늘 방문자 수: **{today_count}명**")
city_kor = st.selectbox("👇사업장 위치 선택", list(city_dict.keys()), index=0)
city_info = city_dict[city_kor]
month = datetime.date.today().month
info = monthly_data[month]

# 🔥 현재 실황
temp_now, humidity_now = get_current_weather_kma(city_info["nx"], city_info["ny"])
br_now, er_now, risk_now = calculate_risk(info, temp_now, humidity_now)
level_now = interpret_index(risk_now)

col1, col2, col3 = st.columns([1, 2, 3])
with col1:
    st.markdown("### 🌡️ 현재 기상")
    st.metric("온도", f"{temp_now}°C")
    st.metric("습도", f"{humidity_now}%")
with col2:
    st.markdown("### 💥 현재 위험지수")
    st.markdown(
        f"""<div style='font-size: 36px; font-weight: bold; color: {"red" if risk_now > 30 else "orange" if risk_now > 15 else "gold" if risk_now > 5 else "green"}; text-align: center; border: 3px solid #ddd; padding: 1rem; border-radius: 15px; background-color: #f9f9f9;'>위험지수: {risk_now}%<br>({level_now})</div>""",
        unsafe_allow_html=True)
with col3:
    st.markdown("🛡️ 평년 대비 현재 온습도 기준 화학사고 발생 위험도")
    st.markdown("""
| 위험지수 범위 | 등급 | 설명 | 추천 행동 요령 |
|:------------|:----|:-----|:-------------|
| 0% ~ 5%    | 🟢 정상 | 정상 | 평소처럼 작업하거나 활동을 진행하세요! |
| 5% ~ 15%   | 🟡 주의 | 모니터링 강화 | 주요 설비 점검 및 모니터링을 강화하세요! |
| 15% ~ 30%  | 🟠 경계 | 점검 필요 | 보호장비 착용 및 긴급대응 계획을 준비하세요! |
| 30% 이상   | 🔴 심각 | 즉각 조치 필요 | 즉각적인 작업 중지 및 비상대응 조치를 실행하세요! |
""", unsafe_allow_html=True)

# 🔮 5일 예보
st.markdown("### 📅 5일간 위험지수 예보")
forecast_df = get_forecast_openweather(city_info["name"])

if forecast_df.empty:
    st.warning("⚠️ 5일 예보 데이터를 불러올 수 없습니다. 도시명이 올바르지 않거나 API 연결에 문제가 있을 수 있습니다.")
else:
    risk_list = []
    for idx, row in forecast_df.iterrows():
        br, er, risk = calculate_risk(info, row["temp"], row["humidity"])
        level = interpret_index(risk)
        risk_list.append({
            "날짜": row["date"].strftime("%m-%d"),
            "평균 온도(°C)": round(row["temp"], 1),
            "평균 습도(%)": round(row["humidity"], 1),
            "예상 위험지수(%)": risk,
            "예상 등급": level
        })
    st.dataframe(pd.DataFrame(risk_list).head(5))

st.caption("※본 데이터는 기상청 및 OpenWeatherMap API 기반으로 수집되었습니다.") 



