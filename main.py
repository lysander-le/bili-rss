import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator

# 配置：输出文件夹
OUTPUT_DIR = 'output'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 设置 Chrome 选项（无头模式，服务器专用）
chrome_options = Options()
chrome_options.add_argument("--headless")  # 不显示界面
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 初始化浏览器
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def generate_rss(uid):
    url = f'https://space.bilibili.com/{uid}/video'
    print(f"正在抓取: {url}")
    
    try:
        driver.get(url)
        time.sleep(5) # 等待页面加载
        
        # 获取 UP 主名字
        username = driver.find_element(By.ID, 'h-name').text
        print(f"UP主名称: {username}")

        # 初始化 RSS 生成器
        fg = FeedGenerator()
        fg.id(url)
        fg.title(f'{username} 的 Bilibili 动态')
        fg.author({'name': username})
        fg.link(href=url, rel='alternate')
        fg.description(f'{username} 的最新视频更新')
        fg.language('zh-CN')

        # 查找视频列表
        # 注意：B站的前端代码可能会变，这里的 class 需要根据实际情况调整
        # 目前使用的是通用的 CSS Selector 查找方法
        videos = driver.find_elements(By.CSS_SELECTOR, '.small-item.fakeDanmu-item')
        
        for video in videos[:10]: # 只取最新的10个
            try:
                title_element = video.find_element(By.CSS_SELECTOR, '.title')
                title = title_element.text
                video_url = video.find_element(By.TAG_NAME, 'a').get_attribute('href')
                
                # 获取封面图
                try:
                    cover = video.find_element(By.TAG_NAME, 'img').get_attribute('src')
                    if not cover.startswith('http'):
                        cover = 'https:' + cover
                except:
                    cover = ""

                # 获取发布时间 (B站通常显示 "昨天", "3小时前", 这里简化处理，不进行复杂时间转换)
                try:
                    pub_time = video.find_element(By.CSS_SELECTOR, '.time').text
                except:
                    pub_time = "Recently"

                fe = fg.add_entry()
                fe.id(video_url)
                fe.title(title)
                fe.link(href=video_url)
                # 在描述里插入封面图，Readwise 抓取效果更好
                fe.description(f'<img src="{cover}"><br>发布时间: {pub_time}<br><a href="{video_url}">点击观看</a>')
                
            except Exception as e:
                print(f"解析单个视频出错: {e}")
                continue

        # 保存为 XML
        rss_file = os.path.join(OUTPUT_DIR, f'{uid}.xml')
        fg.rss_file(rss_file)
        print(f"成功生成: {rss_file}")

    except Exception as e:
        print(f"抓取 {uid} 失败: {e}")

# 读取 UID 列表并运行
with open('ids.txt', 'r') as f:
    uids = [line.strip() for line in f if line.strip()]

for uid in uids:
    generate_rss(uid)

driver.quit()
