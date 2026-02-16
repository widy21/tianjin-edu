#!/usr/bin/env python3
"""
自动邮件定时任务 & 管理页面 — 自测脚本
使用临时数据库，不影响正式数据。
"""
import os
import sys
import tempfile
import shutil
import json

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

PASS = 0
FAIL = 0
RESULTS = []


def record(test_name, passed, detail=''):
    global PASS, FAIL
    if passed:
        PASS += 1
        RESULTS.append((test_name, '✅ PASS', detail))
    else:
        FAIL += 1
        RESULTS.append((test_name, '❌ FAIL', detail))


# ============================================================
# 1. 数据库层测试
# ============================================================
def test_database():
    from database.db import Database

    # 使用临时目录
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, 'test.db')

    try:
        # 1.1 初始化
        db = Database(db_path=db_path)
        record('1.1 数据库初始化', os.path.exists(db_path))

        # 1.2 用户 CRUD
        ok = db.create_user('testuser', 'pass123', 'user')
        record('1.2a create_user 成功', ok is True)

        ok2 = db.create_user('testuser', 'pass456', 'user')
        record('1.2b create_user 重复用户名返回 False', ok2 is False)

        user = db.get_user('testuser')
        record('1.2c get_user 存在的用户', user is not None and user['username'] == 'testuser')

        user_none = db.get_user('nonexist')
        record('1.2d get_user 不存在的用户返回 None', user_none is None)

        verified = db.verify_user('testuser', 'pass123')
        record('1.2e verify_user 正确密码', verified is not None and verified['username'] == 'testuser')

        not_verified = db.verify_user('testuser', 'wrongpass')
        record('1.2f verify_user 错误密码返回 None', not_verified is None)

        # 禁用用户后验证
        db.update_user('testuser', enabled=0)
        disabled = db.verify_user('testuser', 'pass123')
        record('1.2g verify_user 禁用用户返回 None', disabled is None)

        # 恢复启用
        db.update_user('testuser', enabled=1, password='newpass', role='admin')
        updated = db.get_user('testuser')
        record('1.2h update_user 修改密码/角色/启用',
               updated['password'] == 'newpass' and updated['role'] == 'admin' and updated['enabled'] == 1)

        # 创建第二个用户用于删除测试
        db.create_user('deluser', 'pass', 'user')
        db.set_user_permissions('deluser', ['query', 'download'])
        db.delete_user('deluser')
        del_user = db.get_user('deluser')
        del_perms = db.get_user_permissions('deluser')
        record('1.2i delete_user 删除用户同时删除权限', del_user is None and len(del_perms) == 0)

        all_users = db.get_all_users()
        record('1.2j get_all_users', isinstance(all_users, list) and len(all_users) >= 1)

        # 1.3 系统配置 CRUD
        db.set_config('test_key', 'test_value', '测试配置')
        val = db.get_config('test_key')
        record('1.3a set_config + get_config 新增', val == 'test_value')

        db.set_config('test_key', 'updated_value')
        val2 = db.get_config('test_key')
        record('1.3b set_config 更新已有配置', val2 == 'updated_value')

        default_val = db.get_config('nonexist_key', 'default')
        record('1.3c get_config 不存在的配置返回默认值', default_val == 'default')

        all_cfg = db.get_all_config()
        record('1.3d get_all_config', isinstance(all_cfg, list) and len(all_cfg) >= 1)

        cfg_dict = db.get_config_dict()
        record('1.3e get_config_dict', isinstance(cfg_dict, dict) and cfg_dict.get('test_key') == 'updated_value')

        # 1.4 邮件任务 CRUD
        task_id = db.create_email_task(
            task_name='测试任务',
            username='testuser',
            buildings=['4', '5'],
            recipients=['a@test.com', 'b@test.com'],
            subject_prefix='[测试]',
            cron_expression='0 7 * * *'
        )
        record('1.4a create_email_task 返回 task_id', isinstance(task_id, int) and task_id > 0)

        task = db.get_email_task(task_id)
        record('1.4b get_email_task 反序列化',
               task is not None and isinstance(task['buildings'], list) and task['buildings'] == ['4', '5']
               and isinstance(task['recipients'], list))

        all_tasks = db.get_all_email_tasks()
        record('1.4c get_all_email_tasks', isinstance(all_tasks, list) and len(all_tasks) >= 1)

        enabled_tasks = db.get_enabled_email_tasks()
        record('1.4d get_enabled_email_tasks', isinstance(enabled_tasks, list) and len(enabled_tasks) >= 1)

        db.update_email_task(task_id, task_name='更新后的任务', enabled=0)
        updated_task = db.get_email_task(task_id)
        record('1.4e update_email_task', updated_task['task_name'] == '更新后的任务' and updated_task['enabled'] == 0)

        # 禁用后不在 enabled 列表中
        enabled_after = db.get_enabled_email_tasks()
        ids_enabled = [t['id'] for t in enabled_after]
        record('1.4f 禁用后不在 enabled 列表', task_id not in ids_enabled)

        db.delete_email_task(task_id)
        deleted_task = db.get_email_task(task_id)
        record('1.4g delete_email_task', deleted_task is None)

        # 1.5 任务日志
        # 先创建一个任务用于关联
        t_id = db.create_email_task('日志测试任务', 'testuser', ['4'], ['x@t.com'])
        log_id = db.create_task_log(t_id, 'testuser', 'running')
        record('1.5a create_task_log', isinstance(log_id, int) and log_id > 0)

        db.update_task_log(log_id, 'success', file_path='/tmp/test.xlsx')
        logs = db.get_task_logs(limit=10)
        record('1.5b update_task_log + get_task_logs',
               len(logs) >= 1 and logs[0]['status'] == 'success' and logs[0]['task_name'] == '日志测试任务')

        # 按用户过滤
        logs_user = db.get_task_logs(limit=10, username='testuser')
        logs_other = db.get_task_logs(limit=10, username='nobody')
        record('1.5c get_task_logs 按用户过滤', len(logs_user) >= 1 and len(logs_other) == 0)

        # 1.6 权限管理
        db.set_user_permissions('testuser', ['query', 'download', 'admin'])
        perms = db.get_user_permissions('testuser')
        record('1.6a set_user_permissions + get_user_permissions',
               set(perms) == {'query', 'download', 'admin'})

        has = db.has_permission('testuser', 'admin')
        has_not = db.has_permission('testuser', 'trigger_task')
        record('1.6b has_permission', has is True and has_not is False)

        all_perms = db.get_all_permissions()
        record('1.6c get_all_permissions', isinstance(all_perms, list) and len(all_perms) >= 3)

        # 重置权限
        db.set_user_permissions('testuser', ['query'])
        perms2 = db.get_user_permissions('testuser')
        record('1.6d 重置权限后只剩 query', perms2 == ['query'])

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ============================================================
# 2. 模块导入测试
# ============================================================
def test_imports():
    try:
        from database.db import Database
        record('2.1 import Database', True)
    except Exception as e:
        record('2.1 import Database', False, str(e))

    try:
        from scheduler.email_sender import EmailSender
        record('2.2 import EmailSender', True)
    except Exception as e:
        record('2.2 import EmailSender', False, str(e))

    try:
        from scheduler.task_manager import TaskManager
        record('2.3 import TaskManager', True)
    except Exception as e:
        record('2.3 import TaskManager', False, str(e))

    try:
        from scheduler.scheduler import SchedulerManager
        record('2.4 import SchedulerManager', True)
    except Exception as e:
        record('2.4 import SchedulerManager', False, str(e))

    try:
        from routes.auth import login_required, admin_required
        record('2.5 import login_required, admin_required', True)
    except Exception as e:
        record('2.5 import login_required, admin_required', False, str(e))

    try:
        from routes.admin import admin_bp
        record('2.6 import admin_bp', True)
    except Exception as e:
        record('2.6 import admin_bp', False, str(e))


