# config.py
"""
统一管理 API 地址等配置。
开发时用本地/测试地址，联调时改这里即可。
"""

# 后端 API 基础地址
# 后端未就绪时，先用 mock；就绪后改成真实地址
API_BASE_URL = "http://localhost:8000/api/v1"

# 是否使用 mock 数据（True = 不调后端，用 mock_data.py）
USE_MOCK = True

# 请求超时（秒）
REQUEST_TIMEOUT = 10

# 当前设备 ID（A 那边生成后告诉你，或你自己模拟）
DEVICE_ID = "win_device_01"
