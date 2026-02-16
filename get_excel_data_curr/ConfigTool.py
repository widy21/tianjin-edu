import json
import os


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
        return self.config.get("username", "")

    def get_password(self):
        return self.config.get("password", "")

    def get_pagesize(self):
        return self.config.get("pagesize", 20)

    def get_data_cfg(self):
        return self.config.get("data_cfg", {})

    def get_bid_dict(self):
        return self.config.get("bid_dict", {})

    def get_beginTime(self):
        return self.config.get("beginTime", "")

    def get_endTime(self):
        return self.config.get("endTime", "")

    def get_flag(self):
        return self.config.get("flag", "")

    def get_env(self):
        return self.config.get("env", "test")

    def get_driver_location(self):
        env = self.get_env()
        if env == "prod":
            return self.config.get("driver_location_prod", "")
        else:
            return self.config.get("driver_location_test", "")

    def get_binary_location(self):
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
    print("密码:", config_tool.get_password())
    print("页面大小:", config_tool.get_pagesize())
    print("学院映射关系:", config_tool.get_data_cfg())

    # 访问 data_cfg 中的具体内容
    print("\n学院名称映射:")
    data_cfg = config_tool.get_data_cfg()
    for key, value in data_cfg.items():
        print(f"{key}: {value}")