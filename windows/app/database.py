
import sqlite3
from datetime import datetime
from pathlib import Path
from contextlib import closing

# 项目根目录和默认数据库路径
PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_DIR / "tests" / "test_usage.db"


def get_connection(db_path=DEFAULT_DB_PATH):
    """创建数据库连接，并启用外键约束。"""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(db_path=DEFAULT_DB_PATH):
    """创建所需的数据表，不删除已有数据。"""
    with closing(get_connection(db_path)) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_key TEXT NOT NULL UNIQUE,
                app_name TEXT NOT NULL,
                process_name TEXT NOT NULL,
                exe_path TEXT,
                created_at TEXT NOT NULL
            );

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
            );

            CREATE INDEX IF NOT EXISTS
                idx_usage_sessions_application_id
            ON usage_sessions(application_id);

            CREATE INDEX IF NOT EXISTS
                idx_usage_sessions_started_at
            ON usage_sessions(started_at);

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('idle_threshold_seconds', '60');

            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('track_browsers', 'true');

            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('track_games', 'true');
            """
        )


def get_or_create_application(
    conn,
    app_key,
    app_name,
    process_name,
    exe_path="",
):
    """获取应用 ID；应用不存在时创建记录。"""
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
            app_key,
            app_name,
            process_name,
            exe_path,
            now,
        ),
    )

    row = conn.execute(
        """
        SELECT id
        FROM applications
        WHERE app_key = ?
        """,
        (app_key,),
    ).fetchone()

    if row is None:
        raise RuntimeError("无法创建或获取应用记录")

    return row[0]


def start_session(conn, application_id):
    """开始一段新的应用使用记录，返回记录 ID。"""
    started_at = datetime.now().isoformat(
        timespec="seconds"
    )

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
        (application_id, started_at),
    )

    return cursor.lastrowid


def update_session_duration(conn, session_id, seconds):
    """更新当前会话已累计的使用秒数。"""
    if seconds < 0:
        raise ValueError("使用时长不能为负数")

    conn.execute(
        """
        UPDATE usage_sessions
        SET duration_seconds = ?
        WHERE id = ? AND ended_at IS NULL
        """,
        (int(seconds), session_id),
    )


def finish_session(conn, session_id, duration_seconds, reason):
    """结束会话，并保存最终时长和结束原因。"""
    if duration_seconds < 0:
        raise ValueError("使用时长不能为负数")

    ended_at = datetime.now().isoformat(
        timespec="seconds"
    )

    cursor = conn.execute(
        """
        UPDATE usage_sessions
        SET ended_at = ?,
            duration_seconds = ?,
            end_reason = ?
        WHERE id = ? AND ended_at IS NULL
        """,
        (
            ended_at,
            int(duration_seconds),
            reason,
            session_id,
        ),
    )

    if cursor.rowcount == 0:
        raise ValueError(
            f"会话不存在或已经结束：{session_id}"
        )


def get_setting(conn, key, default=None):
    """读取设置；不存在时返回默认值。"""
    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?",
        (key,),
    ).fetchone()

    return row[0] if row else default


def set_setting(conn, key, value):
    """新增或更新设置。"""
    conn.execute(
        """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
        """,
        (key, str(value)),
    )


def get_application_usage(conn):
    """查询每个应用的累计使用秒数。"""
    return conn.execute(
        """
        SELECT
            a.app_name,
            a.process_name,
            COALESCE(SUM(u.duration_seconds), 0)
                AS total_seconds
        FROM applications AS a
        LEFT JOIN usage_sessions AS u
            ON u.application_id = a.id
        GROUP BY a.id
        ORDER BY total_seconds DESC
        """
    ).fetchall()
