import sqlite3
import json
import os
import logging


class Database:
    def __init__(self, db_path='data/edu.db'):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        """根据 schema.sql 初始化表结构"""
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if not os.path.exists(schema_path):
            self.logger.error(f"schema.sql 不存在: {schema_path}")
            return
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        conn = self._get_conn()
        try:
            conn.executescript(schema_sql)
            conn.commit()
            # 迁移：为已有 users 表添加 allowed_buildings 字段
            columns = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
            if 'allowed_buildings' not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN allowed_buildings TEXT DEFAULT ''")
                conn.commit()
                self.logger.info("已为 users 表添加 allowed_buildings 字段")
        finally:
            conn.close()

    # ==================== 用户相关 ====================

    def get_user(self, username):
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_users(self):
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def verify_user(self, username, password):
        user = self.get_user(username)
        if user and user['enabled'] and user['password'] == password:
            return user
        return None

    def update_user(self, username, **kwargs):
        allowed = {'password', 'role', 'enabled', 'allowed_buildings'}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        set_clause = ', '.join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [username]
        conn = self._get_conn()
        try:
            conn.execute(
                f"UPDATE users SET {set_clause}, updated_at = datetime('now','localtime') WHERE username = ?",
                values
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def get_user_buildings(self, username):
        """获取用户可操作的楼栋列表，返回列表；空列表表示全部可操作"""
        user = self.get_user(username)
        if not user:
            return []
        val = user.get('allowed_buildings', '')
        if not val:
            return []  # 空表示全部
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_user_buildings(self, username, buildings):
        """设置用户可操作的楼栋列表，空列表表示全部可操作"""
        val = json.dumps(buildings) if buildings else ''
        return self.update_user(username, allowed_buildings=val)

    def create_user(self, username, password, role='user'):
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def delete_user(self, username):
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.execute("DELETE FROM permissions WHERE username = ?", (username,))
            conn.commit()
            return True
        finally:
            conn.close()

    # ==================== 系统配置相关 ====================

    def get_config(self, key, default=None):
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT config_value FROM system_config WHERE config_key = ?", (key,)
            ).fetchone()
            return row['config_value'] if row else default
        finally:
            conn.close()

    def get_all_config(self):
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM system_config ORDER BY id").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def set_config(self, key, value, description=None):
        conn = self._get_conn()
        try:
            existing = conn.execute(
                "SELECT id FROM system_config WHERE config_key = ?", (key,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE system_config SET config_value = ?, updated_at = datetime('now','localtime') WHERE config_key = ?",
                    (value, key)
                )
            else:
                conn.execute(
                    "INSERT INTO system_config (config_key, config_value, description) VALUES (?, ?, ?)",
                    (key, value, description)
                )
            conn.commit()
            return True
        finally:
            conn.close()

    def get_config_dict(self):
        """以字典形式返回所有配置 {key: value}"""
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT config_key, config_value FROM system_config").fetchall()
            return {r['config_key']: r['config_value'] for r in rows}
        finally:
            conn.close()

    # ==================== 邮件任务配置相关 ====================

    def get_all_email_tasks(self):
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM email_tasks ORDER BY id").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d['buildings'] = json.loads(d['buildings'])
                d['recipients'] = json.loads(d['recipients'])
                result.append(d)
            return result
        finally:
            conn.close()

    def get_email_task(self, task_id):
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM email_tasks WHERE id = ?", (task_id,)).fetchone()
            if row:
                d = dict(row)
                d['buildings'] = json.loads(d['buildings'])
                d['recipients'] = json.loads(d['recipients'])
                return d
            return None
        finally:
            conn.close()

    def get_enabled_email_tasks(self):
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM email_tasks WHERE enabled = 1 ORDER BY id").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d['buildings'] = json.loads(d['buildings'])
                d['recipients'] = json.loads(d['recipients'])
                result.append(d)
            return result
        finally:
            conn.close()

    def create_email_task(self, task_name, username, buildings, recipients,
                          subject_prefix='', start_time='23:20:00', end_time='05:30:00',
                          cron_expression='0 6 * * *', enabled=1):
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO email_tasks
                   (task_name, username, buildings, recipients, subject_prefix,
                    start_time, end_time, cron_expression, enabled)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (task_name, username, json.dumps(buildings, ensure_ascii=False),
                 json.dumps(recipients, ensure_ascii=False),
                 subject_prefix, start_time, end_time, cron_expression, enabled)
            )
            conn.commit()
            return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        finally:
            conn.close()

    def update_email_task(self, task_id, **kwargs):
        allowed = {'task_name', 'username', 'buildings', 'recipients', 'subject_prefix',
                    'start_time', 'end_time', 'cron_expression', 'enabled'}
        fields = {}
        for k, v in kwargs.items():
            if k not in allowed:
                continue
            if k in ('buildings', 'recipients') and isinstance(v, list):
                fields[k] = json.dumps(v, ensure_ascii=False)
            else:
                fields[k] = v
        if not fields:
            return False
        set_clause = ', '.join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [task_id]
        conn = self._get_conn()
        try:
            conn.execute(
                f"UPDATE email_tasks SET {set_clause}, updated_at = datetime('now','localtime') WHERE id = ?",
                values
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def delete_email_task(self, task_id):
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM email_tasks WHERE id = ?", (task_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    # ==================== 任务执行记录相关 ====================

    def create_task_log(self, email_task_id, username, status='pending'):
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO task_logs (email_task_id, username, status) VALUES (?, ?, ?)",
                (email_task_id, username, status)
            )
            conn.commit()
            return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        finally:
            conn.close()

    def update_task_log(self, log_id, status, file_path=None, error_message=None):
        conn = self._get_conn()
        try:
            conn.execute(
                """UPDATE task_logs
                   SET status = ?, file_path = ?, error_message = ?, updated_at = datetime('now','localtime')
                   WHERE id = ?""",
                (status, file_path, error_message, log_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_task_logs(self, limit=50, username=None):
        conn = self._get_conn()
        try:
            if username:
                rows = conn.execute(
                    """SELECT tl.*, et.task_name FROM task_logs tl
                       LEFT JOIN email_tasks et ON tl.email_task_id = et.id
                       WHERE tl.username = ?
                       ORDER BY tl.created_at DESC LIMIT ?""",
                    (username, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT tl.*, et.task_name FROM task_logs tl
                       LEFT JOIN email_tasks et ON tl.email_task_id = et.id
                       ORDER BY tl.created_at DESC LIMIT ?""",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== 权限相关 ====================

    def get_user_permissions(self, username):
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT permission FROM permissions WHERE username = ? AND enabled = 1",
                (username,)
            ).fetchall()
            return [r['permission'] for r in rows]
        finally:
            conn.close()

    def get_all_permissions(self):
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM permissions ORDER BY username, permission").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def set_user_permissions(self, username, permissions):
        """重置用户权限列表"""
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM permissions WHERE username = ?", (username,))
            for perm in permissions:
                conn.execute(
                    "INSERT INTO permissions (username, permission) VALUES (?, ?)",
                    (username, perm)
                )
            conn.commit()
            return True
        finally:
            conn.close()

    def has_permission(self, username, permission):
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT 1 FROM permissions WHERE username = ? AND permission = ? AND enabled = 1",
                (username, permission)
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    # ==================== 操作日志相关 ====================

    def create_operation_log(self, username, action, detail=None, ip_address=None):
        """记录用户操作日志"""
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO operation_logs (username, action, detail, ip_address) VALUES (?, ?, ?, ?)",
                (username, action, detail, ip_address)
            )
            conn.commit()
        except Exception as e:
            self.logger.warning(f"记录操作日志失败: {e}")
        finally:
            conn.close()

    def get_operation_logs(self, limit=100, username=None):
        """查询操作日志"""
        conn = self._get_conn()
        try:
            if username:
                rows = conn.execute(
                    "SELECT * FROM operation_logs WHERE username = ? ORDER BY created_at DESC LIMIT ?",
                    (username, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM operation_logs ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

