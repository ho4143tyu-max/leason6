
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

st.caption(
    f"자료 출처: 서울 기온 CSV | 필터: 2025년 이하, 연평균기온 유효 관측일 300일 이상. "
    f"전체 기간 회귀식: 예상 기온 = {slope:.6f} × 연도 + ({intercept:.3f}). "
    + (
        f"최근 구간 회귀식: 예상 기온 = {recent_slope:.6f} × 연도 + ({recent_intercept:.3f})."
        if np.isfinite(recent_slope)
        else "최근 20년 회귀식은 유효한 연도가 부족해 계산하지 못했습니다."
    )
)
