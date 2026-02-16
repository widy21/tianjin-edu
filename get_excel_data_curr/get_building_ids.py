"""
获取所有公寓楼栋的 buildingId
"""
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ConfigTool import ConfigTool

config_tool = ConfigTool("./config.json")

username = config_tool.get_username()
password = config_tool.get_password()

if username == '' or password == '':
    print('用户信息为空，请检查配置')
    sys.exit(-1)

def get_building_list():
    login_url = "http://gygl.tust.edu.cn:8080/da-roadgate-resident/index"

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 关闭无头模式以便调试
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(login_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))

        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

        WebDriverWait(driver, 10).until(EC.title_contains("公寓出入安全分析系统"))
        print("登录成功！\n")

        # 登录后需要点击进入出入安全模块
        print("正在进入出入安全模块...")
        time.sleep(2)

        # 尝试点击出入安全图标
        try:
            # 查找并点击出入安全按钮
            img_button = driver.find_element(By.CSS_SELECTOR, "img[src*='rg.png']")
            img_button.click()
            time.sleep(3)
        except Exception as e:
            print(f"点击出入安全按钮失败: {e}")
            # 直接访问页面
            driver.get("http://gygl.tust.edu.cn:8080/da-roadgate-resident/inout/inout_record/index")
            time.sleep(3)

        # 切换到可能的 iframe
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"找到 {len(iframes)} 个 iframe")
            for i, iframe in enumerate(iframes):
                print(f"  iframe {i}: {iframe.get_attribute('src')}")
            if iframes:
                driver.switch_to.frame(iframes[0])
                time.sleep(1)
        except Exception as e:
            print(f"切换 iframe 失败: {e}")

        print("=" * 70)
        print("所有公寓楼栋列表：")
        print("=" * 70)

        # 查找所有 select 元素
        select_elements = driver.find_elements(By.TAG_NAME, "select")
        print(f"找到 {len(select_elements)} 个下拉框")

        for sel in select_elements:
            sel_id = sel.get_attribute("id") or sel.get_attribute("name") or "unknown"
            options = sel.find_elements(By.TAG_NAME, "option")
            print(f"\n下拉框: {sel_id}")
            for opt in options:
                value = opt.get_attribute("value")
                text = opt.text.strip()
                if value:
                    print(f'  "{text}": "{value}",')

        # 等待用户查看
        print("\n" + "=" * 70)
        print("请在浏览器中手动选择校区和楼群，然后按回车继续...")
        input()

        # 再次获取楼栋列表
        print("\n获取楼栋下拉框内容：")
        select_elements = driver.find_elements(By.TAG_NAME, "select")
        for sel in select_elements:
            sel_id = sel.get_attribute("id") or sel.get_attribute("name") or "unknown"
            if "building" in sel_id.lower():
                options = sel.find_elements(By.TAG_NAME, "option")
                print(f"\n下拉框: {sel_id}")
                for opt in options:
                    value = opt.get_attribute("value")
                    text = opt.text.strip()
                    if value and len(value) > 10:
                        print(f'  "{text}": "{value}",')

        print("=" * 70)
            
    except TimeoutException:
        print("登录超时")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    get_building_list()

