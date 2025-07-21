

import streamlit as st

import requests

import numpy as np

import pandas as pd

import datetime

import gspread

from google.oauth2.service_account import Credentials

import datetime


# 🔥 API 키

SERVICE_KEY = "iN/Sz1zmIiINI5hTBH3m/XQDjB+oMj/8gzDJytzGQs6XPC3xeLs6c1XLCVWH53VObrUfLFWQTXWcEeM0FG3rXg=="

OPENWEATHER_KEY = "32ce12499c694975782b1fd761dc79c1"


city_dict = {

    "서울시": {"nx": 60, "ny": 127, "name": "Seoul"},

    "인천시 강화군": {"nx": 51, "ny": 130, "name": "Incheon"},

    "인천시 계양구": {"nx": 55, "ny": 128, "name": "Incheon"},

    "인천시 남동구": {"nx": 56, "ny": 125, "name": "Incheon"},

    "인천시 동구": {"nx": 55, "ny": 126, "name": "Incheon"},

    "인천시 미추홀구": {"nx": 55, "ny": 125, "name": "Incheon"},

    "인천시 부평구": {"nx": 56, "ny": 126, "name": "Incheon"},

    "인천시 서구": {"nx": 55, "ny": 128, "name": "Incheon"},

    "인천시 연수구": {"nx": 55, "ny": 124, "name": "Incheon"},

    "인천시 중구": {"nx": 54, "ny": 125, "name": "Incheon"},

    "경기도 고양시": {"nx": 57, "ny": 128, "name": "Goyang"},

    "경기도 김포시": {"nx": 55, "ny": 128, "name": "Gimpo"},

    "경기도 부천시": {"nx": 56, "ny": 126, "name": "Bucheon"},

    "경기도 시흥시": {"nx": 56, "ny": 125, "name": "Siheung"},

    "경기도 안산시": {"nx": 57, "ny": 123, "name": "Ansan"},

    "경기도 파주시": {"nx": 58, "ny": 131, "name": "Paju"},

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

def get_current_weather_kma(nx, ny):

    now = datetime.datetime.now()

    base_date = now.strftime("%Y%m%d")

    base_time = now.strftime("%H") + "00"


    if int(now.strftime("%M")) < 45:

        hour = now - datetime.timedelta(hours=1)

        base_time = hour.strftime("%H") + "00"

        base_date = hour.strftime("%Y%m%d")


    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"

    params = {

        "serviceKey": SERVICE_KEY,

        "numOfRows": "100",

        "pageNo": "1",

        "dataType": "JSON",

        "base_date": base_date,

        "base_time": base_time,

        "nx": nx,

        "ny": ny,

    }


    response = requests.get(url, params=params)

    data = response.json()

    items = data["response"]["body"]["items"]["item"]


    temp = None

    humidity = None

    for item in items:

        if item["category"] == "T1H":

            temp = float(item["obsrValue"])

        elif item["category"] == "REH":

            humidity = float(item["obsrValue"])


    return temp, humidity


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

    daily_df = df.groupby(df["date"].dt.date)[["temp", "humidity"]].mean().reset_index()


    return daily_df


# ✅ Streamlit UI

st.set_page_config(page_title="화학사고 위험지수", page_icon="☣️", layout="wide")

st.title("☣️ 화학사고 위험지수 실시간 확인 by 한국환경공단☣️")

import streamlit as st

import gspread

from google.oauth2.service_account import Credentials


# 🔐 인증 범위 설정

SCOPES = [

    "https://www.googleapis.com/auth/spreadsheets",

    "https://www.googleapis.com/auth/drive"

]


# 🔐 secrets.toml을 통한 인증

credentials = Credentials.from_service_account_info(

    st.secrets["gspread_service_account"],

    scopes=SCOPES

)


# 📊 gspread 클라이언트 생성

gc = gspread.authorize(credentials)


# ✅ 구글 시트 열기 (방법 1: 파일 ID로 여는 것이 가장 안정적)

SPREADSHEET_ID = "1eCxc_5yJAWG1_zjlOkN_dlVcHRCqMtFssZlxzbwSdmY"  # 예: 1AbCDeFgHiJKlmn...

sh = gc.open_by_key(SPREADSHEET_ID)


# 첫 번째 워크시트 선택

worksheet = sh.get_worksheet(0)


# 🔄 방문자 수 읽기 (A1 셀)

cell = worksheet.acell("A1").value

visitor_count = int(cell) if cell and cell.strip().isdigit() else 0


# 방문자 수 +1

visitor_count += 1


# 🔄 업데이트 (2차원 리스트로 전달해야 함)

worksheet.update("A1", [[visitor_count]])


# 🖥️ Streamlit 출력

st.markdown(f"### 📈총 방문자 수: **{visitor_count}명** ")

st.markdown("<h3 style='margin-bottom: 5px;'>👇사업장 위치를 선택해주세요</h3>", unsafe_allow_html=True)

city_kor = st.selectbox("", list(city_dict.keys()), index=0)

city_info = city_dict[city_kor]


today = datetime.date.today()

month = today.month

info = monthly_data[month]


# 🔥 오늘 실황 (기상청)

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

        f"""

        <div style='

            font-size: 36px;

            font-weight: bold;

            color: {"red" if risk_now > 30 else "orange" if risk_now > 15 else "gold" if risk_now > 5 else "green"};

            text-align: center;

            border: 3px solid #ddd;

            padding: 1rem;

            border-radius: 15px;

            background-color: #f9f9f9;

        '>

        위험지수: {risk_now}%<br>({level_now})

        </div>

        """,

        unsafe_allow_html=True

    )


with col3:

    st.markdown("🛡️ 위험지수: 평년 대비 현재 온습도 기준 화학사고 발생 위험도</small>", unsafe_allow_html=True)

    st.markdown("""

| 위험지수 범위 | 등급 | 설명 | 추천 행동 요령 |

|:------------|:----|:-----|:-------------|

| 0% ~ 5%    | 🟢 정상 | 조치 불필요 | 평소처럼 작업하거나 활동을 진행하세요! |

| 5% ~ 15%   | 🟡 주의 | 모니터링 강화 | 주요 설비 점검 및 모니터링을 강화하세요! |

| 15% ~ 30%  | 🟠 경계 | 점검 필요 | 보호장비 착용 및 긴급대응 계획을 준비하세요! |

| 30% 이상   | 🔴 심각 | 즉각 조치 필요 | 즉각적인 작업 중지 및 비상대응 조치를 실행하세요! |

    """, unsafe_allow_html=True)


# 🔥 5일 예보 (OpenWeather)

st.markdown("### 📅 5일간 위험지수 예보")

forecast_df = get_forecast_openweather(city_info["name"])


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


risk_forecast_df = pd.DataFrame(risk_list).head(5)


st.dataframe(risk_forecast_df)


st.caption("※본 데이터는 기상청 및 OpenWeatherMap API 기반으로 수집되었습니다.")


