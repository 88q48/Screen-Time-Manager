
import ctypes
import os
import time
from contextlib import closing
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

import psutil

from app.database import (
    DEFAULT_DB_PATH,
    get_connection,
    get_setting,
    get_or_create_application,
    start_session as db_start_session,
    update_session_duration,
    finish_session as db_finish_session,
)


# ==================== 基本配置 ====================

DB_PATH = DEFAULT_DB_PATH

DEFAULT_IDLE_THRESHOLD_SECONDS = 60
POLL_INTERVAL_SECONDS = 0.5


# ==================== Windows API ====================

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

user32.GetForegroundWindow.restype = wintypes.HWND

user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD


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


# ==================== 前台与空闲检测 ====================

def get_idle_seconds():
    """获取用户距离最后一次键盘或鼠标输入的秒数。"""
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)

    if not user32.GetLastInputInfo(ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())

    now_ms = kernel32.GetTickCount()
    elapsed_ms = (now_ms - info.dwTime) & 0xFFFFFFFF

    return elapsed_ms / 1000.0


def get_foreground_app():
    """获取当前前台应用信息，无法识别时返回 None。"""
    hwnd = user32.GetForegroundWindow()

    if not hwnd:
        return None

    pid = wintypes.DWORD()

    user32.GetWindowThreadProcessId(
        hwnd,
        ctypes.byref(pid),
    )

    if not pid.value:
        return None

    try:
        process = psutil.Process(pid.value)
        process_name = process.name()

        try:
            exe_path = process.exe()
        except (
            psutil.AccessDenied,
            psutil.NoSuchProcess,
            OSError,
        ):
            exe_path = ""

        if exe_path:
            app_key = os.path.normcase(
                os.path.normpath(exe_path)
            ).casefold()
        else:
            app_key = process_name.casefold()

        return {
            "app_key": app_key,
            "app_name": Path(process_name).stem,
            "process_name": process_name,
            "exe_path": exe_path,
        }

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


# ==================== 记录管理 ====================

def get_idle_threshold(conn):
    """读取空闲阈值设置，默认 60 秒。"""
    value = get_setting(
        conn,
        "idle_threshold_seconds",
        str(DEFAULT_IDLE_THRESHOLD_SECONDS),
    )

    try:
        seconds = int(value)
        if seconds < 1:
            raise ValueError
        return seconds
    except (TypeError, ValueError):
        print("空闲阈值设置无效，使用默认值 60 秒")
        return DEFAULT_IDLE_THRESHOLD_SECONDS


def recover_unfinished_sessions(conn):
    """处理上一次运行遗留的未结束记录。"""
    now = datetime.now().isoformat(timespec="seconds")

    cursor = conn.execute(
        """
        UPDATE usage_sessions
        SET ended_at = ?,
            end_reason = ?
        WHERE ended_at IS NULL
        """,
        (now, "recovered_after_restart"),
    )

    if cursor.rowcount:
        conn.commit()
        print(f"已处理遗留记录：{cursor.rowcount} 条")


def start_tracking_session(conn, app):
    """创建或获取应用，并开始计时。"""
    app_id = get_or_create_application(
        conn,
        app_key=app["app_key"],
        app_name=app["app_name"],
        process_name=app["process_name"],
        exe_path=app["exe_path"],
    )

    session_id = db_start_session(conn, app_id)
    conn.commit()

    return {
        "session_id": session_id,
        "app_key": app["app_key"],
        "app_name": app["app_name"],
        "elapsed": 0.0,
        "last_tick": time.monotonic(),
    }

def save_session_duration(conn, active):
    """保存当前累计时长。"""
    update_session_duration(
        conn,
        active["session_id"],
        round(active["elapsed"]),
    )
    conn.commit()


