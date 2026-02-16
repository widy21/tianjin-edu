import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, redirect, url_for, request, session, flash, send_file

from get_excel_data_curr.main import process

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于会话加密

# 配置日志
log_file = 'edu.log'
log_max_size = 100 * 1024 * 1024  # 100MB
log_backup_count = 5  # 保留5个备份文件

logging.basicConfig(level=logging.DEBUG)
handler = RotatingFileHandler(log_file, maxBytes=log_max_size, backupCount=log_backup_count)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# 模拟数据库中的用户数据
users = {
    'admin': 'admin123',
    'lily': 'lily2025',
}


# 登录页面路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    app.logger.debug("Entering login function")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        app.logger.debug(f"Received POST request with username: {username} and password: {password}")

        # 检查用户名是否存在
        if username not in users:
            app.logger.debug(f"Username {username} does not exist")
            flash('用户名不存在，请先注册。')
            return redirect(url_for('login'))

        # 验证密码是否正确
        if not (username in users and users[username] == password):
            app.logger.debug(f"Password for username {username} is incorrect")
            flash('密码错误，请重新输入。')
            return redirect(url_for('login'))

        # 登录成功，将用户信息存储到会话中
        session['username'] = username
        app.logger.debug(f"User {username} logged in successfully")
        flash('登录成功！')
        return redirect(url_for('dashboard'))

    app.logger.debug("Rendering login.html")
    return render_template('login.html')


# 登录后的页面路由
@app.route('/dashboard')
def dashboard():
    app.logger.debug("Entering dashboard function")
    # 检查用户是否已登录
    if 'username' not in session:
        app.logger.debug("User not logged in, redirecting to login")
        flash('请先登录。')
        return redirect(url_for('login'))

    app.logger.debug(f"Rendering dashboard.html for user {session['username']}")
    return render_template('dashboard.html', username=session['username'])


# 退出登录路由
@app.route('/logout')
def logout():
    app.logger.debug("Entering logout function")
    # 从会话中移除用户信息
    session.pop('username', None)
    app.logger.debug("User logged out")
    flash('已退出登录。')
    return redirect(url_for('login'))


@app.route('/')
def home():
    app.logger.debug("Entering home function")
    return 'Hello, Flask!'


@app.route('/query', methods=['POST'])
def query():
    app.logger.debug("Entering query function")
    if request.method == 'POST':
        data = request.json
        app.logger.debug(f"Received POST request with data: {data}")
        # 加工数据
        result = process(data)
        app.logger.debug(f"Processed result: {result}")
        return result


@app.route('/download/<filename>')
def download_file(filename):
    app.logger.debug(f"Entering download_file function with filename: {filename}")
    # 确保文件存在
    if os.path.exists(filename):
        app.logger.debug(f"File {filename} exists, sending file")
        return send_file(filename, as_attachment=True)
    else:
        app.logger.debug(f"File {filename} not found")
        return "File not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
