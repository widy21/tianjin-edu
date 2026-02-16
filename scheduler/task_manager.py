import logging
import time
from datetime import datetime
from get_excel_data_curr.main import process
from scheduler.email_sender import EmailSender
from database.db import Database


class TaskManager:
    def __init__(self, db):
        """
        :param db: Database 实例
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

    def execute_single_task(self, email_task):
        """
        执行单个邮件任务
        :param email_task: email_tasks 表的一行数据（dict）
        """
        task_id = email_task['id']
        username = email_task['username']
        log_id = self.db.create_task_log(task_id, username, 'running')

        try:
            self.logger.info(f"开始执行任务: {email_task['task_name']} (用户: {username})")

            # 构造 process() 需要的请求数据
            request_data = {
                'buildings': email_task['buildings'],
                'username': username,
                'startTime': email_task['start_time'],
                'endTime': email_task['end_time'],
            }

            # 调用现有的 process 函数生成 Excel
            result = process(request_data)

            if result.get('status') == 'success':
                file_path = result['file_name']

                # 发送邮件
                email_sender = EmailSender.from_db(self.db)
                recipients = email_task['recipients']
                now_str = datetime.now().strftime('%Y-%m-%d')
                subject = f"{email_task.get('subject_prefix', '')}{now_str} 公寓学生晚归名单"
                body = (
                    f"您好：\n\n"
                    f"附件是 {now_str} 的公寓学生晚归名单。\n\n"
                    f"查询楼栋：{', '.join(email_task['buildings'])}\n"
                    f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"此邮件由系统自动发送，请勿回复。"
                )

                success, message = email_sender.send_email(
                    recipients=recipients,
                    subject=subject,
                    body=body,
                    attachments=[file_path]
                )

                if success:
                    self.db.update_task_log(log_id, 'success', file_path=file_path)
                    self.logger.info(f"任务执行成功: {email_task['task_name']}")
                else:
                    self.db.update_task_log(log_id, 'email_failed', file_path=file_path, error_message=message)
                    self.logger.error(f"邮件发送失败: {email_task['task_name']} - {message}")
            else:
                error_msg = result.get('msg', '数据查询失败')
                self.db.update_task_log(log_id, 'failed', error_message=str(error_msg))
                self.logger.error(f"数据查询失败: {email_task['task_name']} - {error_msg}")

        except Exception as e:
            self.db.update_task_log(log_id, 'failed', error_message=str(e))
            self.logger.error(f"任务执行异常: {email_task['task_name']} - {str(e)}")

    def execute_all_enabled_tasks(self):
        """执行所有启用的邮件任务"""
        tasks = self.db.get_enabled_email_tasks()
        self.logger.info(f"开始执行定时任务，共 {len(tasks)} 个启用的任务")

        for task in tasks:
            self.execute_single_task(task)
            # 任务之间间隔几秒，避免并发压力
            time.sleep(2)

        self.logger.info("所有定时任务执行完毕")

