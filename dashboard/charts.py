# charts.py
"""
图表函数：折线图、柱状图、饼图、群体对比图。
每个函数接收后端返回的 JSON 片段，返回 plotly figure。
"""

import pandas as pd
import plotly.express as px


def line_trend(trend):
    """每日使用趋势折线图"""
    df = pd.DataFrame(trend)
    df["hours"] = df["total_duration_seconds"] / 3600
    fig = px.line(
        df, x="date", y="hours", markers=True,
        title="每日使用趋势",
        labels={"date": "日期", "hours": "时长（小时）"}
    )
    fig.update_layout(yaxis_range=[0, max(df["hours"]) * 1.2 if len(df) else 1])
    return fig


def bar_ranking(app_ranking):
    """应用使用排行柱状图"""
    df = pd.DataFrame(app_ranking)
    df["hours"] = df["duration_seconds"] / 3600
    fig = px.bar(
        df, x="app_name", y="hours", color="category",
        title="应用使用排行",
        labels={"app_name": "应用", "hours": "时长（小时）", "category": "类别"}
    )
    return fig


def pie_category(app_ranking):
    """按类别汇总的饼图"""
    df = pd.DataFrame(app_ranking)
    df = df.groupby("category", as_index=False)["duration_seconds"].sum()
    df["hours"] = df["duration_seconds"] / 3600
    fig = px.pie(
        df, names="category", values="duration_seconds",
        title="使用类别占比",
        hover_data=["hours"]
    )
    return fig


def bar_group_compare(summary, group_comparison):
    """个人 vs 群体的分组柱状图"""
    metrics = ["日均", "中位数", "P90"]
    my_values = [
        summary["avg_daily_seconds"] / 3600,
        summary["median_daily_seconds"] / 3600,
        summary["p90_daily_seconds"] / 3600,
    ]
    group_values = [
        group_comparison["group_avg_daily_seconds"] / 3600,
        group_comparison["group_median_daily_seconds"] / 3600,
        group_comparison["group_p90_daily_seconds"] / 3600,
    ]
    df = pd.DataFrame({
        "指标": metrics,
        "个人": my_values,
        "群体": group_values,
    })
    fig = px.bar(
        df, x="指标", y=["个人", "群体"], barmode="group",
        title="个人 vs 群体",
        labels={"value": "时长（小时）", "variable": "对象"}
    )
    return fig