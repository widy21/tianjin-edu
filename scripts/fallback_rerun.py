#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
每日 07:10 兜底任务（crontab 触发）：
检查当天 07:00 的「统计全部公寓」(email_task id=2) 是否已有成功记录，
若当天尚无 success 记录，则自动补跑一次。
历史故障（如 2026-10-20 上游系统瞬时故障）由此兜底。
"""
import sys
import os
import logging
from datetime import date

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from database.db import Database
from scheduler.task_manager import TaskManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fallback_rerun')

TARGET_TASK_ID = 2


def main():
    today_str = date.today().strftime('%Y-%m-%d')
    db = Database()

    # 检查该任务当天是否已有成功记录
    conn = db._get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM task_logs "
            "WHERE email_task_id = ? AND status = 'success' "
            "AND created_at >= ?",
            (TARGET_TASK_ID, today_str + ' 00:00:00')
        ).fetchone()
        success_count = row[0]
    finally:
        conn.close()

    if success_count > 0:
        logger.info(f'任务 {TARGET_TASK_ID} 今天({today_str})已有成功记录，跳过兜底补跑')
        return

    logger.info(f'任务 {TARGET_TASK_ID} 今天({today_str})尚无成功记录，开始兜底补跑...')
    task = db.get_email_task(TARGET_TASK_ID)
    if not task:
        logger.error(f'未找到任务 id={TARGET_TASK_ID}')
        sys.exit(1)

    tm = TaskManager(db)
    tm.execute_single_task(task)
    logger.info('兜底补跑流程结束')


if __name__ == '__main__':
    main()
