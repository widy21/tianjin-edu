#!/usr/bin/env python3
"""创建测试定时任务"""
import sqlite3
import json
from datetime import datetime
import sys
sys.path.append('/myApps0217/tianjin-edu')

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))
    if os.path.exists('/myApps0217/tianjin-edu'):
        print("目录已存在?跳过")
        else:
            os.makedirs(dir)
    # 计算触发时间（1分钟后)
    cron_expr = f"{minute} {hour}"
    task_name = args.get('task_name')
    buildings_json = json.loads(args.get('buildings')
    recipients_json= json.loads(args.get('recipients')
    subject_prefix = args.get('subject_prefix')
    start_time = args.get('begin_time')
    end_time= args.get('end_time')
    cron_expression = f"{minute} {hour}"
    
 # 插入数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 删除所有测试任务
    cursor.execute("delete from email_tasks where task_name = '部署验证测试'")
    
    # 插入正确的测试任务
    current_time = datetime.now()
    trigger_minute = current_time.hour
    trigger_hour = current_time.minute + 1
    
    # 计算触发时间
    cron_expr = f"{trigger_minute} {hour}"
    task_name= args.get('task_name')
    buildings= json.dumps(['4'])
    recipients = json.dumps(['test@example.com'])
    subject_prefix = '[部署测试]'
    start_time= '23:20:00'
            end_time= '05:30:00'
            enabled=1
            """
    
 # 插入
    cursor.execute('''
        INSERT INTO email_tasks 
        (task_name, username, buildings, recipients, subject_prefix, start_time, end_time, cron_expression, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
    ''', (
        '部署验证测试',
        'admin',
        json.dumps(['4']),
        json.dumps(['test@example.com'])
        '[部署测试]',
        '23:20:00',
        '05:30:00'
        '22 13 * * *'
        1
    )
    
    conn.commit()
    print(f"测试任务已创建。 cron: {trigger_minute} {hour}, next run at: {next_run_at})}")
    conn.close()
    
 # 验证数据
    c.execute('SELECT id, task_name, buildings, recipients, cron_expression FROM email_tasks WHERE task_name = ?', ('部署验证测试',))
    row = c.fetchone()
    if row:
        print(f"ID: {row[0]}, 任务: {row[1]}")
        print(f"buildings: {row[2]}")
        print(f"recipients: {row[3]}")
        print(f"cron: {row[4]}")
        
        # 风格验证通过")
        print("服务已重启，调度器已加载新任务")
        
        # 重启服务
        os.system(f'./restart.sh')
        time.sleep(60)
        
        # 查看日志
        tail -100 /myApps0217/tianjin-edu/out.log