# ============================================================
# 3. Flask 应用测试 + 4. 管理 API 测试
# ============================================================
def test_flask_app():
    """使用临时数据库创建 Flask 测试客户端"""
    from flask import Flask
    from database.db import Database
    from routes.admin import admin_bp as _admin_bp
    from routes.auth import login_required as _lr

    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, 'test.db')

    try:
        db = Database(db_path=db_path)
        # 创建测试用户
        db.create_user('admin', 'admin123', 'admin')
        db.create_user('user1', 'user123', 'user')
        db.set_user_permissions('admin', ['query', 'download', 'admin', 'trigger_task'])
        db.set_user_permissions('user1', ['query', 'download'])
        # 创建一些配置
        db.set_config('smtp_server', 'smtp.test.com')
        db.set_config('smtp_port', '587')
        db.set_config('sender_email', 'test@test.com')
        db.set_config('sender_password', 'testpass')
        db.set_config('smtp_use_tls', 'true')
        db.set_config('scheduler_enabled', 'false')

        # 创建一个新的 Flask app 用于测试（避免影响全局 app）
        test_app = Flask(__name__, template_folder=os.path.join(PROJECT_ROOT, 'templates'))
        test_app.secret_key = 'test-secret-key'
        test_app.config['TESTING'] = True

        # 需要重新创建 Blueprint 以避免重复注册问题
        # 直接 monkey-patch admin.py 中的 db
        import routes.admin as admin_module
        original_db = admin_module.db
        admin_module.db = db

        import routes.auth as auth_module
        original_auth_db = auth_module.db
        auth_module.db = db

        # 注册 Blueprint（需要用新的名字避免冲突）
        from flask import Blueprint
        # 直接使用已有的 blueprint
        test_app.register_blueprint(_admin_bp)

        # 添加必要的路由
        @test_app.route('/login', methods=['GET', 'POST'])
        def login():
            from flask import request, session, flash, redirect, url_for, render_template
            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']
                user = db.verify_user(username, password)
                if not user:
                    flash('用户名或密码错误。')
                    return redirect(url_for('login'))
                session['username'] = username
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            return render_template('login.html')

        @test_app.route('/dashboard')
        @_lr
        def dashboard():
            from flask import session, render_template
            username = session['username']
            user = db.get_user(username)
            is_admin = user and user['role'] == 'admin'
            return render_template('dashboard.html', username=username, is_admin=is_admin)

        @test_app.route('/logout')
        def logout():
            from flask import session, redirect, url_for
            session.pop('username', None)
            session.pop('role', None)
            return redirect(url_for('login'))

        client = test_app.test_client()

        # 3.1 应用启动
        record('3.1a Flask app 实例创建成功', test_app is not None)
        record('3.1b Blueprint 注册成功', 'admin' in test_app.blueprints)

        # 3.2 登录认证
        # 正确密码登录
        resp = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=False)
        record('3.2a POST /login 正确密码 → 重定向', resp.status_code in (302, 303))

        # 错误密码登录
        resp = client.post('/login', data={'username': 'admin', 'password': 'wrong'}, follow_redirects=False)
        record('3.2b POST /login 错误密码 → 重定向回 login', resp.status_code in (302, 303))

        # 未登录访问 dashboard
        client2 = test_app.test_client()  # 新客户端，无 session
        resp = client2.get('/dashboard', follow_redirects=False)
        record('3.2c GET /dashboard 未登录 → 重定向', resp.status_code in (302, 303))

        # 3.3 管理页面访问控制
        # 未登录访问 admin
        client3 = test_app.test_client()
        resp = client3.get('/admin/', follow_redirects=False)
        record('3.3a GET /admin/ 未登录 → 重定向到 login', resp.status_code in (302, 303))

        # 普通用户访问 admin
        client4 = test_app.test_client()
        client4.post('/login', data={'username': 'user1', 'password': 'user123'})
        resp = client4.get('/admin/', follow_redirects=False)
        record('3.3b GET /admin/ 普通用户 → 重定向到 dashboard', resp.status_code in (302, 303))

        # 管理员访问 admin
        admin_client = test_app.test_client()
        admin_client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        resp = admin_client.get('/admin/')
        record('3.3c GET /admin/ 管理员 → 200', resp.status_code == 200)

        # ==================== 4. 管理 API 测试 ====================
        # 使用 admin_client（已登录管理员）

        # 4.1 用户管理 API
        resp = admin_client.get('/admin/api/users')
        users_data = resp.get_json()
        record('4.1a GET /admin/api/users 返回用户列表',
               resp.status_code == 200 and isinstance(users_data, list))
        # 检查不含密码
        has_password = any('password' in u for u in users_data)
        record('4.1b 用户列表不含密码字段', not has_password)

        resp = admin_client.post('/admin/api/users',
                                  json={'username': 'newuser', 'password': 'newpass', 'role': 'user'})
        record('4.1c POST /admin/api/users 创建用户', resp.status_code == 200 and resp.get_json()['success'])

        resp = admin_client.put('/admin/api/users/newuser', json={'role': 'admin', 'enabled': False})
        record('4.1d PUT /admin/api/users/<username> 更新用户', resp.status_code == 200)

        resp = admin_client.delete('/admin/api/users/newuser')
        record('4.1e DELETE /admin/api/users/<username> 删除用户', resp.status_code == 200)

        # 不能删除当前登录用户
        resp = admin_client.delete('/admin/api/users/admin')
        record('4.1f DELETE 当前登录用户 → 400', resp.status_code == 400)

        # 4.2 权限管理 API
        resp = admin_client.get('/admin/api/permissions')
        record('4.2a GET /admin/api/permissions', resp.status_code == 200)

        resp = admin_client.put('/admin/api/permissions/user1',
                                 json={'permissions': ['query', 'download', 'trigger_task']})
        record('4.2b PUT /admin/api/permissions/<username>', resp.status_code == 200)

        resp = admin_client.get('/admin/api/permissions/user1')
        perms = resp.get_json()
        record('4.2c GET /admin/api/permissions/<username> 验证更新',
               'trigger_task' in perms)

        # 4.3 邮件任务 API
        resp = admin_client.post('/admin/api/email-tasks', json={
            'task_name': 'API测试任务',
            'username': 'admin',
            'buildings': ['4', '5'],
            'recipients': ['test@test.com'],
            'cron_expression': '0 7 * * *',
            'enabled': True
        })
        resp_data = resp.get_json()
        record('4.3a POST /admin/api/email-tasks 创建任务', resp.status_code == 200 and resp_data['success'])
        api_task_id = resp_data.get('id')

        resp = admin_client.get('/admin/api/email-tasks')
        tasks_data = resp.get_json()
        record('4.3b GET /admin/api/email-tasks 返回任务列表',
               resp.status_code == 200 and isinstance(tasks_data, list) and len(tasks_data) >= 1)

        if api_task_id:
            resp = admin_client.put(f'/admin/api/email-tasks/{api_task_id}',
                                     json={'task_name': '更新后的API任务', 'enabled': False})
            record('4.3c PUT /admin/api/email-tasks/<id> 更新任务', resp.status_code == 200)

            resp = admin_client.delete(f'/admin/api/email-tasks/{api_task_id}')
            record('4.3d DELETE /admin/api/email-tasks/<id> 删除任务', resp.status_code == 200)

        # 4.4 系统配置 API
        resp = admin_client.get('/admin/api/config')
        record('4.4a GET /admin/api/config', resp.status_code == 200 and isinstance(resp.get_json(), list))

        resp = admin_client.put('/admin/api/config', json=[
            {'config_key': 'test_api_key', 'config_value': 'test_api_value', 'description': 'API测试'}
        ])
        record('4.4b PUT /admin/api/config 批量更新', resp.status_code == 200)

        # 4.5 调度器 API
        resp = admin_client.get('/admin/api/scheduler/status')
        record('4.5a GET /admin/api/scheduler/status', resp.status_code == 200)

        resp = admin_client.post('/admin/api/scheduler/reload')
        # 调度器未初始化时返回 500
        record('4.5b POST /admin/api/scheduler/reload (无调度器)', resp.status_code == 500)

        # 4.6 任务日志 API
        resp = admin_client.get('/admin/api/task-logs')
        record('4.6 GET /admin/api/task-logs', resp.status_code == 200 and isinstance(resp.get_json(), list))

    finally:
        # 恢复原始 db
        admin_module.db = original_db
        auth_module.db = original_auth_db
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ============================================================
# 5. EmailSender 测试
# ============================================================
def test_email_sender():
    from database.db import Database
    from scheduler.email_sender import EmailSender

    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, 'test.db')

    try:
        db = Database(db_path=db_path)
        db.set_config('smtp_server', 'smtp.qq.com')
        db.set_config('smtp_port', '587')
        db.set_config('sender_email', 'sender@qq.com')
        db.set_config('sender_password', 'authcode123')
        db.set_config('smtp_use_tls', 'true')

        sender = EmailSender.from_db(db)
        record('5.1 EmailSender.from_db 实例化成功', sender is not None)
        record('5.2 smtp_server 正确', sender.smtp_server == 'smtp.qq.com')
        record('5.3 smtp_port 正确', sender.smtp_port == 587)
        record('5.4 sender_email 正确', sender.sender_email == 'sender@qq.com')
        record('5.5 use_tls 正确', sender.use_tls is True)

        # 测试 use_tls=false
        db.set_config('smtp_use_tls', 'false')
        sender2 = EmailSender.from_db(db)
        record('5.6 use_tls=false 正确', sender2.use_tls is False)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ============================================================
