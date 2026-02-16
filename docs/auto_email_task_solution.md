# 自动邮件定时任务 & 管理页面 — 整体方案

## 1. 功能概述

本次功能扩展为 edu-flask 系统新增两大能力：

1. **自动邮件定时任务**：按配置的时间自动查询公寓晚归数据、生成 Excel 文件、发送到指定邮箱
2. **后台管理页面**：统一管理用户、权限、邮件任务、系统配置、调度器，以及查看任务执行记录

### 核心价值

- 原来需要每天手动登录系统查询下载 → 现在系统自动完成并发送到邮箱
- 原来配置分散在 `.env` + `config.json` → 现在统一存储在 SQLite，通过管理页面在线修改
- 原来没有权限控制 → 现在支持细粒度的用户权限管理

---

## 2. 技术架构

### 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | Flask + Blueprint | 路由分离，管理页面独立模块 |
| 数据存储 | SQLite | 用户、配置、任务、日志统一存储 |
| 定时调度 | APScheduler (BackgroundScheduler) | 后台线程执行，支持 Cron 表达式 |
| 数据采集 | Selenium WebDriver | 自动登录公寓系统抓取晚归数据 |
| 邮件发送 | smtplib + MIME | 支持 TLS 加密、附件发送 |
| 前端 | 原生 HTML/CSS/JavaScript | 无额外框架依赖 |

### 项目结构

```
edu-flask/
├── app.py                          # Flask 主应用（集成调度器、注册 Blueprint）
├── database/
│   ├── __init__.py
│   ├── schema.sql                  # 数据库表结构（提交 Git）
│   ├── init_data.sql               # 初始化数据（不提交，含敏感信息）
│   └── db.py                       # Database 类，封装所有 CRUD 操作
├── scheduler/
│   ├── __init__.py
│   ├── scheduler.py                # SchedulerManager 定时调度管理
│   ├── task_manager.py             # TaskManager 任务执行逻辑
│   └── email_sender.py             # EmailSender 邮件发送
├── routes/
│   ├── __init__.py
│   ├── auth.py                     # login_required / admin_required 装饰器
│   └── admin.py                    # 管理页面 Blueprint（所有 /admin/ 路由）
├── templates/
│   ├── admin.html                  # 管理页面前端（6 个 Tab）
│   ├── dashboard.html              # 主面板（管理员显示管理入口）
│   └── login.html                  # 登录页
├── data/
│   └── edu.db                      # SQLite 数据库文件（不提交）
└── get_excel_data_curr/            # 原有 Selenium 数据采集模块
    ├── main.py                     # process() 核心函数
    ├── ConfigTool.py               # 配置读取工具
    └── gen_excel_data_v1.py        # Excel 生成
```

---

## 3. 数据库设计

共 5 张表，使用 `CREATE TABLE IF NOT EXISTS` 保证幂等性。

### 3.1 users — 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| username | TEXT UNIQUE | 用户名 |
| password | TEXT | 密码 |
| role | TEXT | 角色：`admin` / `user` |
| enabled | INTEGER | 是否启用：1=是 0=否 |

### 3.2 system_config — 系统配置表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| config_key | TEXT UNIQUE | 配置键 |
| config_value | TEXT | 配置值（复杂数据用 JSON 字符串） |
| description | TEXT | 配置说明 |

替代了原来分散在 `.env` 和 `config.json` 中的所有配置项。

### 3.3 email_tasks — 邮件任务配置表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| task_name | TEXT | 任务名称 |
| username | TEXT | 关联用户 |
| buildings | TEXT | 查询楼栋（JSON 数组，如 `["4","5","7"]`） |
| recipients | TEXT | 收件人（JSON 数组） |
| subject_prefix | TEXT | 邮件主题前缀 |
| start_time | TEXT | 查询开始时间，默认 `23:20:00` |
| end_time | TEXT | 查询结束时间，默认 `05:30:00` |
| cron_expression | TEXT | Cron 表达式，默认 `0 6 * * *`（每天 6:00） |
| enabled | INTEGER | 是否启用 |