def finish_tracking_session(conn, active, reason):
    """结束当前计时记录并保存最终时长。"""
    if active is None:
        return

    now_mono = time.monotonic()
    active["elapsed"] += max(
        0.0,
        now_mono - active["last_tick"],
    )

    db_finish_session(
        conn,
        active["session_id"],
        round(active["elapsed"]),
        reason,
    )
    conn.commit()

    print(
        f"\n记录结束：{active['app_name']} "
        f"| {active['elapsed']:.1f} 秒 "
        f"| 原因：{reason}"
    )


def process_tracking_sample(conn, active, app, idle_seconds, idle_threshold):
    """处理一次采样，决定结束、继续或开始计时。"""
    now_mono = time.monotonic()

    # 累计上一采样周期的时长
    if active is not None:
        active["elapsed"] += max(
            0.0,
            now_mono - active["last_tick"],
        )
        active["last_tick"] = now_mono
        save_session_duration(conn, active)

    # 判断当前是否应该统计
    should_count = (
        app is not None
        and idle_seconds < idle_threshold
    )

    desired_key = app["app_key"] if should_count else None

    # 应用切换、进入空闲或无法识别前台时，结束当前记录
    if active is not None and desired_key != active["app_key"]:
        if idle_seconds >= idle_threshold:
            reason = "idle"
        elif app is None:
            reason = "unknown_foreground"
        else:
            reason = "app_switch"

        finish_tracking_session(conn, active, reason)
        active = None

    # 为新前台应用开始记录
    if should_count and active is None:
        active = start_tracking_session(conn, app)

    return active

# ==================== 计时主程序 ====================

def main():
    if not DB_PATH.exists():
        print(f"数据库不存在：{DB_PATH}")
        print("请先初始化数据库。")
        return

    # closing 确保程序退出时关闭 SQLite 连接
    with closing(get_connection(DB_PATH)) as conn:
        active = None

        try:
            idle_threshold = get_idle_threshold(conn)
            recover_unfinished_sessions(conn)

            print("Windows 应用使用时长统计已启动")
            print(f"数据库：{DB_PATH.resolve()}")
            print(f"空闲阈值：{idle_threshold} 秒")
            print("浏览器和游戏均按普通应用统计")
            print("按 Ctrl+C 结束程序")
            print("-" * 80)

            
            while True:
                app = get_foreground_app()
                idle_seconds = get_idle_seconds()

                previous_session_id = (
                    active["session_id"]
                    if active is not None
                    else None
                )

                active = process_tracking_sample(
                    conn,
                    active,
                    app,
                    idle_seconds,
                    idle_threshold,
                )

                # 如果刚刚开始了一条新记录，显示应用名称
                if (
                    active is not None
                    and active["session_id"] != previous_session_id
                ):
                    print(
                        f"\n开始记录：{app['app_name']} "
                        f"({app['process_name']})"
                    )

                # 显示运行状态
                should_count = (
                    app is not None
                    and idle_seconds < idle_threshold
                )

                if should_count and active is not None:
                    status = "正在计时"
                    app_name = app["app_name"]
                    current_usage = active["elapsed"]

                elif idle_seconds >= idle_threshold:
                    status = "空闲暂停"
                    app_name = "-"
                    current_usage = 0.0

                else:
                    status = "无法识别前台程序"
                    app_name = "-"
                    current_usage = 0.0

                print(
                    f"\r前台：{app_name[:20]:20} "
                    f"| 空闲：{idle_seconds:5.1f}s "
                    f"| 本段：{current_usage:7.1f}s "
                    f"| {status}       ",
                    end="",
                    flush=True,
                )

                time.sleep(POLL_INTERVAL_SECONDS)


        except KeyboardInterrupt:
            print("\n\n正在结束计时……")

        except Exception as exc:
            print(f"\n计时发生错误：{exc}")
            raise

        finally:
            if active is not None:
                finish_tracking_session(
                    conn,
                    active,
                    "stopped",
                )

    print("计时器已退出，数据库连接已关闭。")


if __name__ == "__main__":
    main()
