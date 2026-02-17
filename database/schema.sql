-- ========================================
-- edu-flask 数据库表结构
-- ========================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',  -- admin / user
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
);

-- 系统配置表（键值对，替代 .env 和 config.json 中的非敏感配置）
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
);

-- 邮件任务配置表（每个账号的定时邮件任务）
CREATE TABLE IF NOT EXISTS email_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    username TEXT NOT NULL,              -- 关联 users 表的 username
    buildings TEXT NOT NULL,             -- JSON 数组，如 ["4","5","7"]
    recipients TEXT NOT NULL,            -- JSON 数组，如 ["a@test.com","b@test.com"]
    subject_prefix TEXT DEFAULT '',
    start_time TEXT DEFAULT '23:20:00',
    end_time TEXT DEFAULT '05:30:00',
    cron_expression TEXT DEFAULT '0 6 * * *',  -- 每天早上6点
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
);

-- 任务执行记录表
CREATE TABLE IF NOT EXISTS task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_task_id INTEGER,              -- 关联 email_tasks 表
    username TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending/running/success/failed/email_failed
    file_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    updated_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (email_task_id) REFERENCES email_tasks(id)
);

-- 权限表（控制账号可操作的功能）
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    permission TEXT NOT NULL,            -- 权限标识：query, download, admin, trigger_task
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
    UNIQUE(username, permission)
);

-- 操作日志表（记录用户登录和操作行为）
CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,                        -- 操作用户（登录失败时可能为空或为尝试的用户名）
    action TEXT NOT NULL,                 -- 操作类型：login/logout/login_failed/query/download/create_user/...
    detail TEXT,                          -- 操作详情（JSON 或文本描述）
    ip_address TEXT,                      -- 客户端 IP 地址
    created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
);

