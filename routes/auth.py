from functools import wraps
from flask import session, flash, redirect, url_for
from database.db import Database

db = Database()


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录。')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录。')
            return redirect(url_for('login'))
        user = db.get_user(session['username'])
        if not user or user['role'] != 'admin':
            flash('您没有管理员权限。')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