### 3.4 task_logs — 任务执行记录表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| email_task_id | INTEGER FK | 关联邮件任务 |
| username | TEXT | 执行用户 |
| status | TEXT | 状态：`pending` / `running` / `success` / `failed` / `email_failed` |
| file_path | TEXT | 生成的文件路径 |
| error_message | TEXT | 错误信息 |

### 3.5 permissions — 权限表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| username | TEXT | 用户名 |
| permission | TEXT | 权限标识：`query` / `download` / `admin` / `trigger_task` |
| enabled | INTEGER | 是否启用 |
| | UNIQUE | (username, permission) 联合唯一 |

---

## 4. 模块设计

### 4.1 数据库层 — `database/db.py`

`Database` 类封装了所有数据库操作，初始化时自动执行 `schema.sql` 建表。

**核心方法：**

| 方法 | 说明 |
|------|------|
| `verify_user(username, password)` | 验证登录，检查用户名+密码+启用状态 |
| `get_config(key)` / `set_config(key, value)` | 读写系统配置 |
| `get_all_email_tasks()` / `get_enabled_email_tasks()` | 获取邮件任务列表 |
| `create_email_task(...)` / `update_email_task(...)` | 任务 CRUD |
| `create_task_log(...)` / `update_task_log(...)` | 记录任务执行日志 |
| `get_user_permissions(username)` / `set_user_permissions(...)` | 权限管理 |

JSON 数组字段（buildings、recipients）在读写时自动序列化/反序列化。

### 4.2 邮件发送 — `scheduler/email_sender.py`

`EmailSender` 类负责 SMTP 邮件发送：

- `from_db(db)` 类方法：从数据库读取 SMTP 配置创建实例
- `send_email(recipients, subject, body, attachments)` ：发送带附件的邮件
- 支持 TLS 加密，返回 `(success, message)` 元组

### 4.3 任务管理器 — `scheduler/task_manager.py`

`TaskManager` 是任务执行的核心，负责串联整个流程：

1. 创建执行日志（状态 `running`）
2. 构造请求参数，调用 `process()` 函数生成 Excel
3. 调用 `EmailSender` 发送邮件（附件为生成的 Excel）
4. 更新执行日志（`success` / `failed` / `email_failed`）

`execute_all_enabled_tasks()` 遍历所有启用任务，任务间间隔 2 秒避免并发压力。

### 4.4 定时调度器 — `scheduler/scheduler.py`

`SchedulerManager` 基于 APScheduler 的 `BackgroundScheduler`：

- `start()`：读取 `scheduler_enabled` 配置，为每个启用的邮件任务创建 `CronTrigger` 调度
- `stop()`：停止调度器
- `reload()`：重新加载（先停后启），用于配置变更后刷新
- `get_jobs()`：返回当前所有调度任务及下次执行时间

Cron 表达式格式：`分 时 日 月 星期`，如 `0 6 * * *` 表示每天 06:00。

### 4.5 路由层 — `routes/admin.py`

使用 Flask Blueprint 独立管理路由，URL 前缀 `/admin/`。

### 4.6 权限控制 — `routes/auth.py`

两个装饰器：

- `@login_required`：检查 session 中是否有 username
- `@admin_required`：在登录基础上，额外检查用户角色是否为 admin

---

## 5. 管理页面

管理页面（`/admin/`）采用 6 个 Tab 页签组织功能：

| Tab | 功能 | 说明 |
|-----|------|------|
| 邮件任务 | 任务 CRUD + 手动触发 | 配置查询楼栋、收件人、Cron 表达式等 |
| 用户管理 | 用户 CRUD | 创建/编辑/删除/启用禁用用户 |
| 权限管理 | 分配权限 | 为每个用户勾选 query/download/admin/trigger_task |
| 执行记录 | 查看日志 | 任务执行历史，包含状态、文件路径、错误信息 |
| 系统配置 | 在线编辑 | 修改 SMTP、Chrome 路径、调度器等所有配置 |
| 调度器 | 状态管理 | 查看调度器运行状态、任务列表、重新加载 |

