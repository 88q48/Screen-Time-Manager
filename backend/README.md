# backend — 后端接口

（B 模块）

## 负责什么

- 接收客户端上传的应用使用记录与错题记录
- 统一统计口径，避免两端各算一套
- 向看板返回一份完整的分析结果

## 接口清单

前缀统一 `/api/v1`，字段详见 [`../docs/api-fields.md`](../docs/api-fields.md)。

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/v1/events/batch` | 批量上传应用使用记录 |
| POST | `/api/v1/errors` | 上传错题记录 |
| GET | `/api/v1/devices/{device_id}/analysis` | 返回分析结果（看板用） |
| GET | `/api/v1/devices/{device_id}/sync` | 同步信息 |
| GET | `/api/v1/health` | 健康检查 |

## 上传：应用使用记录

```json
{
  "event_id": "evt_a102",
  "device_id": "win_device_01",
  "platform": "windows",
  "app_key": "chrome",
  "start_at": "2026-10-17T09:00:00Z",
  "end_at": "2026-10-17T09:30:00Z",
  "duration_seconds": 1800
}
```

| 字段 | 说明 |
|---|---|
| `event_id` | 每条记录唯一，重试时保持不变，用于去重 |
| `device_id` | 客户端首次启动生成并持久化，不用硬件序列号 |
| `platform` | `windows` 或 `android` |
| `app_key` | 稳定的应用标识，不依赖窗口标题 |
| `start_at` / `end_at` | UTC，ISO 8601 |
| `duration_seconds` | 整数秒 |

## 上传：错题记录

```json
{
  "error_id": "err_0001",
  "device_id": "win_device_01",
  "subject": "数学",
  "knowledge_point": "导数与函数",
  "content": "求 f(x)=x^3-3x 的单调区间",
  "created_at": "2026-10-17T20:00:00Z",
  "mastered": false,
  "review_count": 0
}
```

| 字段 | 说明 |
|---|---|
| `error_id` | 每条错题唯一，用于去重 |
| `subject` | 中文科目名，与客户端录入一致 |
| `knowledge_point` | 知识点，用于薄弱项统计 |
| `mastered` | 是否已彻底掌握 |
| `review_count` | 已复习次数 |

## 建议的表结构

```
usage_event      event_id(PK) device_id platform app_key
                 start_at end_at duration_seconds received_at

error_record     error_id(PK) device_id subject knowledge_point
                 content created_at mastered review_count

device           device_id(PK) platform registered_at
```

去重交给主键加 `ON CONFLICT DO NOTHING`，比先查后插稳。

## 分析接口要点

`/devices/{device_id}/analysis` 要一次返回 11 个顶层字段，两个维度：

- 专注维度：`summary` / `trend` / `app_ranking` / `group_comparison`
- 错题维度：`error_stats` / `subject_distribution` / `knowledge_points` / `review_trend`
- 交叉分析：`efficiency_trend`

`efficiency_trend` 是把两边的日期对齐后拼出来的，前端双轴图靠它。

## 代码放这里

例如 `backend/main.py`、`backend/db.py`、`backend/models.py`。