# 6. SchedulerManager 测试
# ============================================================
def test_scheduler():
    from database.db import Database
    from scheduler.scheduler import SchedulerManager

    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, 'test.db')

    try:
        db = Database(db_path=db_path)
        db.set_config('scheduler_enabled', 'false')

        sm = SchedulerManager(db)
        record('6.1 SchedulerManager 实例化成功', sm is not None)

        sm.start()
        record('6.2 scheduler_enabled=false 时不启动', sm.scheduler is None)

        jobs = sm.get_jobs()
        record('6.3 get_jobs 无调度器时返回空列表', jobs == [])

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ============================================================
# 主执行
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("自动邮件定时任务 & 管理页面 — 自测执行")
    print("=" * 60)
    print()

    sections = [
        ('1. 数据库层测试', test_database),
        ('2. 模块导入测试', test_imports),
        ('3+4. Flask 应用 & 管理 API 测试', test_flask_app),
        ('5. EmailSender 测试', test_email_sender),
        ('6. SchedulerManager 测试', test_scheduler),
    ]

    for name, func in sections:
        print(f"--- {name} ---")
        try:
            func()
        except Exception as e:
            record(f'{name} 执行异常', False, str(e))
            import traceback
            traceback.print_exc()
        print()

    # 打印结果汇总
    print("=" * 60)
    print(f"测试结果汇总: {PASS} 通过, {FAIL} 失败, 共 {PASS + FAIL} 项")
    print("=" * 60)
    print()

    for test_name, status, detail in RESULTS:
        line = f"  {status} {test_name}"
        if detail:
            line += f"  ({detail})"
        print(line)

    print()
    if FAIL == 0:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️  有 {FAIL} 项测试失败，请检查。")

    sys.exit(0 if FAIL == 0 else 1)

