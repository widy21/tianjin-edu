import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ConfigTool:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """
        加载配置文件，支持回退机制：
        1. 优先读取 config.json（本地配置，包含敏感信息，被 gitignore）
        2. 如果不存在，回退到 config.json.example（模板文件，可提交到 Git）
        """
        config = {}
        
        # 尝试读取主配置文件
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"已加载配置文件: {self.config_path}")
                return config
            except Exception as e:
                print(f"加载配置文件出错: {e}")
        
        # 回退到 example 文件
        example_path = self.config_path.replace('.json', '.json.example')
        if os.path.exists(example_path):
            try:
                with open(example_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"已加载配置模板: {example_path}")
                return config
            except Exception as e:
                print(f"加载配置模板出错: {e}")
        
        print("警告: 未找到任何配置文件，将使用默认值")
        return {}

    def get_username(self):
        """从环境变量获取用户名"""
        return os.environ.get('TUST_USERNAME', '')

    def get_password(self):
        """从环境变量获取密码"""
        return os.environ.get('TUST_PASSWORD', '')

    def get_pagesize(self):
        return self.config.get("pagesize", 20)

    def get_data_cfg(self):
        return self.config.get("data_cfg", {})

    def get_bid_dict(self):
        return self.config.get("bid_dict", {})

    def get_beginTime(self):
        """优先从环境变量获取，其次从配置文件"""
        return os.environ.get('BEGIN_TIME') or self.config.get("beginTime", "23:20:00")

    def get_endTime(self):
        """优先从环境变量获取，其次从配置文件"""
        return os.environ.get('END_TIME') or self.config.get("endTime", "05:30:00")

    def get_flag(self):
        return self.config.get("flag", "")

    def get_env(self):
        """优先从环境变量获取运行环境"""
        return os.environ.get('ENV') or self.config.get("env", "test")

    def get_driver_location(self):
        """
        从环境变量获取 ChromeDriver 路径
        环境变量优先级最高，即使为空字符串也返回（让 Selenium 自动管理）
        """
        if 'CHROMEDRIVER_PATH' in os.environ:
            return os.environ.get('CHROMEDRIVER_PATH', '')
        env = self.get_env()
        if env == "prod":
            return self.config.get("driver_location_prod", "")
        else:
            return self.config.get("driver_location_test", "")

    def get_binary_location(self):
        """
        从环境变量获取 Chrome 浏览器路径
        环境变量优先级最高，即使为空字符串也返回（让 Selenium 自动管理）
        """
        if 'CHROME_BINARY_PATH' in os.environ:
            return os.environ.get('CHROME_BINARY_PATH', '')
        env = self.get_env()
        if env == "prod":
            return self.config.get("binary_location_prod", "")
        else:
            return self.config.get("binary_location_test", "")


# 使用示例
if __name__ == "__main__":
    config_path = "config.json"
    config_tool = ConfigTool(config_path)

    print("用户名:", config_tool.get_username())
    print("密码:", "***" if config_tool.get_password() else "(未设置)")
    print("页面大小:", config_tool.get_pagesize())
    print("学院映射关系:", config_tool.get_data_cfg())

    # 访问 data_cfg 中的具体内容
    print("\n学院名称映射:")
    data_cfg = config_tool.get_data_cfg()
    for key, value in data_cfg.items():
        print(f"{key}: {value}")
