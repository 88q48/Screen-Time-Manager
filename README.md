# 使用时间统计看板（C 模块）

同一份数据，两种呈现方式：**Streamlit 看板**（自己调试用）和 **静态网页**（发给别人看）。

## 项目结构

```
.
├── mock_data.py        模拟后端数据（原始事件 + 聚合响应）
├── api_client.py       Streamlit 用的数据获取入口，mock / 真实 API 可切换
├── config.py           Streamlit 用的配置
├── charts.py           Streamlit 用的图表函数（Plotly）
├── app.py              Streamlit 主页面
├── requirements.txt    依赖清单
└── web/                静态网页（不用装 Python）
    ├── index.html      页面入口，双击即可打开
    ├── style.css       样式
    ├── config.js       网页配置：API 地址、设备 ID、是否用 mock
    ├── charts.js       图表配置（ECharts）
    ├── app.js          数据获取、渲染、使用建议
    ├── mock-data.js    由 gen_mock.py 生成，勿手改
    ├── gen_mock.py     从 mock_data.py 生成 mock-data.js
    └── lib/echarts.min.js  ECharts（本地版，断网也能用）
```

## 一、静态网页

**双击 `web/index.html` 就能看**，不需要装任何东西。

要改数据来源，编辑 `web/config.js`：

```js
USE_MOCK: true,                                  // false 表示请求后端
API_BASE_URL: "http://localhost:8000/api/v1",    // 后端地址
DEVICE_ID: "win_device_01",
```

`mock_data.py` 改动后，重新生成网页用的数据：

```bash
python web/gen_mock.py
```

## 二、Streamlit 看板

```bash
pip install -r requirements.txt
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。

## 数据来源

两个版本都读同一份数据，字段与后端 `/api/v1/devices/{device_id}/analysis` 对齐：

| 字段 | 说明 |
|---|---|
| `device_id` | 设备标识 |
| `period` | 统计时间范围（UTC） |
| `summary` | 总时长、日均、中位数、P90（秒） |
| `trend` | 每日总时长 |
| `app_ranking` | 应用排行（含类别） |
| `group_comparison` | 群体均值、中位数、P90、我的排名 |

## 使用建议的判断规则

两个版本用同一套规则：

- 日均 > 6 小时 → 明显偏长
- 日均 > 4 小时 → 略高于健康范围
- 娱乐类占比 > 40% → 建议调整使用结构
- 学习类 < 0.5 小时 → 偏少
- 都不触发 → 使用情况良好
