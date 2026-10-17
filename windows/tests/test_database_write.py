
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "test_usage.db"


def main():
    # 检查数据库文件是否存在
    if not DB_PATH.exists():
        print("数据库不存在，请先运行 test_database.py")
        return

    now = datetime.now()
    started_at = now - timedelta(minutes=2)
    ended_at = now
    duration_seconds = int(
        (ended_at - started_at).total_seconds()
    )

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        # 创建或获取测试应用
        app_key = "test_database_write"
        app_name = "数据库写入测试"
        process_name = "test.exe"

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
                app_key,
                app_name,
                process_name,
                "",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        # 查询应用 ID
        row = conn.execute(
            """
            SELECT id
            FROM applications
            WHERE app_key = ?
            """,
            (app_key,),
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "无法获取应用记录，请检查数据库表结构"
            )

        application_id = row[0]

        # 写入一段模拟使用记录
        conn.execute(
            """
            INSERT INTO usage_sessions
            (
                application_id,
                started_at,
                ended_at,
                duration_seconds,
                end_reason
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                application_id,
                started_at.isoformat(timespec="seconds"),
                ended_at.isoformat(timespec="seconds"),
                duration_seconds,
                "test",
            ),
        )

        # 提交事务，保存数据
        conn.commit()

        print("数据库写入成功！")
        print(f"数据库路径：{DB_PATH.resolve()}")
        print(f"应用：{app_name}")
        print(f"进程名称：{process_name}")
        print(
            f"开始时间：{started_at:%Y-%m-%d %H:%M:%S}"
        )
        print(
            f"结束时间：{ended_at:%Y-%m-%d %H:%M:%S}"
        )
        print(f"使用时长：{duration_seconds} 秒")

        # 查询并显示刚刚保存的记录
        print("\n最新使用记录：")
        result = conn.execute(
            """
            SELECT
                a.app_name,
                u.started_at,
                u.ended_at,
                u.duration_seconds,
                u.end_reason
            FROM usage_sessions AS u
            JOIN applications AS a
                ON u.application_id = a.id
            ORDER BY u.id DESC
            LIMIT 1
            """
        ).fetchone()

        if result:
            print(f"应用名称：{result[0]}")
            print(f"开始时间：{result[1]}")
            print(f"结束时间：{result[2]}")
            print(f"使用时长：{result[3]} 秒")
            print(f"结束原因：{result[4]}")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
