
import ctypes
import os
import sqlite3
import time
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

import psutil


# ==================== 基本配置 ====================

DB_PATH = Path(__file__).parent / "test_usage.db"

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


# ==================== 时间与前台应用检测 ====================

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
    """获取前台应用信息，无法识别时返回 None。"""
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
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            exe_path = ""

        # 优先用程序路径区分应用，路径不可用时使用进程名
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


# ==================== 数据库操作 ====================

def get_idle_threshold(conn):
    """读取数据库中的空闲阈值，没有配置时默认 60 秒。"""
    row = conn.execute(
        """
        SELECT value
        FROM settings
        WHERE key = ?
        """,
        ("idle_threshold_seconds",),
    ).fetchone()

    if row is None:
        return DEFAULT_IDLE_THRESHOLD_SECONDS

    try:
        value = int(row[0])
        if value < 1:
            raise ValueError("空闲阈值必须大于零")
        return value
    except (TypeError, ValueError):
        print("空闲阈值设置无效，使用默认值 60 秒")
        return DEFAULT_IDLE_THRESHOLD_SECONDS


def recover_unfinished_sessions(conn):
    """关闭上次异常退出时遗留的未结束记录。"""
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
        print(f"已处理上次遗留的记录：{cursor.rowcount} 条")


def start_session(conn, app):
    """创建或获取应用，并开始一段新的使用记录。"""
    now = datetime.now().isoformat(timespec="seconds")

    conn.execute(
        """
        INSERT OR IGNORE INTO applications
        (
            app_key,
            app_name,
            process_name,
            exe_path,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            app["app_key"],
            app["app_name"],
            app["process_name"],
            app["exe_path"],
            now,
        ),
    )

    row = conn.execute(
        """
        SELECT id
        FROM applications
        WHERE app_key = ?
        """,
        (app["app_key"],),
    ).fetchone()

    if row is None:
        raise RuntimeError("无法创建或获取应用记录")

    cursor = conn.execute(
        """
        INSERT INTO usage_sessions
        (
            application_id,
            started_at,
            ended_at,
            duration_seconds,
            end_reason
        )
        VALUES (?, ?, NULL, 0, NULL)
        """,
        (row[0], now),
    )

    conn.commit()

    return {
        "session_id": cursor.lastrowid,
        "app_key": app["app_key"],
        "app_name": app["app_name"],
        "started_at": now,
        "elapsed": 0.0,
        "last_tick": time.monotonic(),
    }


def save_session_duration(conn, active):
    """将当前累计秒数保存到数据库。"""
    conn.execute(
        """
        UPDATE usage_sessions
        SET duration_seconds = ?
        WHERE id = ?
        """,
        (
            int(active["elapsed"]),
            active["session_id"],
        ),
    )
    conn.commit()


def finish_session(conn, active, reason):
    """结束当前记录并保存最终时长。"""
    if active is None:
        return

    # 补上最后一次更新之后经过的时间
    now_mono = time.monotonic()
    active["elapsed"] += max(
        0.0,
        now_mono - active["last_tick"],
    )

    ended_at = datetime.now().isoformat(
        timespec="seconds"
    )

    conn.execute(
        """
        UPDATE usage_sessions
        SET ended_at = ?,
            duration_seconds = ?,
            end_reason = ?
        WHERE id = ?
        """,
        (
            ended_at,
            int(active["elapsed"]),
            reason,
            active["session_id"],
        ),
    )

    conn.commit()

    print(
        f"\n记录结束：{active['app_name']} "
        f"| {active['elapsed']:.1f} 秒 "
        f"| 原因：{reason}"
    )


# ==================== 计时主程序 ====================

def main():
    if not DB_PATH.exists():
        print("数据库不存在，请先运行 test_database.py")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

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
            # 先累计上一个采样周期的时间。
            # 这段时间归属于上一次检测到的活动应用。
            now_mono = time.monotonic()

            if active is not None:
                active["elapsed"] += max(
                    0.0,
                    now_mono - active["last_tick"],
                )
                active["last_tick"] = now_mono

                save_session_duration(conn, active)

            # 检测当前前台应用和空闲时间
            app = get_foreground_app()
            idle_seconds = get_idle_seconds()

            should_count = (
                app is not None
                and idle_seconds < idle_threshold
            )

            desired_key = (
                app["app_key"]
                if should_count
                else None
            )

            # 应用改变，或进入空闲状态：结束上一段记录
            if (
                active is not None
                and desired_key != active["app_key"]
            ):
                if idle_seconds >= idle_threshold:
                    reason = "idle"
                elif app is None:
                    reason = "unknown_foreground"
                else:
                    reason = "app_switch"

                finish_session(conn, active, reason)
                active = None

            # 当前有可统计的应用，但尚未建立记录
            if should_count and active is None:
                active = start_session(conn, app)

                print(
                    f"\n开始记录：{app['app_name']} "
                    f"({app['process_name']})"
                )

            # 显示当前状态
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
        try:
            if active is not None:
                finish_session(conn, active, "stopped")
        finally:
            conn.close()

        print("计时器已退出，数据库连接已关闭。")


if __name__ == "__main__":
    main()
