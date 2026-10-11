# mock_data.py
"""
模拟后端 API 返回的统一 JSON 数据。
用于 C 在联调前开发统计、图表、Streamlit 看板。
"""

import json
from datetime import datetime, timedelta, timezone
import random
import numpy as np
import os

BASE_URL = os.getenv("USAGE_API_BASE", "http://127.0.0.1:8000")
USE_MOCK = os.getenv("USAGE_USE_MOCK", "1") == "1"

# 固定随机种子，保证每次运行生成的数据一致，方便调试
random.seed(42)


def generate_trend(days=7):
    """
    生成最近 days 天的每日总使用时长（秒）。
    返回列表，每个元素是 {"date": "YYYY-MM-DD", "total_duration_seconds": 整数}
    """
    today = datetime.now(timezone.utc).date()
    trend = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        # 模拟每天总时长在 2~6 小时之间波动
        total_seconds = random.randint(2 * 3600, 6 * 3600)
        trend.append({
            "date": day.isoformat(),          # "2026-10-10"
            "total_duration_seconds": total_seconds
        })
    return trend


def calculate_summary(trend):
    """
    根据 trend 列表计算 summary 指标。
    使用 numpy 计算均值、中位数、P90。
    """
    durations = [item["total_duration_seconds"] for item in trend]
    arr = np.array(durations, dtype=float)
    return {
        "total_duration_seconds": int(arr.sum()),
        "avg_daily_seconds": float(arr.mean()),
        "median_daily_seconds": float(np.median(arr)),
        "p90_daily_seconds": float(np.percentile(arr, 90))
    }


def generate_app_ranking(total_duration):
    """
    根据总时长生成应用排行。
    每个应用有一个权重，权重之和为 1。
    返回按 duration_seconds 降序排列的列表。
    """
    apps = [
        {"app_key": "chrome",       "app_name": "Chrome", "category": "工具", "weight": 0.35},
        {"app_key": "com.tencent.mm","app_name": "微信",   "category": "社交", "weight": 0.25},
        {"app_key": "douyin",       "app_name": "抖音",   "category": "娱乐", "weight": 0.20},
        {"app_key": "study",        "app_name": "学习通", "category": "学习", "weight": 0.10},
        {"app_key": "bilibili",     "app_name": "B站",    "category": "娱乐", "weight": 0.10},
    ]

    ranking = []
    for app in apps:
        duration = int(total_duration * app["weight"])
        ranking.append({
            "app_key": app["app_key"],
            "app_name": app["app_name"],
            "category": app["category"],
            "duration_seconds": duration,
            "percentage": round(app["weight"] * 100, 2)
        })

    # 按时长从高到低排序
    ranking.sort(key=lambda x: x["duration_seconds"], reverse=True)
    return ranking


def generate_group_comparison(my_avg_daily_seconds):
    """
    生成群体对比数据。
    模拟群体均值、中位数、P90，以及我的排名。
    """
    group_avg = my_avg_daily_seconds * random.uniform(0.8, 1.2)
    group_median = my_avg_daily_seconds * random.uniform(0.8, 1.1)
    group_p90 = my_avg_daily_seconds * random.uniform(1.2, 1.5)

    # 根据个人日均相对群体均值的位置，算一个合理的排名
    ratio = my_avg_daily_seconds / group_avg if group_avg > 0 else 1.0
    # ratio 越小排名越靠前；把 ratio 映射到 1~20
    rank = int(max(1, min(20, round(ratio * 10))))

    return {
        "group_avg_daily_seconds": round(float(group_avg), 1),
        "group_median_daily_seconds": round(float(group_median), 1),
        "group_p90_daily_seconds": round(float(group_p90), 1),
        "my_rank": rank,
        "group_size": 20
    }


def get_mock_response():
    """
    返回完整的模拟 API 响应字典。
    这是其他模块唯一需要调用的函数。
    """
    # 1. 生成最近 7 天的趋势数据
    trend = generate_trend(days=7)

    # 2. 根据趋势计算 summary
    summary = calculate_summary(trend)

    # 3. 根据总时长生成应用排行
    total_duration = summary["total_duration_seconds"]
    app_ranking = generate_app_ranking(total_duration)

    # 4. 生成群体对比数据
    group_comparison = generate_group_comparison(summary["avg_daily_seconds"])

    # 5. 构造 period（时间范围）
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=6)
    period = {
        "start": datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
                 .isoformat().replace("+00:00", "Z"),
        "end": datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
               .replace(hour=23, minute=59, second=59)
               .isoformat().replace("+00:00", "Z")
    }

    # 6. 组装最终字典
    return {
        "device_id": "win_device_01",
        "period": period,
        "summary": summary,
        "trend": trend,
        "app_ranking": app_ranking,
        "group_comparison": group_comparison
    }

