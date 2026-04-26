import traceback
import logging
import time
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


# 重试配置
MAX_LOGIN_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 5  # 重试间隔（秒）

logger = logging.getLogger(__name__)


def _get_config_tool():
    """创建 Database 和 ConfigTool 实例"""
    db = Database()
    return ConfigTool(db)


def verify(config_tool):
    """验证配置工具"""
    current_date = datetime.now().date()
    target_date_str = "2025-06-01"
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    if config_tool.get_flag() != 'whosyourdady':
        if current_date <= target_date:
            pass
        else:
            logging.debug(f"当前日期 {current_date} 大于目标日期 {target_date}，请注册后使用")


def _login_with_retry(driver, login_url, username, password):
    """
    带重试的登录函数
    :param driver: WebDriver 实例
    :param login_url: 登录页面 URL
    :param username: 用户名
    :param password: 密码
    :return: tuple(success: bool, message: str, cookies: list or None)
    """
    for attempt in range(1, MAX_LOGIN_RETRIES + 1):
        logger.info(f"登录尝试 {attempt}/{MAX_LOGIN_RETRIES}")
        
        try:
            # 打开登录页面
            driver.get(login_url)
            
            # 等待页面加载完成并定位元素
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
            except TimeoutException:
                if attempt < MAX_LOGIN_RETRIES:
                    logger.warning(f"第 {attempt} 次登录失败: 页面加载超时，{RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    return (False, "页面加载超时，已达最大重试次数", None)
            
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
                        return (False, "无法找到登录按钮，请检查页面的 HTML 结构", None)
            
            # 磉待登录成功（页面标题变化）
            try:
                WebDriverWait(driver, 10).until(EC.title_contains("公寓出入安全分析系统"))
                print("登录成功！login_url}")
                # 获取 cookie
                cookies = driver.get_cookies()
                return (True, "登录成功", cookies)
            except TimeoutException:
                if attempt < MAX_LOGIN_RETRIES:
                    logger.warning(f"第 {attempt} 次登录失败: 登录后页面加载超时，{RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    return (False, "登录后页面加载超时，已达最大重试次数", None)
                    
        except Exception as e:
            if attempt < MAX_LOGIN_RETRIES:
                logger.warning(f"第 {attempt} 次登录失败: {str(e)}， {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
                continue
            else:
                return (False, f"登录异常: {str(e)}", None)
    
    return (False, "超过最大重试次数", None)


def process(data=None):
    """主处理函数，带登录重试机制"""
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
    login_url = "http://gygl.tust.edu.cn:8080/da-roadgate-resident/index"
    
    # 设置 Chrome 选项
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-dev-shm-usage')
    
    binary_location = config_tool.get_binary_location()
    driver_location = config_tool.get_driver_location()
    
    if binary_location != "":
        options.browser_version = "stable"
        options.binary_location = binary_location
    if driver_location != "":
        service = Service(driver_location)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)
    
    try:
        # 使用带重试的登录函数
        success, message, cookies = _login_with_retry(driver, login_url, username, password)
        
        if not success:
            driver.quit()
            return {
                'msg': message,
                'status': 'false',
            }
        
        # 获取 cookie 值
        value_ = cookies[0]['value']
        
        bid_dict = config_tool.get_bid_dict()
        new_bid_dict = {}
        for idx in data['buildings']:
            new_bid_dict[idx] = bid_dict[idx]
        
        # 从配置获取 page_size 和 data_cfg
        page_size = config_tool.get_pagesize()
        data_cfg = config_tool.get_data_cfg()
        
        # 循环查n个公寓数据
        print("数据处理中，具体进度如下：")
        ret_dict = {}
        fetch_errors = []
        for b_num, bid in new_bid_dict.items():
            try:
                ret_data = t3.deal(value_, bid, b_num, data, page_size=page_size)
                ret_dict[b_num] = ret_data
            except t3.DataFetchError as e:
                error_msg = f"楼栋{b_num}: {e}"
                fetch_errors.append(error_msg)
                logger.error(f"楼栋取数失败: {error_msg}")

        if not ret_dict:
            msg = "所有楼栋取数失败：" + "；".join(fetch_errors)
            logger.error(msg)
            return {
                'msg': msg,
                'status': 'false',
            }

        if fetch_errors:
            logger.warning(f"部分楼栋取数失败，继续生成成功楼栋报表：{'；'.join(fetch_errors)}")
        
        # 生成excel数据
        file_name = gen_excel_data_v1(ret_dict, data['username'], data_cfg=data_cfg, request_data=data)
        
        return {
            'file_name': file_name,
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
        driver.quit()
