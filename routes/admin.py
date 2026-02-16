import logging
from flask import Blueprint, render_template, request, session, jsonify
from database.db import Database
from routes.auth import admin_required
from scheduler.task_manager import TaskManager

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
db = Database()


# ==================== 管理页面 ====================

@admin_bp.route('/')
@admin_required
def admin_page():
    return render_template('admin.html', username=session['username'])


# ==================== 用户管理 API ====================

@admin_bp.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    users = db.get_all_users()
    # 不返回密码
    for u in users:
        u.pop('password', None)
    return jsonify(users)


@admin_bp.route('/api/users', methods=['POST'])
@admin_required
def create_user():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'user')
    if not username or not password:
        return jsonify({'success': False, 'msg': '用户名和密码不能为空'}), 400
    ok = db.create_user(username, password, role)
    if not ok:
        return jsonify({'success': False, 'msg': '用户名已存在'}), 400
    return jsonify({'success': True})


@admin_bp.route('/api/users/<username>', methods=['PUT'])
@admin_required
def update_user(username):
    data = request.json
    kwargs = {}
    if 'password' in data and data['password'].strip():
        kwargs['password'] = data['password'].strip()
    if 'role' in data:
        kwargs['role'] = data['role']
    if 'enabled' in data:
        kwargs['enabled'] = 1 if data['enabled'] else 0
    db.update_user(username, **kwargs)
    return jsonify({'success': True})


@admin_bp.route('/api/users/<username>', methods=['DELETE'])
@admin_required
def delete_user(username):
    if username == session.get('username'):
        return jsonify({'success': False, 'msg': '不能删除当前登录用户'}), 400
    db.delete_user(username)
    return jsonify({'success': True})


# ==================== 权限管理 API ====================

@admin_bp.route('/api/permissions', methods=['GET'])
@admin_required
def get_permissions():
    return jsonify(db.get_all_permissions())


@admin_bp.route('/api/permissions/<username>', methods=['GET'])
@admin_required
def get_user_perms(username):
    return jsonify(db.get_user_permissions(username))


@admin_bp.route('/api/permissions/<username>', methods=['PUT'])
@admin_required
def set_user_perms(username):
    data = request.json
    permissions = data.get('permissions', [])
    db.set_user_permissions(username, permissions)
    return jsonify({'success': True})


# ==================== 邮件任务配置 API ====================

@admin_bp.route('/api/email-tasks', methods=['GET'])
@admin_required
def get_email_tasks():
    return jsonify(db.get_all_email_tasks())


@admin_bp.route('/api/email-tasks', methods=['POST'])
@admin_required
def create_email_task():
    data = request.json
    task_id = db.create_email_task(
        task_name=data.get('task_name', ''),
        username=data.get('username', ''),
        buildings=data.get('buildings', []),
        recipients=data.get('recipients', []),
        subject_prefix=data.get('subject_prefix', ''),
        start_time=data.get('start_time', '23:20:00'),
        end_time=data.get('end_time', '05:30:00'),
        cron_expression=data.get('cron_expression', '0 6 * * *'),
        enabled=1 if data.get('enabled', True) else 0,
    )
    return jsonify({'success': True, 'id': task_id})


@admin_bp.route('/api/email-tasks/<int:task_id>', methods=['PUT'])
@admin_required
def update_email_task(task_id):
    data = request.json
    kwargs = {}
    for key in ('task_name', 'username', 'buildings', 'recipients', 'subject_prefix',
                'start_time', 'end_time', 'cron_expression'):
        if key in data:
            kwargs[key] = data[key]
    if 'enabled' in data:
        kwargs['enabled'] = 1 if data['enabled'] else 0
    db.update_email_task(task_id, **kwargs)
    return jsonify({'success': True})


@admin_bp.route('/api/email-tasks/<int:task_id>', methods=['DELETE'])
@admin_required
def delete_email_task(task_id):
    db.delete_email_task(task_id)
    return jsonify({'success': True})


# ==================== 手动触发任务 ====================

@admin_bp.route('/api/trigger-task/<int:task_id>', methods=['POST'])
@admin_required
def trigger_task(task_id):
    task = db.get_email_task(task_id)
    if not task:
        return jsonify({'success': False, 'msg': '任务不存在'}), 404
    try:
        tm = TaskManager(db)
        tm.execute_single_task(task)
        return jsonify({'success': True, 'msg': '任务已触发执行'})
    except Exception as e:
        logging.error(f"手动触发任务失败: {str(e)}")
        return jsonify({'success': False, 'msg': str(e)}), 500


# ==================== 任务执行记录 API ====================

@admin_bp.route('/api/task-logs', methods=['GET'])
@admin_required
def get_task_logs():
    limit = request.args.get('limit', 50, type=int)
    username = request.args.get('username', None)
    logs = db.get_task_logs(limit=limit, username=username)
    return jsonify(logs)


# ==================== 系统配置 API ====================

@admin_bp.route('/api/config', methods=['GET'])
@admin_required
def get_config():
    return jsonify(db.get_all_config())


@admin_bp.route('/api/config', methods=['PUT'])
@admin_required
def update_config():
    data = request.json
    for item in data:
        db.set_config(item['config_key'], item['config_value'], item.get('description'))
    return jsonify({'success': True})


# ==================== 调度器管理 API ====================

@admin_bp.route('/api/scheduler/status', methods=['GET'])
@admin_required
def scheduler_status():
    from flask import current_app
    sm = current_app.config.get('SCHEDULER_MANAGER')
    if not sm:
        return jsonify({'running': False, 'jobs': []})
    return jsonify({
        'running': bool(sm.scheduler and sm.scheduler.running),
        'jobs': sm.get_jobs()
    })


@admin_bp.route('/api/scheduler/reload', methods=['POST'])
@admin_required
def scheduler_reload():
    from flask import current_app
    sm = current_app.config.get('SCHEDULER_MANAGER')
    if sm:
        sm.reload()
        return jsonify({'success': True, 'msg': '调度器已重新加载'})
    return jsonify({'success': False, 'msg': '调度器未初始化'}), 500

