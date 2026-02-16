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
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"配置文件 {self.config_path} 不存在")

            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件出错: {e}")
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
        """从环境变量获取 ChromeDriver 路径"""
        env = self.get_env()
        driver_from_env = os.environ.get('CHROMEDRIVER_PATH')
        if driver_from_env:
            return driver_from_env
        if env == "prod":
            return self.config.get("driver_location_prod", "")
        else:
            return self.config.get("driver_location_test", "")

    def get_binary_location(self):
        """从环境变量获取 Chrome 浏览器路径"""
        env = self.get_env()
        binary_from_env = os.environ.get('CHROME_BINARY_PATH')
        if binary_from_env:
            return binary_from_env
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
