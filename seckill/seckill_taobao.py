#!/usr/bin/env python3
# encoding=utf-8


import os
import json
import platform
from time import sleep
from random import choice
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

import seckill.settings as utils_settings
from utils.utils import get_useragent_data
from utils.utils import notify_user

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.options import Options



# 抢购失败最大次数
max_retry_count = 30


def default_chrome_path():

    driver_dir = getattr(utils_settings, "DRIVER_DIR", None)
    if platform.system() == "Windows":
        if driver_dir:
            return os.path.abspath(os.path.join(driver_dir, "chromedriver.exe"))

        raise Exception("The chromedriver drive path attribute is not found.")
    else:
        if driver_dir:
            return os.path.abspath(os.path.join(driver_dir, "chromedriver"))

        raise Exception("The chromedriver drive path attribute is not found.")


class ChromeDrive:

    def __init__(self, chrome_path=default_chrome_path(), seckill_time=None, password=None):
        self.chrome_path = chrome_path
        self.seckill_time = seckill_time
        self.seckill_time_obj = datetime.strptime(self.seckill_time, '%Y-%m-%d %H:%M:%S')
        self.password = password
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")  # 前面设置的端口号
        self.driver = webdriver.Chrome(executable_path=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe',
                                        options=self.chrome_options)  # executable执行webdriver驱动的文件

    def keep_wait(self):
        print("等待到点抢购...")
        while True:
            current_time = datetime.now()
            if (self.seckill_time_obj - current_time).seconds > 180:
                self.driver.get("https://cart.taobao.com/cart.htm")
                print("每分钟刷新一次界面，防止登录超时...")
                sleep(60)
            else:
                self.get_cookie()
                print("抢购时间点将近，停止自动刷新，准备进入抢购阶段...")
                break


    def sec_kill(self):
        self.keep_wait()
        self.driver.get("https://cart.taobao.com/cart.htm")
        sleep(1)

        if self.driver.find_element_by_id("J_SelectAll1"):
            self.driver.find_element_by_id("J_SelectAll1").click()
            print("已经选中全部商品！！！")

        submit_succ = False
        retry_count = 0

        while True:
            now = datetime.now()
            if now >= self.seckill_time_obj:
                print(f"开始抢购, 尝试次数： {str(retry_count)}")
                if submit_succ:
                    print("订单已经提交成功，无需继续抢购...")
                    break
                if retry_count > max_retry_count:
                    print("重试抢购次数达到上限，放弃重试...")
                    break

                retry_count += 1

                try:
                    while True:
                        try:
                            self.driver.find_element_by_id("J_Go").click()
                        except WebDriverException:
                            break
                        print("已经点击结算按钮...")
                        click_submit_times = 0
                    while True:
                        try:
                            if click_submit_times < 10:
                                self.driver.find_element_by_link_text('提交订单').click()
                                print("已经点击提交订单按钮")
                                submit_succ = True
                                break
                            else:
                                print("提交订单失败...")
                        except Exception as e:

                            print("没发现提交按钮, 页面未加载, 重试...")
                            click_submit_times = click_submit_times + 1
                            sleep(0.1)
                except Exception as e:
                    print(e)
                    print("临时写的脚本, 可能出了点问题!!!")

            sleep(0.1)
        if submit_succ:
            if self.password:
                self.pay()

    def pay(self):
        try:
            element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'sixDigitPassword')))
            element.send_keys(self.password)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'J_authSubmit'))).click()
            notify_user(msg="付款成功")
        except:
            notify_user(msg="付款失败")
        finally:
            sleep(60)
            self.driver.quit()


    def get_cookie(self):
        cookies = self.driver.get_cookies()
        cookie_json = json.dumps(cookies)
        with open('./cookies.txt', 'w', encoding = 'utf-8') as f:
            f.write(cookie_json)
