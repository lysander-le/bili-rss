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

# --- 关键修改：增加伪装头，防止被B站拦截 ---
chrome_options = Options()
chrome_options.add_argument("--headless")  # 无头模式
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# 伪装成正常的 Windows Chrome 浏览器
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
chrome_options.add_argument("--window-size=1920,1080")

# 初始化浏览器
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def generate_rss(uid):
    url = f'https://space.bilibili.com/{uid}/video'
    print(f"--------------------------------")
    print(f"正在尝试抓取: {url}")
    
    try:
        driver.get(url)
        time.sleep(5) # 等待页面加载
        
        # 尝试获取 UP 主名字
        try:
            username = driver.find_element(By.ID, 'h-name').text
            print(f"✅ 成功获取UP主: {username}")
        except:
            print(f"❌ 无法获取UP主名字，可能是页面没加载出来。")
            # 打印网页标题帮助调试
            print(f"当前网页标题: {driver.title}")
            return # 退出该UP主的抓取

        # 初始化 RSS
        fg = FeedGenerator()
        fg.id(url)
        fg.title(f'{username} 的 Bilibili 动态')
        fg.author({'name': username})
        fg.link(href=url, rel='alternate')
        fg.description(f'{username} 的最新视频更新')
        fg.language('zh-CN')

        # 查找视频
        # 尝试两种常见的 class，提高成功率
        videos = driver.find_elements(By.CSS_SELECTOR, '.small-item.fakeDanmu-item')
        if not videos:
             videos = driver.find_elements(By.CSS_SELECTOR, 'li.small-item')

        print(f"🔍 找到视频数量: {len(videos)}")

        if len(videos) == 0:
            print("⚠️ 警告: 视频列表为空，可能是B站改版或反爬拦截。")
            return

        for video in videos[:10]:
            try:
                title_element = video.find_element(By.CSS_SELECTOR, '.title')
                title = title_element.text
                video_url = video.find_element(By.TAG_NAME, 'a').get_attribute('href')
                
                # 封面图
                try:
                    cover = video.find_element(By.TAG_NAME, 'img').get_attribute('src')
                    if not cover.startswith('http'):
                        cover = 'https:' + cover
                except:
                    cover = ""

                # 时间
                try:
                    pub_time = video.find_element(By.CSS_SELECTOR, '.time').text
                except:
                    pub_time = "Recently"

                fe = fg.add_entry()
                fe.id(video_url)
                fe.title(title)
                fe.link(href=video_url)
                fe.description(f'<img src="{cover}"><br>发布时间: {pub_time}<br><a href="{video_url}">点击观看</a>')
                
            except Exception as e:
                continue

        # 只有确实抓到了视频才生成文件
        rss_file = os.path.join(OUTPUT_DIR, f'{uid}.xml')
        fg.rss_file(rss_file)
        print(f"🎉 成功生成文件: {rss_file}")

    except Exception as e:
        print(f"❌ 抓取过程发生未知错误: {e}")

# 读取 UID
# 增加容错：防止文件不存在
if not os.path.exists('ids.txt'):
    print("❌ 错误: 找不到 ids.txt 文件！请确保你创建了这个文件。")
else:
    with open('ids.txt', 'r') as f:
        uids = [line.strip() for line in f if line.strip()]

    print(f"📋 待抓取 UID 列表: {uids}")
    
    if not uids:
        print("❌ 错误: ids.txt 是空的！请填入 UP 主 UID。")

    for uid in uids:
        generate_rss(uid)

driver.quit()