def generate_raw_events(device_id="win_device_01", days=7):
    """
    生成模拟的原始上传事件列表，格式与 A→B 的上传 JSON 完全一致。
    用于验证统计逻辑，或在后端未就绪时自己造数据。
    """
    today = datetime.now(timezone.utc).date()
    events = []
    event_counter = 1

    # 每天模拟若干个活跃时间段
    app_pool = [
        ("chrome", "windows"),
        ("com.tencent.mm", "windows"),
        ("douyin", "windows"),
        ("study", "windows"),
        ("bilibili", "windows"),
    ]

    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        # 每天随机 3~6 条记录
        n_events = random.randint(3, 6)
        for _ in range(n_events):
            app_key, platform = random.choice(app_pool)
            # 开始时间：当天 8:00 ~ 22:00 之间
            start_hour = random.randint(8, 21)
            start_minute = random.randint(0, 59)
            start_dt = datetime(
                day.year, day.month, day.day,
                start_hour, start_minute, 0,
                tzinfo=timezone.utc
            )
            # 时长：5 分钟 ~ 2 小时
            duration_seconds = random.randint(5 * 60, 2 * 3600)
            end_dt = start_dt + timedelta(seconds=duration_seconds)

            events.append({
                "event_id": f"evt_{event_counter:04d}",
                "device_id": device_id,
                "platform": platform,
                "app_key": app_key,
                "start_at": start_dt.isoformat().replace("+00:00", "Z"),
                "end_at": end_dt.isoformat().replace("+00:00", "Z"),
                "duration_seconds": duration_seconds
            })
            event_counter += 1

    return events


def aggregate_events_to_response(events, device_id="win_device_01"):
    """
    把原始事件聚合成分析响应格式。
    这样 mock 数据就和真实后端逻辑一致：
    原始事件 → 按天汇总 → 应用排行 → 群体对比。
    """
    import pandas as pd

    df = pd.DataFrame(events)

    # 按天汇总
    df["date"] = pd.to_datetime(df["start_at"], utc=True).dt.date
    daily = df.groupby("date")["duration_seconds"].sum().reset_index()
    daily = daily.sort_values("date")
    trend = [
        {"date": str(row["date"]), "total_duration_seconds": int(row["duration_seconds"])}
        for _, row in daily.iterrows()
    ]

    # 计算 summary
    durations = [item["total_duration_seconds"] for item in trend]
    arr = np.array(durations, dtype=float)
    summary = {
        "total_duration_seconds": int(arr.sum()),
        "avg_daily_seconds": float(arr.mean()),
        "median_daily_seconds": float(np.median(arr)),
        "p90_daily_seconds": float(np.percentile(arr, 90))
    }

    # 应用排行
    app_group = df.groupby("app_key")["duration_seconds"].sum().reset_index()
    app_group = app_group.sort_values("duration_seconds", ascending=False)
    total = app_group["duration_seconds"].sum()
    app_name_map = {
        "chrome": ("Chrome", "工具"),
        "com.tencent.mm": ("微信", "社交"),
        "douyin": ("抖音", "娱乐"),
        "study": ("学习通", "学习"),
        "bilibili": ("B站", "娱乐"),
    }
    app_ranking = []
    for _, row in app_group.iterrows():
        key = row["app_key"]
        name, category = app_name_map.get(key, (key, "其他"))
        app_ranking.append({
            "app_key": key,
            "app_name": name,
            "category": category,
            "duration_seconds": int(row["duration_seconds"]),
            "percentage": round(float(row["duration_seconds"]) / total * 100, 2)
        })

    # 群体对比
    group_comparison = generate_group_comparison(summary["avg_daily_seconds"])

    # period
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1) if (days := len(trend)) else today
    period = {
        "start": datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
                 .isoformat().replace("+00:00", "Z"),
        "end": datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
               .replace(hour=23, minute=59, second=59)
               .isoformat().replace("+00:00", "Z")
    }

    return {
        "device_id": device_id,
        "period": period,
        "summary": summary,
        "trend": trend,
        "app_ranking": app_ranking,
        "group_comparison": group_comparison
    }


def get_mock_response_from_events(device_id="win_device_01", days=7):
    """
    更真实的 mock：先生成原始事件，再聚合成分析响应。
    推荐 C 用这个函数，因为它和真实后端逻辑一致。
    """
    events = generate_raw_events(device_id=device_id, days=days)
    return aggregate_events_to_response(events, device_id=device_id)

# 直接运行本文件时，打印 JSON，方便检查
if __name__ == "__main__":
    # 打印原始上传事件（A → B 格式）
    events = generate_raw_events()
    print("=== 原始上传事件（A → B）===")
    print(json.dumps(events[:3], indent=2, ensure_ascii=False))  # 只打印前 3 条

    # 打印聚合后的分析响应（B → C 格式）
    data = get_mock_response_from_events()
    print("\n=== 聚合后的分析响应（B → C）===")
    print(json.dumps(data, indent=2, ensure_ascii=False))
