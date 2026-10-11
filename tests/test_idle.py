
import ctypes
import time
from ctypes import wintypes


# 加载 Windows API
user32 = ctypes.WinDLL("user32", use_last_error=True)


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


# 设置 Windows API 的参数和返回值类型
user32.GetLastInputInfo.argtypes = [
    ctypes.POINTER(LASTINPUTINFO)
]
user32.GetLastInputInfo.restype = wintypes.BOOL


# 临时测试阈值：60秒
IDLE_THRESHOLD_SECONDS = 60


def get_idle_seconds():
    """获取距离上一次键盘或鼠标输入的秒数。"""
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)

    success = user32.GetLastInputInfo(ctypes.byref(info))

    if not success:
        raise ctypes.WinError(ctypes.get_last_error())

    # dwTime 和 GetTickCount 都使用 Windows 毫秒计数
    # 使用无符号 32 位减法处理计数器回绕
    now_ms = ctypes.windll.kernel32.GetTickCount()
    elapsed_ms = (now_ms - info.dwTime) & 0xFFFFFFFF

    return elapsed_ms / 1000.0


def main():
    print("Windows 空闲检测测试")
    print(f"临时阈值：{IDLE_THRESHOLD_SECONDS} 秒")
    print("移动鼠标或按键后观察状态变化，按 Ctrl+C 退出。")
    print("-" * 50)

    last_state = None

    try:
        while True:
            idle_seconds = get_idle_seconds()

            if idle_seconds >= IDLE_THRESHOLD_SECONDS:
                state = "IDLE（空闲，达到阈值）"
            else:
                state = "ACTIVE（未达到空闲阈值）"

            print(
                f"\r空闲时间：{idle_seconds:6.1f} 秒 | 状态：{state}    ",
                end="",
                flush=True,
            )

            if state != last_state:
                print()
                last_state = state

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n测试结束。")


if __name__ == "__main__":
    main()
