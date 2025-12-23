import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator

# --- 配置 ---
OUTPUT_DIR = 'output'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- 浏览器伪装 ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# 模拟普通 Mac 电脑访问
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def generate_rss(uid):
    url = f'https://space.bilibili.com/{uid}/video'
    print(f"🕵️ 正在抓取 UID: {uid}")
    
    try:
        driver.get(url)
        time.sleep(5) # 等待加载
        
        # 1. 获取 UP 主名字 (尝试多种位置)
        try:
            username = driver.find_element(By.ID, 'h-name').text
        except:
            try:
                username = driver.find_element(By.XPATH, '//*[@id="h-name"]').text
            except:
                username = f"UID_{uid}"
                print("⚠️ 没找到名字，使用 ID 代替")

        print(f"✅ UP主: {username}")

        # 2. 初始化 RSS
        fg = FeedGenerator()
        fg.id(url)
        fg.title(f'{username} 的 Bilibili 动态')
        fg.link(href=url, rel='alternate')
        fg.description(f'{username} 的最新视频')
        fg.language('zh-CN')

        # 3. 万能视频查找 (查找所有包含 video/BV 的链接)
        # B站视频链接通常是 https://www.bilibili.com/video/BVxxxxx
        video_elements = driver.find_elements(By.XPATH, '//a[contains(@href, "/video/BV")]')
        
        # 去重 (因为有时候图片和标题都是链接，会重复)
        seen_links = set()
        count = 0

        for video in video_elements:
            if count >= 10: break # 只取前10个
            
            try:
                video_url = video.get_attribute('href')
                
                # 过滤掉非视频链接或重复链接
                if video_url in seen_links or 'javascript' in video_url:
                    continue
                
                # 尝试获取标题
                try:
                    # 只要链接里面包含文本，就认为是标题
                    title = video.text
                    if not title: # 如果链接没文字，可能是图片包裹的链接
                        # 尝试找同级的 title 元素
                        # 这里不做太复杂，如果没标题就跳过
                        continue 
                except:
                    title = "New Video"

                seen_links.add(video_url)
                count += 1

                fe = fg.add_entry()
                fe.id(video_url)
                fe.title(title)
                fe.link(href=video_url)
                fe.description(f'<a href="{video_url}">点击观看: {title}</a>')
                
            except Exception as e:
                continue

        print(f"🎬 成功提取 {count} 个视频")

        # 只有提取到了才生成文件
        if count > 0:
            rss_file = os.path.join(OUTPUT_DIR, f'{uid}.xml')
            fg.rss_file(rss_file)
            print(f"🎉 生成 XML: {rss_file}")
        else:
            print("⚠️ 未找到有效视频链接")

    except Exception as e:
        print(f"❌ 错误: {e}")

# 读取 UID
if os.path.exists('ids.txt'):
    with open('ids.txt', 'r') as f:
        uids = [line.strip() for line in f if line.strip()]
    for uid in uids:
        generate_rss(uid)
else:
    print("❌ ids.txt 不存在")

driver.quit()
