# app.py
"""
Streamlit 主页面：使用时间统计看板。
运行：streamlit run app.py
"""

import streamlit as st
from api_client import fetch_analysis
from charts import line_trend, bar_ranking, pie_category, bar_group_compare

st.set_page_config(page_title="使用时间统计看板", layout="wide")
st.title("📊 使用时间统计看板")


def fmt_hours(seconds):
    """秒 → 小时，保留 1 位小数"""
    return f"{seconds / 3600:.1f} 小时"


# ---------- 加载数据 ----------
with st.spinner("正在加载数据..."):
    try:
        data = fetch_analysis()
    except Exception as e:
        st.error(f"数据加载失败：{e}")
        st.stop()

summary = data["summary"]
group = data["group_comparison"]

# ---------- 指标卡 ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("总时长", fmt_hours(summary["total_duration_seconds"]))
col2.metric("日均", fmt_hours(summary["avg_daily_seconds"]))
col3.metric("中位数", fmt_hours(summary["median_daily_seconds"]))
col4.metric("P90", fmt_hours(summary["p90_daily_seconds"]))

st.caption(
    f"数据范围：{data['period']['start']} ~ {data['period']['end']}　"
    f"设备：{data['device_id']}"
)

# ---------- 趋势图 ----------
st.subheader("📈 每日使用趋势")
st.plotly_chart(line_trend(data["trend"]), use_container_width=True)

# ---------- 排行 + 饼图 ----------
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("🏆 应用使用排行")
    st.plotly_chart(bar_ranking(data["app_ranking"]), use_container_width=True)
with col_b:
    st.subheader("🥧 使用类别占比")
    st.plotly_chart(pie_category(data["app_ranking"]), use_container_width=True)

# ---------- 群体对比 ----------
st.subheader("👥 个人 vs 群体")
st.plotly_chart(bar_group_compare(summary, group), use_container_width=True)

st.info(
    f"你在群体中排名：第 **{group['my_rank']}** 名 / 共 **{group['group_size']}** 人"
)

# ---------- 使用建议 ----------
st.subheader("💡 使用建议")
tips = []
avg_h = summary["avg_daily_seconds"] / 3600
if avg_h > 6:
    tips.append(f"日均 {avg_h:.1f} 小时，使用时间偏长，建议明显减少。")
elif avg_h > 4:
    tips.append(f"日均 {avg_h:.1f} 小时，略高于健康范围，注意控制。")

# 娱乐类占比
entertainment_seconds = sum(
    item["duration_seconds"] for item in data["app_ranking"]
    if item["category"] == "娱乐"
)
total_seconds = summary["total_duration_seconds"]
if total_seconds > 0 and entertainment_seconds / total_seconds > 0.4:
    tips.append("娱乐类应用占比超过 40%，建议调整使用结构。")

# 学习类
study_seconds = sum(
    item["duration_seconds"] for item in data["app_ranking"]
    if item["category"] == "学习"
)
if study_seconds < 0.5 * 3600:
    tips.append("学习类应用使用时间偏少，可适当增加。")

if not tips:
    tips.append("使用情况良好 👍")

for t in tips:
    st.write(f"- {t}")

st.caption("数据来源：后端 /api/v1/devices/{device_id}/analysis（当前为 mock）")