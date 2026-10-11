
import sqlite3
from pathlib import Path


# 临时测试数据库，正式程序不会使用这个路径
DB_PATH = Path(__file__).with_name("test_usage.db")


def create_database():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_key TEXT NOT NULL UNIQUE,
                app_name TEXT NOT NULL,
                process_name TEXT NOT NULL,
                exe_path TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                end_reason TEXT,
                FOREIGN KEY (application_id)
                    REFERENCES applications(id)
                    ON DELETE CASCADE,
                CHECK (duration_seconds >= 0),
                CHECK (
                    ended_at IS NULL
                    OR ended_at >= started_at
                )
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_sessions_application_start
            ON usage_sessions(application_id, started_at)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        conn.execute("""
            INSERT INTO settings (key, value)
            VALUES ('idle_threshold_seconds', '60')
            ON CONFLICT(key) DO NOTHING
        """)

        conn.execute("""
            INSERT INTO settings (key, value)
            VALUES ('track_browsers', 'true')
            ON CONFLICT(key) DO NOTHING
        """)

        conn.execute("""
            INSERT INTO settings (key, value)
            VALUES ('track_games', 'true')
            ON CONFLICT(key) DO NOTHING
        """)

        conn.commit()


def main():
    create_database()

    with sqlite3.connect(DB_PATH) as conn:
        tables = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        print("数据库创建成功！")
        print(f"数据库位置：{DB_PATH.resolve()}")
        print("\n已创建的数据表：")

        for (table_name,) in tables:
            print(f"- {table_name}")

        print("\n当前设置：")
        settings = conn.execute("""
            SELECT key, value
            FROM settings
            ORDER BY key
        """).fetchall()

        for key, value in settings:
            print(f"{key} = {value}")


if __name__ == "__main__":
    main()
