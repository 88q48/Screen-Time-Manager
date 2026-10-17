
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import closing

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from app.database import (
    get_connection,
    get_or_create_application,
    start_session,
    update_session_duration,
    finish_session,
    get_setting,
    set_setting,
    get_application_usage,
    initialize_database,
)


class TestDatabaseModule(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.db_path)
        self.conn = get_connection(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_default_settings(self):
        self.assertEqual(
            get_setting(self.conn, "idle_threshold_seconds"),
            "60",
        )

    def test_create_application(self):
        app_id = get_or_create_application(
            self.conn,
            app_key="test_app",
            app_name="测试应用",
            process_name="test.exe",
            exe_path="",
        )
        self.assertGreater(app_id, 0)

    def test_session_lifecycle_and_usage(self):
        app_id = get_or_create_application(
            self.conn,
            app_key="test_app",
            app_name="测试应用",
            process_name="test.exe",
            exe_path="",
        )

        session_id = start_session(self.conn, app_id)
        update_session_duration(self.conn, session_id, 30)
        finish_session(self.conn, session_id, 30, "test")

        usage = get_application_usage(self.conn)
        self.assertEqual(len(usage), 1)
        self.assertEqual(usage[0][0], "测试应用")
        self.assertEqual(usage[0][2], 30)

    def test_update_setting(self):
        set_setting(self.conn, "idle_threshold_seconds", "10")
        self.assertEqual(
            get_setting(self.conn, "idle_threshold_seconds"),
            "10",
        )

    def test_finish_session_rejects_negative_duration(self):
        app_id = get_or_create_application(
            self.conn,
            app_key="rollback_test",
            app_name="回滚测试应用",
            process_name="rollback.exe",
            exe_path="",
        )

        session_id = start_session(self.conn, app_id)
        self.conn.commit()

        with self.assertRaises(ValueError):
            finish_session(
                self.conn,
                session_id,
                -1,
                "test",
            )

        # 失败后，原会话应仍然保持未结束状态
        row = self.conn.execute(
            """
            SELECT ended_at, duration_seconds, end_reason
            FROM usage_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()

        self.assertIsNone(row[0])
        self.assertEqual(row[1], 0)
        self.assertIsNone(row[2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
