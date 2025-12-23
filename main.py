import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator

# --- 配置区 ---
OUTPUT_DIR = 'output'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 记录日志的函数
def log_message(msg):
    print(msg)
    with open(os.path.join(OUTPUT_DIR, 'debug_log.txt'), 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

# 初始化日志
if os.path.exists(os.path.join(OUTPUT_DIR, 'debug_log.txt')):
    os.remove(os.path.join(OUTPUT_DIR, 'debug_log.txt'))
log_message("🚀 脚本开始运行...")

# --- 核心：最强伪装配置 ---
chrome_options = Options()
chrome_options.add_argument("--headless") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# 禁用自动化栏
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
# 伪装 User-Agent
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 移除 navigator.webdriver 特征
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
    Object.defineProperty(navigator, 'webdriver', {
      get: () => undefined
    })
  """
})

def generate_rss(uid):
    url = f'https://space.bilibili.com/{uid}/video'
    log_message(f"--------------------------------")
    log_message(f"🕵️ 正在抓取 UID: {uid}")
    
    try:
        driver.get(url)
        time.sleep(5) # 等待加载
        
        # 调试：打印一下网页标题，看看是不是被拦截了
        page_title = driver.title
        log_message(f"📄 网页标题: {page_title}")

        # 尝试获取 UP 主名字
        try:
            username = driver.find_element(By.ID, 'h-name').text
            log_message(f"✅ 识别到UP主: {username}")
        except:
            log_message("⚠️ 无法找到UP主名字，尝试备用选择器...")
            try:
                username = driver.find_element(By.CSS_SELECTOR, '.h-name').text
            except:
                username = f"UID_{uid}"
                log_message("❌ 彻底无法获取名字，使用默认 ID")

        # 初始化 RSS
        fg = FeedGenerator()
        fg.id(url)
        fg.title(f'{username} 的 Bilibili 动态')
        fg.link(href=url, rel='alternate')
        fg.description(f'{username} 的最新视频')
        fg.language('zh-CN')

        # 查找视频
        videos = driver.find_elements(By.CSS_SELECTOR, '.small-item.fakeDanmu-item')
        # 备用选择器
        if not videos:
             videos = driver.find_elements(By.CSS_SELECTOR, 'li.small-item')
        
        log_message(f"🎬 找到视频数量: {len(videos)}")

        if len(videos) == 0:
            log_message("⚠️ 警告: 0 个视频。可能是被 B 站拦截，或者页面结构改变。")
            # 打印一点源码看看发生了什么
            log_message(f"网页源码片段: {driver.page_source[:500]}")
            return

        for video in videos[:10]:
            try:
                title_element = video.find_element(By.CSS_SELECTOR, '.title')
                title = title_element.text
                video_url = video.find_element(By.TAG_NAME, 'a').get_attribute('href')
                
                try:
                    pub_time = video.find_element(By.CSS_SELECTOR, '.time').text
                except:
                    pub_time = "Recent"

                fe = fg.add_entry()
                fe.id(video_url)
                fe.title(title)
                fe.link(href=video_url)
                fe.description(f'发布时间: {pub_time}<br><a href="{video_url}">点击观看</a>')
                
            except Exception as e:
                continue

        rss_file = os.path.join(OUTPUT_DIR, f'{uid}.xml')
        fg.rss_file(rss_file)
        log_message(f"🎉 成功生成 RSS: {rss_file}")

    except Exception as e:
        log_message(f"❌ 抓取过程报错: {str(e)}")

# 读取 UID
id_file = 'ids.txt'
if not os.path.exists(id_file):
    log_message("❌ 致命错误: ids.txt 不存在！")
else:
    with open(id_file, 'r') as f:
        uids = [line.strip() for line in f if line.strip()]
    
    if not uids:
        log_message("❌ ids.txt 是空的！请检查文件内容。")
    
    for uid in uids:
        generate_rss(uid)

driver.quit()
