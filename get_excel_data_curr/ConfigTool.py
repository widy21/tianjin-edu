import json
import logging


class ConfigTool:
    """
    配置工具类，从 SQLite 数据库的 system_config 表读取配置。
    """

    def __init__(self, db):
        """
        :param db: database.db.Database 实例
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.logger.debug("ConfigTool 已初始化（从数据库读取配置）")

    def _get(self, key, default=None):
        """从数据库读取单个配置值"""
        return self.db.get_config(key, default)

    def _get_json(self, key, default=None):
        """从数据库读取 JSON 格式的配置值并解析"""
        raw = self._get(key)
        if raw is None:
            return default if default is not None else {}
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.warning(f"配置项 {key} 的值不是有效 JSON: {e}")
            return default if default is not None else {}

    def get_username(self):
        """获取公寓系统用户名"""
        return self._get('tust_username', '')

    def get_password(self):
        """获取公寓系统密码"""
        return self._get('tust_password', '')

    def get_pagesize(self):
        """获取分页大小"""
        val = self._get('pagesize', '20')
        try:
            return int(val)
        except (ValueError, TypeError):
            return 20

    def get_data_cfg(self):
        """获取学院名称映射（JSON）"""
        return self._get_json('data_cfg', {})

    def get_bid_dict(self):
        """获取楼栋 ID 映射（JSON）"""
        return self._get_json('bid_dict', {})

    def get_beginTime(self):
        """获取默认查询开始时间"""
        return self._get('begin_time', '23:20:00')

    def get_endTime(self):
        """获取默认查询结束时间"""
        return self._get('end_time', '05:30:00')

    def get_flag(self):
        """获取 flag 配置（兼容旧逻辑）"""
        return self._get('flag', '')

    def get_env(self):
        """获取运行环境"""
        return self._get('env', 'test')

    def get_driver_location(self):
        """
        获取 ChromeDriver 路径。
        根据 env 配置决定返回测试环境还是生产环境路径。
        """
        env = self.get_env()
        if env == "prod":
            return self._get('chromedriver_path_prod', '')
        else:
            return self._get('chromedriver_path', '')

    def get_binary_location(self):
        """
        获取 Chrome 浏览器路径。
        根据 env 配置决定返回测试环境还是生产环境路径。
        """
        env = self.get_env()
        if env == "prod":
            return self._get('chrome_binary_path_prod', '')
        else:
            return self._get('chrome_binary_path', '')


# 使用示例
if __name__ == "__main__":
    from database.db import Database
    db = Database()
    config_tool = ConfigTool(db)

    print("用户名:", config_tool.get_username())
    print("密码:", "***" if config_tool.get_password() else "(未设置)")
    print("页面大小:", config_tool.get_pagesize())
    print("学院映射关系:", config_tool.get_data_cfg())

    # 访问 data_cfg 中的具体内容
    print("\n学院名称映射:")
    data_cfg = config_tool.get_data_cfg()
    for key, value in data_cfg.items():
        print(f"{key}: {value}")
