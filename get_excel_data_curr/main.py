import sys
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
# from gen_excel_data import gen_excel_data
from selenium.webdriver.chrome.service import Service

config_tool = ConfigTool("./get_excel_data_curr/config.json")

# 登录信息
username = config_tool.get_username()
password = config_tool.get_password()

if username == '' or password == '':
    print('用户信息为空，请检查配置')
    sys.exit(-1)

def verify():
    # 获取当前日期
    current_date = datetime.now().date()
    # 定义目标日期
    target_date_str = "2025-06-01"
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    # 比较当前日期和目标日期
    if config_tool.get_flag() != 'whosyourdady':
        if current_date <= target_date:
            # print(f"当前日期 {current_date} 小于等于目标日期 {target_date}")
            pass
        else:
            logging.debug(f"当前日期 {current_date} 大于目标日期 {target_date}，请注册后使用")

def process(data=None):
    verify()

    # 登录 URL
    login_url = "http://gygl.tust.edu.cn:8080/da-roadgate-resident/index  "
    # 设置 Chrome 选项
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 无头模式，暂时注释以便调试
    #options.add_argument("--start-maximized")  # 最大化窗口
    options.add_argument("--disable-gpu")  # 禁用 GPU 加速
    #options.add_argument("--window-size=1920,1080")  # 设置窗口大小
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
            exit()

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
                    exit()

        # 等待页面加载完成
        try:
            WebDriverWait(driver, 10).until(EC.title_contains("公寓出入安全分析系统"))
            print("登录成功！")

            # 获取当前页面的所有 cookie
            cookies = driver.get_cookies()
            # 将 cookie 添加到请求头中
            # cookie_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            value_ = cookies[0]['value']
            # print(f"cookie_str: {value_}")

            bid_dict = config_tool.get_bid_dict()
            new_bid_dict = {}
            for idx in data['buildings']:
                new_bid_dict[idx] = bid_dict[idx]

            # 循环查n个公寓数据
            print("数据处理中，具体进度如下：")
            ret_dict = {}
            for b_num, bid in new_bid_dict.items():
                ret_data = t3.deal(value_, bid, b_num, data)
                ret_dict[b_num] = ret_data

            # 生成excel数据
            file_name = gen_excel_data_v1(ret_dict, data['username'])

            # 关闭浏览器
            # driver.quit()

            # 点击出入安全按钮
            # img_button = WebDriverWait(driver, 10).until(
            #     EC.element_to_be_clickable((By.CSS_SELECTOR, "img[src='resources/images/application/webos/rg.png']"))
            # )
            # img_button.click()

            return {
                'file_name':file_name,
                'status':'success',
            }

        except TimeoutException:
            # 如果等待超时，检查当前页面标题
            print(f"当前页面标题: {driver.title}")
            print("登录后页面加载超时，可能登录失败。")
            return {
                'msg': "登录后页面加载超时，可能登录失败。",
                'status': 'success',
            }

        # 保持浏览器打开，方便调试
        # input("按任意键关闭...")

    except Exception as e:
        traceback.print_exc()
        print(f"处理失败: {e}")
        return {
            'msg': e,
            'status': 'false',
        }

    finally:
        # 关闭浏览器
        driver.quit()

