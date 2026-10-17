
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import closing

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from app.database import (
    get_connection,
    initialize_database,
    get_application_usage,
    get_or_create_application,
)
from app.usage_tracker import (
    recover_unfinished_sessions,
    start_tracking_session,
    save_session_duration,
    finish_tracking_session,
)


class TestUsageTracker(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_usage.db"
        initialize_database(self.db_path)
        self.conn = get_connection(self.db_path)

        self.app = {
            "app_key": "test_app",
            "app_name": "测试应用",
            "process_name": "test.exe",
            "exe_path": "",
        }

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_start_and_finish_session(self):
        active = start_tracking_session(self.conn, self.app)
        self.assertIsNotNone(active)
        self.assertIn("session_id", active)

        active["elapsed"] = 5.0
        active["last_tick"] = __import__("time").monotonic()

        finish_tracking_session(self.conn, active, "test")

        usage = get_application_usage(self.conn)
        self.assertEqual(len(usage), 1)
        self.assertEqual(usage[0][0], "测试应用")
        self.assertGreaterEqual(usage[0][2], 5)

    def test_save_session_duration(self):
        active = start_tracking_session(self.conn, self.app)
        active["elapsed"] = 12.0

        save_session_duration(self.conn, active)

        row = self.conn.execute(
            "SELECT duration_seconds FROM usage_sessions WHERE id = ?",
            (active["session_id"],),
        ).fetchone()

        self.assertEqual(row[0], 12)

        finish_tracking_session(self.conn, active, "test")

    def test_recover_unfinished_sessions(self):
        app_id = get_or_create_application(
            self.conn,
            app_key="old_app",
            app_name="旧应用",
            process_name="old.exe",
            exe_path="",
        )

        # 创建一条未结束的记录
        self.conn.execute(
            """
            INSERT INTO usage_sessions
                (application_id, started_at, duration_seconds)
            VALUES (?, datetime('now'), 10)
            """,
            (app_id,),
        )

        # 创建一条已经正常结束的记录
        self.conn.execute(
            """
            INSERT INTO usage_sessions
                (application_id, started_at, ended_at,
                duration_seconds, end_reason)
            VALUES (?, datetime('now'), datetime('now'),
                    20, 'app_switch')
            """,
            (app_id,),
        )
        self.conn.commit()

        # 执行恢复
        recover_unfinished_sessions(self.conn)
        recover_unfinished_sessions(self.conn)
        
        rows = self.conn.execute(
            """
            SELECT ended_at, end_reason, duration_seconds
            FROM usage_sessions
            WHERE application_id = ?
            ORDER BY rowid
            """,
            (app_id,),
        ).fetchall()

        # 第一条遗留记录应被恢复
        self.assertEqual(len(rows), 2)
        self.assertIsNotNone(rows[0][0])
        self.assertEqual(rows[0][1], "recovered_after_restart")
        self.assertEqual(rows[0][2], 10)

        # 第二条正常结束的记录应保持不变
        self.assertIsNotNone(rows[1][0])
        self.assertEqual(rows[1][1], "app_switch")
        self.assertEqual(rows[1][2], 20)

    def test_app_switch(self):
        from app.usage_tracker import process_tracking_sample

        code_app = {
            "app_key": "code",
            "app_name": "Code",
            "process_name": "Code.exe",
            "exe_path": "",
        }
        edge_app = {
            "app_key": "edge",
            "app_name": "msedge",
            "process_name": "msedge.exe",
            "exe_path": "",
        }

        active = start_tracking_session(self.conn, code_app)

        # 模拟切换到 Edge
        active = process_tracking_sample(
            self.conn,
            active,
            edge_app,
            idle_seconds=0,
            idle_threshold=60,
        )

        self.assertIsNotNone(active)
        self.assertEqual(active["app_key"], "edge")

        rows = self.conn.execute(
            """
            SELECT a.app_name, s.end_reason, s.ended_at
            FROM usage_sessions s
            JOIN applications a ON a.id = s.application_id
            ORDER BY s.id
            """
        ).fetchall()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "Code")
        self.assertEqual(rows[0][1], "app_switch")
        self.assertIsNotNone(rows[0][2])
        self.assertEqual(rows[1][0], "msedge")
        self.assertIsNone(rows[1][2])

        # 结束新会话，避免留下未结束的测试记录
        finish_tracking_session(self.conn, active, "test_cleanup")
    
    def test_idle_stops_tracking(self):
        from app.usage_tracker import process_tracking_sample

        code_app = {
            "app_key": "code",
            "app_name": "Code",
            "process_name": "Code.exe",
            "exe_path": "",
        }

        active = start_tracking_session(self.conn, code_app)

        # 模拟空闲时间已经达到 10 秒阈值
        active = process_tracking_sample(
            self.conn,
            active,
            code_app,
            idle_seconds=10,
            idle_threshold=10,
        )

        self.assertIsNone(active)

        row = self.conn.execute(
            """
            SELECT end_reason, ended_at
            FROM usage_sessions
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        self.assertEqual(row[0], "idle")
        self.assertIsNotNone(row[1])

        # 空闲期间不应新建计时会话
        count = self.conn.execute(
            "SELECT COUNT(*) FROM usage_sessions"
        ).fetchone()[0]

        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
