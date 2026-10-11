
import ctypes
import time
from ctypes import wintypes

import psutil


# 加载 Windows API
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


# 前台窗口对应的进程 ID
user32.GetForegroundWindow.restype = wintypes.HWND

user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD


# 获取用户最后一次输入的时间
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


user32.GetLastInputInfo.argtypes = [
    ctypes.POINTER(LASTINPUTINFO)
]
user32.GetLastInputInfo.restype = wintypes.BOOL

kernel32.GetTickCount.restype = wintypes.DWORD


IDLE_THRESHOLD_SECONDS = 10


def get_idle_seconds():
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)

    if not user32.GetLastInputInfo(ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())

    now_ms = kernel32.GetTickCount()
    elapsed_ms = (now_ms - info.dwTime) & 0xFFFFFFFF

    return elapsed_ms / 1000.0


def get_foreground_app():
    hwnd = user32.GetForegroundWindow()

    if not hwnd:
        return None

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    if not pid.value:
        return None

    try:
        process = psutil.Process(pid.value)
        return process.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def main():
    print("软件使用计时核心测试")
    print("空闲阈值：10 秒")
    print("按 Ctrl+C 结束测试")
    print("-" * 65)

    usage_seconds = {}
    previous_time = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            elapsed = now - previous_time
            previous_time = now

            app_name = get_foreground_app()
            idle_seconds = get_idle_seconds()

            should_count = (
                app_name is not None
                and idle_seconds < IDLE_THRESHOLD_SECONDS
            )

            if should_count:
                usage_seconds[app_name] = (
                    usage_seconds.get(app_name, 0.0) + elapsed
                )

            if should_count:
                status = "正在计时"
            elif idle_seconds >= IDLE_THRESHOLD_SECONDS:
                status = "空闲暂停"
            elif app_name is None:
                status = "无法识别前台程序"
            else:
                status = "程序已排除"

            current_usage = (
                usage_seconds.get(app_name, 0.0)
                if app_name else 0.0
            )

            print(
                f"\r前台：{str(app_name):20.20} "
                f"| 空闲：{idle_seconds:5.1f}s "
                f"| 当前累计：{current_usage:7.1f}s "
                f"| {status}       ",
                end="",
                flush=True,
            )

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n测试结束，累计结果：")

        for name, seconds in sorted(
            usage_seconds.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            print(f"{name}: {seconds:.1f} 秒")


if __name__ == "__main__":
    main()
