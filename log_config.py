# log_config.py
import logging
from logging.handlers import RotatingFileHandler

_logging_configured = False  # 全局标志，记录是否已配置

def setup_logging():
    global _logging_configured
    
    if _logging_configured:  # 如果已经配置过，直接返回
        return
    
    log_file = 'edu.log'
    log_max_size = 100 * 1024 * 1024  # 100MB
    log_backup_count = 5
    
    # 清除现有的 handlers（避免重复）
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # 文件 handler
    file_handler = RotatingFileHandler(log_file, maxBytes=log_max_size, backupCount=log_backup_count)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    root_logger.setLevel(logging.DEBUG)
    
    _logging_configured = True  # 标记为已配置
