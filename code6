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

# 최소제곱 선형회귀: 예상 기온 = 기울기 × 연도 + 절편
slope, intercept = np.polyfit(years, temps, 1)
correlation = float(np.corrcoef(years, temps)[0, 1])
fit_temps = slope * years + intercept

start_year = int(annual["연도"].min())
end_year = int(annual["연도"].max())
year_count = len(annual)

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
line_years = np.array([start_year, end_year], dtype=float)
fig.add_trace(
    go.Scatter(
        x=line_years,
        y=slope * line_years + intercept,
        mode="lines",
        name="선형회귀 직선",
        line=dict(width=3),
        hovertemplate="연도: %{x:.0f}년<br>회귀값: %{y:.2f} °C<extra></extra>",
    )
)
# 선택한 연도의 예측값도 그래프에서 확인할 수 있도록 표시
fig.add_trace(
    go.Scatter(
        x=[selected_year],
        y=[predicted_temp],
        mode="markers",
        name=f"{selected_year}년 예측값",
        marker=dict(size=13, symbol="diamond"),
        hovertemplate="%{x}년 예측값: %{y:.2f} °C<extra></extra>",
    )
)
fig.update_layout(
    xaxis_title="연도",
    yaxis_title="연평균기온 (°C)",
    hovermode="closest",
    legend_title="범례",
    margin=dict(l=20, r=20, t=30, b=20),
)
st.plotly_chart(fig, use_container_width=True)

st.metric("연도와 연평균기온의 피어슨 상관계수", f"{correlation:.4f}")
if correlation > 0:
    st.write("해석: 분석 기간에는 연도가 커질수록 연평균기온이 높아지는 양의 선형 관계가 나타납니다.")
elif correlation < 0:
    st.write("해석: 분석 기간에는 연도가 커질수록 연평균기온이 낮아지는 음의 선형 관계가 나타납니다.")
else:
    st.write("해석: 분석 기간의 연도와 연평균기온 사이에 선형 상관관계가 거의 나타나지 않습니다.")

with st.expander("분석에 사용한 연도별 데이터 보기"):
    display_df = annual.copy()
    display_df["연평균기온"] = display_df["연평균기온"].round(2)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
