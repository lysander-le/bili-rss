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

# --- 浏览器配置 (伪装) ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# 伪装成 Mac 电脑，防止加载移动端页面
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def generate_rss(uid):
    url = f'https://space.bilibili.com/{uid}/video'
    print(f"--------------------------------------------------")
    print(f"🕵️ 正在抓取 UID: {uid}")
    
    try:
        driver.get(url)
        # 等待 15 秒，给页面充足时间加载
        time.sleep(15)
        
        # 1. 获取 UP 主名字
        try:
            username = driver.find_element(By.ID, 'h-name').text
            print(f"✅ UP主: {username}")
        except:
            username = f"UID_{uid}"
            print("⚠️ 没找到名字，使用 ID 代替")

        # 2. 初始化 RSS
        fg = FeedGenerator()
        fg.id(url)
        fg.title(f'{username} 的 Bilibili 动态')
        fg.link(href=url, rel='alternate')
        fg.description(f'{username} 的最新投稿视频')
        fg.language('zh-CN')

        # 3. 【核心修改】精准定位视频卡片
        # 不再抓取所有链接，而是先找到“卡片(li)”，再在卡片里分别找图和字
        video_cards = driver.find_elements(By.CSS_SELECTOR, '#submit-video-list ul.cube-list li.small-item')
        
        # 备用方案：如果改版了，尝试宽泛的选择器
        if not video_cards:
             video_cards = driver.find_elements(By.CSS_SELECTOR, 'li.small-item')

        print(f"🎬 找到视频卡片: {len(video_cards)} 个")

        count = 0
        for card in video_cards:
            if count >= 10: break # 只取前10个
            
            try:
                # --- A. 提取标题 (找 class="title" 的元素) ---
                try:
                    title_element = card.find_element(By.CSS_SELECTOR, 'a.title')
                    title = title_element.text
                    # 获取纯净链接，去掉问号后面的追踪参数
                    link = title_element.get_attribute('href').split('?')[0]
                except:
                    continue # 如果连标题都没找到，跳过这个

                # --- B. 提取封面图 (找 img 标签) ---
                try:
                    img_element = card.find_element(By.TAG_NAME, 'img')
                    cover_url = img_element.get_attribute('src')
                    if not cover_url.startswith('http'):
                        cover_url = 'https:' + cover_url
                    # 移除 @后缀 (B站有时会加缩略图后缀，去掉能拿原图)
                    cover_url = cover_url.split('@')[0]
                except:
                    cover_url = ""

                # --- C. 提取发布时间 ---
                try:
                    time_text = card.find_element(By.CSS_SELECTOR, 'span.time').text
                except:
                    time_text = ""

                # --- D. 生成 RSS 条目 ---
                fe = fg.add_entry()
                fe.id(link)
                fe.title(title) # 这里的 Title 绝对是纯文字标题
                fe.link(href=link)
                
                # 【关键】把图片放进描述里，Readwise 才能显示封面
                # HTML 排版：封面图 + 换行 + 标题 + 换行 + 观看链接
                desc_html = f"""
                <img src="{cover_url}" style="width:100%; max-width:600px;"><br>
                <h3>{title}</h3>
                <p>📅 发布时间: {time_text}</p>
                <p>🔗 <a href="{link}">点击在 Bilibili 观看</a></p>
                """
                fe.description(desc_html)
                fe.content(content=desc_html, type='CDATA') # 增强兼容性

                count += 1
                
            except Exception as e:
                print(f"⚠️ 解析单个视频出错: {e}")
                continue

        if count > 0:
            rss_file = os.path.join(OUTPUT_DIR, f'{uid}.xml')
            fg.rss_file(rss_file)
            print(f"🎉 成功生成完美版 XML: {rss_file}")
        else:
            print("⚠️ 未提取到视频，请检查页面加载情况。")

    except Exception as e:
        print(f"❌ 全局错误: {e}")

# 读取 UID
if os.path.exists('ids.txt'):
    with open('ids.txt', 'r') as f:
        uids = [line.strip() for line in f if line.strip()]
    for uid in uids:
        generate_rss(uid)
else:
    print("❌ ids.txt 不存在")

driver.quit()
