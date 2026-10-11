# backend — 后端接口

（B 模块，尚未开始）

## 负责什么

接收客户端上传的使用记录，统一统计口径，向前端返回分析结果。

## 待实现的接口

见 [`../docs/api-fields.md`](../docs/api-fields.md)，前缀统一为 `/api/v1`：

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/v1/events/batch` | 批量上传活跃时间记录 |
| GET | `/api/v1/devices/{device_id}/sync` | 获取服务器端配置与同步信息 |
| GET | `/api/v1/devices/{device_id}/analysis` | 获取使用时间分析结果 |
| POST | `/api/v1/devices/register` | 注册或登记设备 |
| GET | `/api/v1/health` | 检查服务器是否可用 |

## 上传数据格式

```json
{
  "event_id": "evt_a102",
  "device_id": "win_device_01",
  "platform": "windows",
  "app_key": "chrome",
  "start_at": "2026-10-10T09:00:00Z",
  "end_at": "2026-10-10T09:30:00Z",
  "duration_seconds": 1800
}
```

- `event_id`：每条记录唯一，上传重试时保持不变，用于去重
- `device_id`：客户端首次启动时生成并持久化，不使用硬件序列号
- `platform`：`windows` 或 `android`
- `app_key`：稳定的应用标识，不依赖窗口标题
- `start_at` / `end_at`：UTC，ISO 8601
- `duration_seconds`：整数秒

## 代码放这里

建好后把代码放在本目录下，例如 `backend/main.py`、`backend/db.py`。
