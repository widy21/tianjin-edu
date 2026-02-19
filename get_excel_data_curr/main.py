import traceback
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import get_excel_data_curr.t3 as t3
from get_excel_data_curr.ConfigTool import ConfigTool
from get_excel_data_curr.gen_excel_data_v1 import gen_excel_data_v1
from selenium.webdriver.chrome.service import Service
from database.db import Database


def _get_config_tool():
    """创建 Database 和 ConfigTool 实例"""
    db = Database()
    return ConfigTool(db)


def verify(config_tool):
    # 获取当前日期
    current_date = datetime.now().date()
    # 定义目标日期
    target_date_str = "2025-06-01"
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    # 比较当前日期和目标日期
    if config_tool.get_flag() != 'whosyourdady':
        if current_date <= target_date:
            pass
        else:
            logging.debug(f"当前日期 {current_date} 大于目标日期 {target_date}，请注册后使用")


def process(data=None):
    # 从数据库读取配置
    config_tool = _get_config_tool()

    # 登录信息
    username = config_tool.get_username()
    password = config_tool.get_password()

    if username == '' or password == '':
        return {
            'msg': '公寓系统用户信息为空，请在管理页面检查配置',
            'status': 'false',
        }

    verify(config_tool)

    # 登录 URL
    login_url = "http://gygl.tust.edu.cn:8080/da-roadgate-resident/index  "
    # 设置 Chrome 选项
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 无头模式
    options.add_argument("--disable-gpu")  # 禁用 GPU 加速
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-dev-shm-usage')

    binary_location = config_tool.get_binary_location()
    driver_location = config_tool.get_driver_location()

    if binary_location != "":
        options.browser_version = "stable"  # 自动匹配稳定版
        options.binary_location = binary_location
    if driver_location != "":
        service = Service(driver_location)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        # 创建 WebDriver
        driver = webdriver.Chrome(options=options)

    try:
        # 打开登录页面
        driver.get(login_url)

        # 等待页面加载完成并定位元素
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
        except TimeoutException:
            print("等待超时，页面加载缓慢或网络问题。")
            driver.quit()
            return {
                'msg': '等待超时，页面加载缓慢或网络问题。',
                'status': 'false',
            }

        # 输入用户名
        driver.find_element(By.NAME, "username").send_keys(username)

        # 输入密码
        driver.find_element(By.NAME, "password").send_keys(password)

        # 点击登录按钮
        try:
            driver.find_element(By.NAME, "submit").click()
        except NoSuchElementException:
            try:
                driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
            except NoSuchElementException:
                try:
                    driver.find_element(By.XPATH, "//button[@type='submit']").click()
                except NoSuchElementException:
                    print("无法找到登录按钮，请检查页面的 HTML 结构。")
                    driver.quit()
                    return {
                        'msg': '无法找到登录按钮，请检查页面的 HTML 结构。',
                        'status': 'false',
                    }

        # 等待页面加载完成
        try:
            WebDriverWait(driver, 10).until(EC.title_contains("公寓出入安全分析系统"))
            print("登录成功！")

            # 获取当前页面的所有 cookie
            cookies = driver.get_cookies()
            value_ = cookies[0]['value']

            bid_dict = config_tool.get_bid_dict()
            new_bid_dict = {}
            for idx in data['buildings']:
                new_bid_dict[idx] = bid_dict[idx]

            # 从配置获取 page_size 和 data_cfg，传递给子模块
            page_size = config_tool.get_pagesize()
            data_cfg = config_tool.get_data_cfg()

            # 循环查n个公寓数据
            print("数据处理中，具体进度如下：")
            ret_dict = {}
            for b_num, bid in new_bid_dict.items():
                ret_data = t3.deal(value_, bid, b_num, data, page_size=page_size)
                ret_dict[b_num] = ret_data

            # 生成excel数据
            file_name = gen_excel_data_v1(ret_dict, data['username'], data_cfg=data_cfg, request_data=data)

            return {
                'file_name': file_name,
                'status': 'success',
            }

        except TimeoutException:
            # 如果等待超时，检查当前页面标题
            print(f"当前页面标题: {driver.title}")
            print("登录后页面加载超时，可能登录失败。")
            return {
                'msg': "登录后页面加载超时，可能登录失败。",
                'status': 'success',
            }

    except Exception as e:
        traceback.print_exc()
        print(f"处理失败: {e}")
        return {
            'msg': str(e),
            'status': 'false',
        }

    finally:
        # 关闭浏览器
        driver.quit()

