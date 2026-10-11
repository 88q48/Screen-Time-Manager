# 分析接口字段约定

前端（C 模块）已完成并用 mock 数据跑通。后端接口就绪后，只要字段名和本文一致，
把 `web/config.js` 里的 `USE_MOCK` 改成 `false` 就能直接对接。

---

## 一、接口路径与请求

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/v1/devices/{device_id}/analysis` | 取某个设备的分析结果 |

查询参数：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `days` | int | 7 | 统计最近多少天，范围 1~90 |

---

## 二、返回结构（顶层）

| 字段 | 类型 | 说明 |
|---|---|---|
| `device_id` | string | 设备标识，与路径参数一致 |
| `period` | object | 统计时间范围 |
| `summary` | object | 汇总指标 |
| `trend` | array | 每日总时长 |
| `app_ranking` | array | 应用排行 |
| `group_comparison` | object | 群体对比 |

---

## 三、各字段明细

### `period`

| 字段 | 类型 | 示例 |
|---|---|---|
| `start` | string（ISO 8601，UTC） | `"2026-10-05T00:00:00Z"` |
| `end` | string（ISO 8601，UTC） | `"2026-10-11T23:59:59Z"` |

### `summary`

| 字段 | 类型 | 单位 | 示例 |
|---|---|---|---|
| `total_duration_seconds` | number | 秒 | `93535` |
| `avg_daily_seconds` | number | 秒 | `13362.14` |
| `median_daily_seconds` | number | 秒 | `14241.0` |
| `p90_daily_seconds` | number | 秒 | `16132.2` |

### `trend`（数组，每项一天）

| 字段 | 类型 | 示例 |
|---|---|---|
| `date` | string（`YYYY-MM-DD`） | `"2026-10-05"` |
| `total_duration_seconds` | number（秒） | `7201` |

### `app_ranking`（数组，按时长从大到小）

| 字段 | 类型 | 示例 |
|---|---|---|
| `app_key` | string | `"douyin"` |
| `app_name` | string | `"抖音"` |
| `category` | string | `"娱乐"` |
| `duration_seconds` | number（秒） | `25725` |
| `percentage` | number | `27.5` |

### `group_comparison`

| 字段 | 类型 | 单位 | 示例 |
|---|---|---|---|
| `group_avg_daily_seconds` | number | 秒 | `12371.6` |
| `group_median_daily_seconds` | number | 秒 | `13317.1` |
| `group_p90_daily_seconds` | number | 秒 | `17620.5` |
| `my_rank` | number | — | `11` |
| `group_size` | number | 人 | `20` |

---

## 四、几个要一起定的点

1. **时长统一用秒**。整数或小数都行，换算成小时交给前端做。
2. **时间统一用 UTC**，ISO 8601 带 `Z` 结尾。
3. **`my_rank` 从 1 开始**，数字越小排名越靠前。
4. 后端没有数据时，`trend` 和 `app_ranking` **返回空数组**，不要返回 `null`。
5. **`category` 的取值要在客户端就定好**，建议固定为 `学习` / `娱乐` / `社交` / `工具` 这四类，
   别让后端靠 app_key 去猜。

---

## 五、前端各字段的用途

| 字段 | 用在哪里 |
|---|---|
| `summary` | 顶部四张指标卡（总时长、日均、中位数、P90） |
| `trend` | 每日使用趋势折线图 |
| `app_ranking` | 应用使用排行 + 类别占比饼图 |
| `group_comparison` | 个人 vs 群体对比图 + 排名文案 |
| `period` / `device_id` | 页面顶部的时间范围说明 |
