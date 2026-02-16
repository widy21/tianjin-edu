# 自动邮件定时任务 & 管理页面 — 自测方案

## 测试范围

本次自测覆盖 `feature/auto-email-task` 分支新增的所有模块，分为以下几个层次：

| 层次 | 测试内容 | 方式 |
|------|----------|------|
| 1. 数据库层 | Database 类所有 CRUD 方法 | Python 脚本自动化测试 |
| 2. 模块导入 | 所有新模块能正常导入 | Python import 验证 |
| 3. Flask 应用启动 | app.py 能正常启动，路由注册正确 | 启动验证 + curl 测试 |
| 4. 管理 API | 所有 /admin/api/ 接口 | Flask test_client 自动化测试 |
| 5. 邮件发送模块 | EmailSender 实例化和配置读取 | 单元测试（不实际发送） |
| 6. 调度器模块 | SchedulerManager 启动/停止/任务加载 | 单元测试 |
| 7. 前端页面 | 管理页面渲染、Tab 切换 | 手动验证（需浏览器） |

> **注意**：Selenium 数据抓取和实际邮件发送依赖外部系统，不在本次自测范围内。

---

## 测试用例

### 1. 数据库层测试

#### 1.1 数据库初始化
- [ ] `Database()` 实例化成功，自动创建 `data/` 目录和表结构
- [ ] 使用临时数据库路径不影响正式数据

#### 1.2 用户 CRUD
- [ ] `create_user()` 创建用户成功
- [ ] `create_user()` 重复用户名返回 False
- [ ] `get_user()` 获取存在的用户
- [ ] `get_user()` 获取不存在的用户返回 None
- [ ] `verify_user()` 正确密码返回用户信息
- [ ] `verify_user()` 错误密码返回 None
- [ ] `verify_user()` 禁用用户返回 None
- [ ] `update_user()` 修改密码/角色/启用状态
- [ ] `delete_user()` 删除用户同时删除权限

#### 1.3 系统配置 CRUD
- [ ] `set_config()` 新增配置
- [ ] `set_config()` 更新已有配置
- [ ] `get_config()` 获取存在的配置
- [ ] `get_config()` 获取不存在的配置返回默认值
- [ ] `get_all_config()` 返回所有配置列表
- [ ] `get_config_dict()` 返回字典格式

#### 1.4 邮件任务 CRUD
- [ ] `create_email_task()` 创建任务，返回 task_id
- [ ] `get_email_task()` 获取任务，buildings/recipients 自动反序列化为列表
- [ ] `get_all_email_tasks()` 返回所有任务
- [ ] `get_enabled_email_tasks()` 仅返回启用的任务
- [ ] `update_email_task()` 更新任务字段
- [ ] `delete_email_task()` 删除任务

#### 1.5 任务日志
- [ ] `create_task_log()` 创建日志记录
- [ ] `update_task_log()` 更新状态和错误信息
- [ ] `get_task_logs()` 获取日志列表（含 task_name 关联）
- [ ] `get_task_logs(username=)` 按用户过滤

#### 1.6 权限管理
- [ ] `set_user_permissions()` 设置权限列表
- [ ] `get_user_permissions()` 获取用户权限
- [ ] `has_permission()` 检查单个权限
- [ ] `get_all_permissions()` 获取所有权限记录

### 2. 模块导入测试
- [ ] `from database.db import Database`
- [ ] `from scheduler.email_sender import EmailSender`
- [ ] `from scheduler.task_manager import TaskManager`
- [ ] `from scheduler.scheduler import SchedulerManager`
- [ ] `from routes.auth import login_required, admin_required`
- [ ] `from routes.admin import admin_bp`

### 3. Flask 应用测试

#### 3.1 应用启动
- [ ] `app.py` 能正常导入，无语法错误
- [ ] Flask app 实例创建成功
- [ ] Blueprint 注册成功

#### 3.2 登录认证
- [ ] POST /login 正确密码 → 重定向到 dashboard
- [ ] POST /login 错误密码 → 重定向回 login
- [ ] GET /dashboard 未登录 → 重定向到 login
- [ ] GET /logout → 清除 session

#### 3.3 管理页面访问控制
- [ ] GET /admin/ 未登录 → 重定向到 login
- [ ] GET /admin/ 普通用户 → 重定向到 dashboard
- [ ] GET /admin/ 管理员 → 返回 200

### 4. 管理 API 测试

#### 4.1 用户管理 API
- [ ] GET /admin/api/users → 返回用户列表（不含密码）
- [ ] POST /admin/api/users → 创建用户
- [ ] PUT /admin/api/users/<username> → 更新用户
- [ ] DELETE /admin/api/users/<username> → 删除用户
- [ ] DELETE 当前登录用户 → 返回 400

#### 4.2 权限管理 API
- [ ] GET /admin/api/permissions → 返回所有权限
- [ ] PUT /admin/api/permissions/<username> → 设置权限

#### 4.3 邮件任务 API
- [ ] GET /admin/api/email-tasks → 返回任务列表
- [ ] POST /admin/api/email-tasks → 创建任务
- [ ] PUT /admin/api/email-tasks/<id> → 更新任务
- [ ] DELETE /admin/api/email-tasks/<id> → 删除任务

#### 4.4 系统配置 API
- [ ] GET /admin/api/config → 返回配置列表
- [ ] PUT /admin/api/config → 批量更新配置

#### 4.5 调度器 API
- [ ] GET /admin/api/scheduler/status → 返回状态
- [ ] POST /admin/api/scheduler/reload → 重新加载

### 5. EmailSender 测试
- [ ] `EmailSender.from_db(db)` 正确读取 SMTP 配置
- [ ] 实例属性（smtp_server, smtp_port, use_tls）正确

### 6. SchedulerManager 测试
- [ ] 实例化成功
- [ ] `scheduler_enabled=false` 时不启动
- [ ] `get_jobs()` 无调度器时返回空列表

---

## 测试执行记录

| 编号 | 测试项 | 结果 | 备注 |
|------|--------|------|------|
| | | | |

> 测试结果将在执行后填入上表。