---

## 6. API 接口

所有管理 API 均需 admin 权限，前缀 `/admin/api/`。

### 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/api/users` | 获取所有用户（不含密码） |
| POST | `/admin/api/users` | 创建用户 |
| PUT | `/admin/api/users/<username>` | 更新用户 |
| DELETE | `/admin/api/users/<username>` | 删除用户 |

### 权限管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/api/permissions` | 获取所有权限 |
| GET | `/admin/api/permissions/<username>` | 获取用户权限 |
| PUT | `/admin/api/permissions/<username>` | 设置用户权限 |

### 邮件任务

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/api/email-tasks` | 获取所有任务 |
| POST | `/admin/api/email-tasks` | 创建任务 |
| PUT | `/admin/api/email-tasks/<id>` | 更新任务 |
| DELETE | `/admin/api/email-tasks/<id>` | 删除任务 |
| POST | `/admin/api/trigger-task/<id>` | 手动触发执行 |

### 任务日志

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/api/task-logs?limit=50` | 获取执行记录 |

### 系统配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/api/config` | 获取所有配置 |
| PUT | `/admin/api/config` | 批量更新配置 |

### 调度器

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/api/scheduler/status` | 获取调度器状态和任务列表 |
| POST | `/admin/api/scheduler/reload` | 重新加载调度器 |

---

## 7. 任务执行流程

```
定时触发 / 手动触发
       │
       ▼
  TaskManager.execute_single_task()
       │
       ├─ 1. 创建 task_log（status=running）
       │
       ├─ 2. 构造请求参数（buildings, startTime, endTime）
       │
       ├─ 3. 调用 process() → Selenium 抓取数据 → 生成 Excel
       │
       ├─ 4. process() 返回成功？
       │      │
       │      ├─ 否 → 更新 task_log（status=failed）→ 结束
       │      │
       │      └─ 是 → 继续
       │
       ├─ 5. EmailSender.send_email()（附件=Excel 文件）
       │      │
       │      ├─ 失败 → 更新 task_log（status=email_failed）
       │      │
       │      └─ 成功 → 更新 task_log（status=success）
       │
       └─ 结束
```

---

## 8. 配置管理方案

### 改造前

| 配置项 | 存储位置 | 问题 |
|--------|----------|------|
| Flask 密钥 | `.env` | — |
| 用户密码 | `.env` | 硬编码用户名 |
| 外部系统凭据 | `.env` | 分散管理 |
| Chrome 路径 | `.env` | 分散管理 |
| 楼栋映射 bid_dict | `config.json` | 被 gitignore |
| 学院映射 data_cfg | `config.json` | 被 gitignore |

### 改造后

| 配置项 | 存储位置 | 管理方式 |
|--------|----------|----------|
| `FLASK_SECRET_KEY` | `.env` | 手动配置（仅此一项） |
| 其他所有配置 | SQLite `system_config` 表 | 管理页面在线修改 |
| 用户和密码 | SQLite `users` 表 | 管理页面在线修改 |

**优势：**
- 本地只需维护 `database/init_data.sql` 一个文件
- 部署时执行 SQL 或直接上传 `edu.db` 即可
- 配置变更通过管理页面完成，无需登录服务器

---

## 9. 文件提交策略

| 文件 | Git 状态 | 说明 |
|------|----------|------|
| `database/schema.sql` | ✅ 提交 | 表结构，所有环境一致 |
| `database/db.py` | ✅ 提交 | 数据库操作代码 |
| `scheduler/*.py` | ✅ 提交 | 调度器、任务管理、邮件发送 |
| `routes/*.py` | ✅ 提交 | 管理页面路由和权限装饰器 |
| `templates/admin.html` | ✅ 提交 | 管理页面前端 |
| `database/init_data.sql` | ❌ 不提交 | 含密码等敏感数据 |
| `data/edu.db` | ❌ 不提交 | 数据库文件 |
| `.env` | ❌ 不提交 | 仅含 FLASK_SECRET_KEY |
