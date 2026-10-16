import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
)

st.set_page_config(page_title="기온 예측기", page_icon="🌡️", layout="wide")
st.title("🌡️ 기온 예측기")
st.write("서울의 과거 연평균기온을 이용해 선택한 연도의 기온을 선형회귀로 추정합니다.")
st.caption("분석 기준: 2025년까지의 자료 중 연간 유효 관측일이 300일 이상인 해")

@st.cache_data
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url, encoding="utf-8")
    df.columns = df.columns.astype(str).str.strip()

    required = ["날짜", "평균기온"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            "필수 열을 찾을 수 없습니다: "
            + ", ".join(missing)
            + f"\n파일에서 읽은 열 이름: {', '.join(df.columns)}"
        )

    # 날짜 열이 YYYYMMDD 형태이거나 일반 날짜 문자열인 경우 모두 처리
    date_text = df["날짜"].astype(str).str.strip()
    df["날짜_변환"] = pd.to_datetime(date_text, format="%Y%m%d", errors="coerce")
    needs_fallback = df["날짜_변환"].isna()
    if needs_fallback.any():
        df.loc[needs_fallback, "날짜_변환"] = pd.to_datetime(
            date_text[needs_fallback], errors="coerce"
        )

    # 숫자 열에 결측 기호나 문자열이 있어도 숫자로 정리
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")
    df = df.dropna(subset=["날짜_변환"])
    df["연도"] = df["날짜_변환"].dt.year
    return df

try:
    raw = load_data(DATA_URL)
except Exception as exc:
    st.error("서울 기온 데이터를 불러오거나 처리하지 못했습니다.")
    st.exception(exc)
    st.stop()

# 2025년까지의 자료만 사용한다. 평균기온이 실제로 기록된 날만 관측일로 센다.
limited = raw[(raw["연도"] <= 2025) & raw["평균기온"].notna()].copy()
annual = (
    limited.groupby("연도")
    .agg(
        연평균기온=("평균기온", "mean"),
        관측일수=("평균기온", "count"),
    )
    .reset_index()
)
annual = annual[annual["관측일수"] >= 300].sort_values("연도").reset_index(drop=True)

if len(annual) < 2:
    st.error("회귀 직선을 계산하기에 유효한 연도가 부족합니다. 데이터와 필터 조건을 확인해 주세요.")
    st.stop()

years = annual["연도"].to_numpy(dtype=float)
temps = annual["연평균기온"].to_numpy(dtype=float)

# 전체 기간의 최소제곱 선형회귀
slope, intercept = np.polyfit(years, temps, 1)
correlation = float(np.corrcoef(years, temps)[0, 1])
fit_temps = slope * years + intercept

start_year = int(annual["연도"].min())
end_year = int(annual["연도"].max())
year_count = len(annual)

# 최근 20년: 데이터에서 가장 최근인 유효 연도를 기준으로 20년 구간을 설정
recent_start_year = end_year - 19
recent = annual[annual["연도"] >= recent_start_year].copy()
if len(recent) >= 2:
    recent_slope, recent_intercept = np.polyfit(
        recent["연도"].to_numpy(dtype=float),
        recent["연평균기온"].to_numpy(dtype=float),
        1,
    )
    recent_year_count = len(recent)
    recent_actual_start = int(recent["연도"].min())
    recent_actual_end = int(recent["연도"].max())
else:
    recent_slope, recent_intercept = np.nan, np.nan
    recent_year_count = len(recent)
    recent_actual_start = int(recent["연도"].min()) if len(recent) else None
    recent_actual_end = int(recent["연도"].max()) if len(recent) else None
st.subheader("100년당 기온 상승폭 비교")
st.write("회귀 직선의 기울기에 100을 곱해, 100년 동안의 예상 기온 변화량으로 표시합니다.")
slope_col1, slope_col2 = st.columns(2)
with slope_col1:
    st.metric(
        label=f"전체 기간 ({start_year}~{end_year})",
        value=f"{slope * 100:+.2f} °C / 100년",
    )
with slope_col2:
    if np.isfinite(recent_slope):
        st.metric(
            label=f"최근 20년 구간 ({recent_actual_start}~{recent_actual_end})",
            value=f"{recent_slope * 100:+.2f} °C / 100년",
        )
    else:
        st.metric(label="최근 20년 구간", value="계산할 데이터 부족")

if np.isfinite(recent_slope):
    difference = (recent_slope - slope) * 100
    if difference > 0:
        st.write(f"최근 20년의 기울기가 전체 기간보다 100년당 {difference:.2f} °C 더 큽니다.")
    elif difference < 0:
        st.write(f"최근 20년의 기울기가 전체 기간보다 100년당 {abs(difference):.2f} °C 더 작습니다.")
    else:
        st.write("최근 20년과 전체 기간의 기울기가 같습니다.")

st.subheader("예상 기온 확인")
selected_year = st.slider(
    "예측할 연도를 선택하세요",
    min_value=1900,
    max_value=2100,
    value=2025,
    step=1,
)
predicted_temp = slope * selected_year + intercept
st.metric(
    label=f"{selected_year}년 선형회귀 예상 연평균기온",
    value=f"{predicted_temp:.2f} °C",
)
st.caption("예측값은 과거 자료의 직선을 연장한 추정치이며, 실제 기온이나 공식 기후 전망이 아닙니다.")

metric1, metric2, metric3 = st.columns(3)
metric1.metric("회귀에 사용한 연도 수", f"{year_count}년")
metric2.metric("시작 연도", f"{start_year}년")
metric3.metric("끝 연도", f"{end_year}년")

st.subheader("연도별 평균기온과 회귀 직선")
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=annual["연도"],
        y=annual["연평균기온"],
        mode="markers",
        name="연평균기온",
        marker=dict(size=8),
        customdata=annual[["관측일수"]].to_numpy(),
        hovertemplate=(
            "연도: %{x}년<br>"
            "연평균기온: %{y:.2f} °C<br>"
            "유효 관측일: %{customdata[0]}일<extra></extra>"
        ),
    )
)
