# error_mock.py
"""模拟错题管理系统的数据。

和 mock_data.py 分工：
- mock_data.py  负责「过程数据」——应用使用时长、专注时长
- error_mock.py 负责「结果数据」——错题、掌握情况、复习进度

对外只暴露 build_error_block()，返回的字段直接并进
后端 /api/v1/analysis 的响应里。
"""

import random
from datetime import datetime, timedelta, timezone

random.seed(2026)


# 科目 → (错题数, 已掌握数, [(知识点, 错题数), ...])
# 每科的知识点错题数之和等于该科错题总数，保持自洽
SUBJECT_TABLE = [
    ("数学", 45, 30, [
        ("导数与函数", 15),
        ("立体几何", 12),
        ("数列", 10),
        ("概率统计", 8),
    ]),
    ("物理", 35, 20, [
        ("电磁学", 13),
        ("力学", 9),
        ("光学", 7),
        ("热学", 6),
    ]),
    ("英语", 25, 18, [
        ("完形填空", 9),
        ("阅读理解", 8),
        ("语法填空", 8),
    ]),
    ("化学", 20, 14, [
        ("有机化学", 8),
        ("化学反应原理", 7),
        ("元素周期律", 5),
    ]),
    ("语文", 15, 9, [
        ("文言文", 6),
        ("现代文阅读", 5),
        ("作文", 4),
    ]),
]


def build_error_block(days=7, focus_trend=None):
    """构造错题维度的完整数据块。

    focus_trend 传入 mock_data 的 trend，用来和专注时长对齐日期，
    这样「效率双轴图」的日期轴两边一致。
    """
    total_errors = sum(row[1] for row in SUBJECT_TABLE)
    mastered_errors = sum(row[2] for row in SUBJECT_TABLE)
    reviewing_errors = total_errors - mastered_errors

    error_stats = {
        "total_errors": total_errors,
        "mastered_errors": mastered_errors,
        "reviewing_errors": reviewing_errors,
        "mastery_rate": round(mastered_errors / total_errors * 100, 1),
    }

    subject_distribution = [
        {
            "subject": name,
            "error_count": err,
            "mastered_count": mst,
            "reviewing_count": err - mst,
            "mastery_rate": round(mst / err * 100, 1),
        }
        for name, err, mst, _ in SUBJECT_TABLE
    ]

    knowledge_points = []
    for name, _, _, points in SUBJECT_TABLE:
        for point, count in points:
            knowledge_points.append({
                "subject": name,
                "knowledge_point": point,
                "error_count": count,
            })
    knowledge_points.sort(key=lambda x: x["error_count"], reverse=True)

    # 最近 days 天的新增 / 消灭，日期与专注趋势对齐
    if focus_trend:
        dates = [item["date"] for item in focus_trend]
        focus_hours = [round(item["total_duration_seconds"] / 3600, 2) for item in focus_trend]
    else:
        today = datetime.now(timezone.utc).date()
        dates = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
        focus_hours = [0.0] * days

    new_added_seq = [7, 5, 6, 3, 4, 2, 3]
    resolved_seq = [4, 8, 5, 9, 6, 10, 7]

    review_trend = []
    efficiency_trend = []
    for i, date in enumerate(dates):
        new_added = new_added_seq[i % len(new_added_seq)]
        resolved = resolved_seq[i % len(resolved_seq)]
        review_trend.append({
            "date": date,
            "new_added": new_added,
            "resolved": resolved,
        })
        efficiency_trend.append({
            "date": date,
            "focus_hours": focus_hours[i] if i < len(focus_hours) else 0.0,
            "new_errors": new_added,
            "resolved_errors": resolved,
        })

    return {
        "error_stats": error_stats,
        "subject_distribution": subject_distribution,
        "knowledge_points": knowledge_points,
        "review_trend": review_trend,
        "efficiency_trend": efficiency_trend,
    }
