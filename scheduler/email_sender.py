import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


class EmailSender:
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password, use_tls=True):
        self.smtp_server = smtp_server
        self.smtp_port = int(smtp_port)
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls if isinstance(use_tls, bool) else str(use_tls).lower() == 'true'
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_db(cls, db):
        """从数据库配置创建 EmailSender 实例"""
        return cls(
            smtp_server=db.get_config('smtp_server', 'smtp.qq.com'),
            smtp_port=db.get_config('smtp_port', '587'),
            sender_email=db.get_config('sender_email', ''),
            sender_password=db.get_config('sender_password', ''),
            use_tls=db.get_config('smtp_use_tls', 'true'),
        )

    def send_email(self, recipients, subject, body, attachments=None):
        """
        发送邮件
        :param recipients: 收件人列表
        :param subject: 邮件主题
        :param body: 邮件正文
        :param attachments: 附件文件路径列表
        :return: (success, message)
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject

            # 正文
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 附件
            if attachments:
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        self.logger.warning(f"附件不存在，跳过: {file_path}")
                        continue
                    filename = os.path.basename(file_path)
                    with open(file_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=filename)
                        part['Content-Disposition'] = f'attachment; filename="{filename}"'
                        msg.attach(part)

            # 发送
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            self.logger.info(f"邮件发送成功: {recipients}")
            return True, "邮件发送成功"

        except Exception as e:
            self.logger.error(f"邮件发送失败: {str(e)}")
            return False, str(e)

