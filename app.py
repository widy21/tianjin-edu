import os
from log_config import setup_logging
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, redirect, url_for, request, session, flash, send_file
from werkzeug.utils import safe_join
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置基础目录
DOWNLOAD_FOLDER = os.path.abspath('result-files')

from get_excel_data_curr.main import process

app = Flask(__name__)

# 从环境变量获取 Secret Key
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# 配置日志
setup_logging()  # 多次调用不会重复配置

# 从环境变量获取用户凭据
users = {
    'admin': os.environ.get('USER_ADMIN_PASSWORD', 'admin123'),
    'lily': os.environ.get('USER_LILY_PASSWORD', 'lily2025'),
    'edu': os.environ.get('USER_EDU_PASSWORD', 'edu2025'),
}


# 登录页面路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    logging.debug("Entering login function")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # 安全修复：不再记录密码
        logging.debug(f"Received POST request with username: {username}")

        # 检查用户名是否存在
        if username not in users:
            logging.debug(f"Username {username} does not exist")
            flash('用户名不存在，请先注册。')
            return redirect(url_for('login'))

        # 验证密码是否正确
        if not (username in users and users[username] == password):
            logging.debug(f"Password for username {username} is incorrect")
            flash('密码错误，请重新输入。')
            return redirect(url_for('login'))

        # 登录成功，将用户信息存储到会话中
        session['username'] = username
        logging.debug(f"User {username} logged in successfully")
        flash('登录成功！')
        return redirect(url_for('dashboard'))

    logging.debug("Rendering login.html")
    return render_template('login.html')


# 登录后的页面路由
@app.route('/dashboard')
def dashboard():
    logging.debug("Entering dashboard function")
    # 检查用户是否已登录
    if 'username' not in session:
        logging.debug("User not logged in, redirecting to login")
        flash('请先登录。')
        return redirect(url_for('login'))

    logging.debug(f"Rendering dashboard.html for user {session['username']}")
    return render_template('dashboard.html', username=session['username'])


# 退出登录路由
@app.route('/logout')
def logout():
    logging.debug("Entering logout function")
    # 从会话中移除用户信息
    session.pop('username', None)
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

        logging.debug(f"Sending file: {safe_path}")
        return send_file(safe_path, as_attachment=True)

    except Exception as e:
        logging.error(f"File access error: {str(e)}")
        return "Invalid request", 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
