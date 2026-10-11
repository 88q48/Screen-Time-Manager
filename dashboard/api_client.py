# api_client.py
import requests
from config import API_BASE_URL, USE_MOCK, REQUEST_TIMEOUT, DEVICE_ID
from mock_data import get_mock_response_from_events


def fetch_analysis(device_id=DEVICE_ID):
    """
    获取分析数据。
    USE_MOCK=True 时返回 mock 数据；
    USE_MOCK=False 时调真实后端。
    """
    if USE_MOCK:
        return get_mock_response_from_events(device_id=device_id)

    url = f"{API_BASE_URL}/devices/{device_id}/analysis"
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)

    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 401:
        raise Exception("未授权：请检查 token 或设备注册")
    elif resp.status_code == 404:
        raise Exception(f"设备 {device_id} 没有数据")
    elif resp.status_code == 500:
        raise Exception("后端错误，请查看后端日志")
    else:
        raise Exception(f"请求失败：{resp.status_code} {resp.text}")


def check_health():
    """检查后端是否可用"""
    if USE_MOCK:
        return {"status": "mock"}
    url = f"{API_BASE_URL}/health"
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    return resp.json()