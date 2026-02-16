import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database.db import Database
from scheduler.task_manager import TaskManager


class SchedulerManager:
    def __init__(self, db):
        """
        :param db: Database 实例
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.scheduler = None

    def start(self):
        """启动定时调度器，根据数据库中的配置加载任务"""
        try:
            scheduler_enabled = self.db.get_config('scheduler_enabled', 'false')
            if scheduler_enabled.lower() != 'true':
                self.logger.info("定时任务调度器未启用（scheduler_enabled != true）")
                return

            timezone = self.db.get_config('scheduler_timezone', 'Asia/Shanghai')
            self.scheduler = BackgroundScheduler(timezone=timezone)

            task_manager = TaskManager(self.db)

            # 获取所有启用的邮件任务，为每个任务创建独立的调度
            email_tasks = self.db.get_enabled_email_tasks()

            if not email_tasks:
                self.logger.info("没有启用的邮件任务，调度器不启动")
                return

            for task in email_tasks:
                cron_expr = task.get('cron_expression', '0 6 * * *')
                parts = cron_expr.split()
                if len(parts) == 5:
                    minute, hour, day, month, day_of_week = parts
                else:
                    minute, hour = '0', '6'
                    day = month = day_of_week = '*'

                job_id = f"email_task_{task['id']}"
                self.scheduler.add_job(
                    func=task_manager.execute_single_task,
                    args=[task],
                    trigger=CronTrigger(
                        minute=minute, hour=hour, day=day,
                        month=month, day_of_week=day_of_week
                    ),
                    id=job_id,
                    name=task['task_name'],
                    replace_existing=True
                )
                self.logger.info(f"已添加定时任务: {task['task_name']} (cron: {cron_expr})")

            self.scheduler.start()
            self.logger.info(f"定时调度器已启动，共 {len(email_tasks)} 个任务")

        except Exception as e:
            self.logger.error(f"启动调度器失败: {str(e)}")

    def stop(self):
        """停止调度器"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("定时调度器已停止")

    def reload(self):
        """重新加载任务配置"""
        self.stop()
        self.start()

    def get_jobs(self):
        """获取当前所有调度任务"""
        if not self.scheduler:
            return []
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': str(job.next_run_time) if job.next_run_time else None,
            }
            for job in self.scheduler.get_jobs()
        ]

