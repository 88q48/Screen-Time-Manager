# 错题管理与学情诊断系统

把「错题摄入」与「专注投入」放在同一张表上对比，回答两个问题：
错在哪、学得高不高效。

## 目录结构

```
.
├── dashboard/        C 模块：学情诊断看板
│   ├── app.py              Streamlit 主页面（两个 Tab）
│   ├── charts.py           图表函数（Plotly，9 张图）
│   ├── config.py           配置：API 地址、设备 ID、是否用 mock
│   ├── api_client.py       数据获取入口，mock / 真实 API 可切换
│   ├── mock_data.py        过程数据：应用使用时长、专注趋势
│   ├── error_mock.py       结果数据：错题、掌握率、复习进度
│   └── web/                静态网页（ECharts，双击即可打开）
│
├── windows/          A 模块：Windows 采集客户端
│   └── tests/              前台窗口识别、空闲检测、计时、本地数据库
│
├── backend/          B 模块：后端接口
│   └── README.md           接口清单与上传格式
│
└── docs/
    └── api-fields.md       分析接口字段约定
```

## 快速开始

### 静态网页

双击 `dashboard/web/index.html`，不需要安装任何东西。

页面分两个 Tab：

- **错题诊断**：累计错题、掌握率、各科分布雷达图、知识点薄弱榜、消化漏斗
- **专注与效率**：专注时长、时长 vs 产出双轴图、个人 vs 群体

连真实后端时改 `dashboard/web/config.js`：

```js
USE_MOCK: false,
API_BASE_URL: "http://localhost:8000/api/v1",
```

### Streamlit 看板

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

浏览器打开 `http://localhost:8501`，同样是两个 Tab。

### 生成网页用的 mock 数据

改动 `dashboard/mock_data.py` 或 `dashboard/error_mock.py` 之后重新生成：

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
                ├─→ 后端 ─→ 学情诊断看板
安卓客户端    ─┘
```

客户端只管采集上传，错题与时长两套数据都由后端统一口径后返回。

## 两条分析主线

**错题维度**：错题总数、已掌握、待复习、掌握率、各科分布、知识点薄弱项、每日新增与消灭。

**效率维度**：把专注时长和消灭错题数放在同一张双轴图上。柱子高而折线低的日子，就是投入产出不匹配的日子，系统会点名提示。

## 分支说明

主开发分支是 `main`。

| 分支 | 状态 |
|---|---|
| `main` | 主线，保持可用 |
| `master` | 早期误建，内容已并入 main，已废弃 |
| `windows` | 早期分支，内容已并入 main，已废弃 |
