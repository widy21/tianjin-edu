import os
from log_config import setup_logging
import logging

from flask import Flask, render_template, redirect, url_for, request, session, flash, send_file
from werkzeug.utils import safe_join
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置基础目录
DOWNLOAD_FOLDER = os.path.abspath('result-files')

from get_excel_data_curr.main import process
from database.db import Database
from scheduler.scheduler import SchedulerManager
from routes.admin import admin_bp
from routes.auth import login_required

app = Flask(__name__)

# 从环境变量获取 Secret Key
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# 配置日志
setup_logging()

# 初始化数据库
db = Database()

# 注册管理页面 Blueprint
app.register_blueprint(admin_bp)


# 登录页面路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    logging.debug("Entering login function")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        logging.debug(f"Received POST request with username: {username}")

        user = db.verify_user(username, password)
        if not user:
            logging.debug(f"Login failed for username: {username}")
            db.create_operation_log(username, 'login_failed', '用户名或密码错误', request.remote_addr)
            flash('用户名或密码错误。')
            return redirect(url_for('login'))

        # 登录成功
        session['username'] = username
        session['role'] = user['role']
        logging.debug(f"User {username} logged in successfully")
        db.create_operation_log(username, 'login', '登录成功', request.remote_addr)
        return redirect(url_for('dashboard'))

    logging.debug("Rendering login.html")
    return render_template('login.html')


# 登录后的页面路由
@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    user = db.get_user(username)
    is_admin = user and user['role'] == 'admin'
    has_admin_perm = db.has_permission(username, 'admin')  # 是否有"管理页面"权限
    allowed_buildings = db.get_user_buildings(username)  # 空列表表示全部
    logging.debug(f"Rendering dashboard.html for user {username}")
    return render_template('dashboard.html', username=username, is_admin=is_admin, has_admin_perm=has_admin_perm, allowed_buildings=allowed_buildings)


# 退出登录路由
@app.route('/logout')
def logout():
    logging.debug("Entering logout function")
    username = session.get('username')
    if username:
        db.create_operation_log(username, 'logout', '退出登录', request.remote_addr)
    # 从会话中移除用户信息
    session.pop('username', None)
    session.pop('role', None)
    logging.debug("User logged out")
    flash('已退出登录。')
    return redirect(url_for('login'))


@app.route('/')
def home():
    logging.debug("Entering home function")
    return 'Hello, Flask!'


@app.route('/query', methods=['POST'])
def query():
    logging.debug("Entering query function")
    if request.method == 'POST':
        data = request.json
        logging.debug(f"Received POST request with data: {data}")
        username = session.get('username', '')
        # 校验楼栋权限
        allowed = db.get_user_buildings(username)
        if allowed:
            requested = data.get('buildings', [])
            data['buildings'] = [b for b in requested if b in allowed]
            if not data['buildings']:
                return {'status': 'error', 'message': '没有可操作的楼栋权限'}
        buildings = ','.join(data.get('buildings', []))
        db.create_operation_log(username, 'query', f'查询楼栋: {buildings}', request.remote_addr)
        # 加工数据
        result = process(data)
        logging.debug(f"Processed result: {result}")
        return result


@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        # 拼接安全路径
        # 移除可能重复的目录名
        clean_filename = filename.replace('result-files/', '').lstrip('/')
        safe_path = safe_join(DOWNLOAD_FOLDER, clean_filename)

        if not os.path.exists(safe_path):
            logging.debug(f"File {safe_path} not found")
            return "File not found", 404

        username = session.get('username', '')
        db.create_operation_log(username, 'download', f'下载文件: {clean_filename}', request.remote_addr)
        logging.debug(f"Sending file: {safe_path}")
        return send_file(safe_path, as_attachment=True)

    except Exception as e:
        logging.error(f"File access error: {str(e)}")
        return "Invalid request", 400


def init_scheduler():
    """初始化并启动定时调度器"""
    sm = SchedulerManager(db)
    app.config['SCHEDULER_MANAGER'] = sm
    sm.start()
    return sm


if __name__ == '__main__':
    init_scheduler()
    app.run(host='0.0.0.0', port=80)
