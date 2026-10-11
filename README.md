# Screen Time Manager

收集应用使用时长，后端统一统计口径，前端做数据展示。

## 目录结构

```
.
├── dashboard/     C 模块：数据看板（Streamlit + 静态网页）
│   ├── app.py             Streamlit 主页面
│   ├── charts.py          图表函数（Plotly）
│   ├── config.py          配置：API 地址、设备 ID、是否用 mock
│   ├── api_client.py      数据获取入口，mock / 真实 API 可切换
│   ├── mock_data.py       模拟后端返回的数据
│   └── web/               静态网页（ECharts，不需要 Python）
│
├── windows/       A 模块：Windows 采集客户端
│   └── tests/             前台窗口识别、空闲检测、计时、本地数据库
│
├── backend/       B 模块：后端接口（尚未开始）
│   └── README.md          接口清单与上传格式
│
└── docs/
    └── api-fields.md      分析接口字段约定
```

## 快速开始

### 静态网页（最简单）

双击 `dashboard/web/index.html` 即可，不需要安装任何东西。

要连真实后端时，改 `dashboard/web/config.js`：

```js
USE_MOCK: false,
API_BASE_URL: "http://localhost:8000/api/v1",
```

### Streamlit 看板

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

浏览器打开 `http://localhost:8501`。

### 生成网页用的 mock 数据

改动 `dashboard/mock_data.py` 之后重新生成：

```bash
python dashboard/web/gen_mock.py
```

### Windows 采集测试

```bash
cd windows/tests
python test.py              # 前台窗口识别
python test_idle.py         # 空闲检测
python text_usage_timer.py  # 计时核心
python test_database.py     # 建本地数据库
```

前三个是持续运行的，按 `Ctrl+C` 退出。

## 数据流

```
Windows 客户端 ─┐
                ├─→ 后端 ─→ 看板
安卓客户端    ─┘
```

客户端只负责采集和上传，统计口径由后端统一，避免两端各算一套。

上传格式与返回字段见 [`docs/api-fields.md`](docs/api-fields.md)。

## 分支说明

主开发分支是 `main`。每个人在自己的分支上写，写完合回 `main`。

| 分支 | 状态 |
|---|---|
| `main` | 主线，保持可用 |
| `dashboard` | C 模块开发分支（已并入 main 后停用） |
| `master` | 早期误建，内容已并入 main，**已废弃** |
| `windows` | 早期分支，内容已并入 main，**已废弃** |
