
import ctypes
import time

import psutil
from ctypes import wintypes


# 加载 Windows 用户界面 API
user32 = ctypes.WinDLL("user32", use_last_error=True)

# 获取当前前台窗口
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND

# 根据窗口获取所属进程 ID
user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD


def get_foreground_info():
    """获取当前前台窗口的基本信息。"""
    hwnd = user32.GetForegroundWindow()

    if not hwnd:
        return None

    pid = wintypes.DWORD(0)

    thread_id = user32.GetWindowThreadProcessId(
        hwnd,
        ctypes.byref(pid),
    )

    if not thread_id or not pid.value:
        return None

    try:
        process = psutil.Process(pid.value)

        return {
            "hwnd": hex(hwnd),
            "pid": pid.value,
            "name": process.name(),
            "path": process.exe(),
        }

    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return {
            "hwnd": hex(hwnd),
            "pid": pid.value,
            "name": "无法读取进程信息",
            "path": "无权限或进程已退出",
        }


def main():
    print("前台窗口识别测试")
    print("每秒检测一次，按 Ctrl+C 退出。")
    print("-" * 60)

    last_info = None

    try:
        while True:
            info = get_foreground_info()

            # 只有识别结果变化时才输出
            if info != last_info:
                print(f"\n时间：{time.strftime('%H:%M:%S')}")

                if info is None:
                    print("当前没有获取到前台窗口。")
                else:
                    print(f"窗口句柄：{info['hwnd']}")
                    print(f"进程 ID：{info['pid']}")
                    print(f"进程名称：{info['name']}")
                    print(f"程序路径：{info['path']}")

                last_info = info

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n测试结束。")


if __name__ == "__main__":
    main()