import os
import sys
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import re
from ip_pool import IPPool


# 全局变量
error_file_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'error.txt')
driver_path = None  # 将在main函数中初始化


def log_error(message):
    with open(error_file_path, 'a', encoding='utf-8') as f:
        f.write(message + '\n')


def clear_error_file():
    if os.path.exists(error_file_path):
        os.remove(error_file_path)


# 读取TXT文件中的驱动路径、截止日期和网址
def read_urls_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]
            if lines:
                driver_path_line = lines[0]
                start_date_line = lines[1]
                urls = lines[2:]

                # 提取驱动路径
                driver_path_match = re.match(r'driver_path\s*=\s*"(.+)"', driver_path_line)
                if driver_path_match:
                    driver_path = driver_path_match.group(1)
                else:
                    error_message = "Invalid driver path format."
                    log_error(error_message)
                    print(error_message)
                    return None, None, []

                # 提取截止日期
                start_date_match = re.match(r'start_date\s*=\s*(\d{4}\.\d{2}\.\d{2})', start_date_line)
                if start_date_match:
                    cutoff_date = datetime.strptime(start_date_match.group(1), '%Y.%m.%d')
                else:
                    error_message = "Invalid start date format."
                    log_error(error_message)
                    print(error_message)
                    return None, None, []

                return driver_path, cutoff_date, urls
            else:
                return None, None, []
    except Exception as e:
        error_message = f"Error reading file {file_path}: {e}"
        log_error(error_message)
        print(error_message)
        return None, None, []


# 初始化Selenium WebDriver
def init_driver(driver_path):
    try:
        options = Options()
        # 添加更多浏览器参数
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-web-security')  # 禁用同源策略
        options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
        
        # 添加实验性选项
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 使用IP池
        ip_pool = IPPool()
        if proxy := ip_pool.get_random_ip():
            options.add_argument(f'--proxy-server={proxy}')
            print(f"使用代理: {proxy}")
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        # 执行 JavaScript 来隐藏自动化特征
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        return driver
    except Exception as e:
        error_message = f"Error initializing driver with path {driver_path}: {e}"
        log_error(error_message)
        print(error_message)
        return None


# 请求网址获取内容
def fetch_url_with_selenium(driver, url, retries=3):
    global driver_path
    try:
        print(f"正在访问: {url}")
        driver.get(url)
        
        # 先等待页面加载完成
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # 等待一段随机时间
        time.sleep(random.uniform(3, 5))
        
        # 尝试多个可能的元素
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'publisher-page'))
            )
        except:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'content'))
                )
            except:
                print("警告: 未找到特定元素，但页面已加载")
        
        print("页面内容长度:", len(driver.page_source))
        return driver.page_source
    except Exception as e:
        if retries > 0:
            driver.quit()
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            
            if proxy := IPPool().get_random_ip():
                options.add_argument(f'--proxy-server={proxy}')
            
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            
            retry_message = f"Error fetching {url}. Retrying...{retries}"
            log_error(retry_message)
            print(retry_message)
            time.sleep(random.uniform(3, 6))
            return fetch_url_with_selenium(driver, url, retries - 1)
        else:
            error_message = f"Error fetching {url} with Selenium after retries: {e}"
            log_error(error_message)
            print(error_message)
            return None


# 提取单个游戏的信息
def extract_game_info(row, source_url, company_name):
    game_info = {}

    # 提取游戏名字和游戏网址
    game_name_tag = row.find('a', class_='g-app-name')
    game_info['name'] = game_name_tag.text.strip() if game_name_tag else 'N/A'
    game_info['url'] = game_name_tag['href'] if game_name_tag else 'N/A'

    # 添加完整的域名，如果URL是相对路径
    if game_name_tag and game_name_tag['href'].startswith('/'):
        game_info['url'] = 'https://appmagic.rocks' + game_name_tag['href']

    # 提取图像URL
    image_tag = row.find('img', class_='application-image')
    game_info['image_url'] = image_tag['src'] if image_tag and 'src' in image_tag.attrs else 'N/A'

    # 提取上线日期
    release_date_tag = row.find('span', class_='release-date')
    game_info['release_date'] = release_date_tag.text.strip() if release_date_tag else 'N/A'

    # 提取发布国家数
    countries_tag = row.find('span', attrs={'analyticsevent': 'publisher_page_show_countries_tooltip'})
    game_info['countries'] = countries_tag.text.strip() if countries_tag else 'N/A'

    # 添加公司名称
    game_info['company_name'] = company_name

    # 添加来源网站的信息
    game_info['source_url'] = source_url

    return game_info


# 提取所有游戏的信息
def extract_all_game_info(html, source_url):
    soup = BeautifulSoup(html, 'html.parser')

    # 提取公司名称
    company_name_tag = soup.find('div', class_='publisher-name')
    company_name = company_name_tag.text.strip() if company_name_tag else 'N/A'

    # 使用更宽松的选择器查找具有相关类的表格行
    game_rows = soup.select('publisher-app-row[class*="g-item"][class*="parent-app-info-hover"]')
    games = []

    print(f"Found {len(game_rows)} game rows")

    for row in game_rows:
        game_info = extract_game_info(row, source_url, company_name)
        games.append(game_info)

    return games


# 过滤和排序游戏信息
def filter_and_sort_games(games, cutoff_date):
    filtered_games = []

    for game in games:
        try:
            release_date = datetime.strptime(game['release_date'], '%d-%m-%Y')
            if release_date > cutoff_date:
                game['parsed_date'] = release_date
                filtered_games.append(game)
        except Exception as e:
            error_message = f"Error parsing date for game {game['name']}: {e}"
            log_error(error_message)
            print(error_message)

    # 按日期倒序排序
    filtered_games.sort(key=lambda x: x['parsed_date'], reverse=True)

    return filtered_games


# 生成新的HTML文件
def generate_html_file(games, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write('<html><head><title>数据分析</title></head><body>\n')
            file.write('<h1>数据分析</h1>\n')
            file.write('<table border="1">\n')
            file.write('<tr><th>图标</th><th>游戏名</th><th>发布日期</th><th>国家</th><th>所属公司</th></tr>\n')
            for game in games:
                file.write(
                    f"<tr><td><img src='{game['image_url']}' alt='Game Image' height='32px' width='32px'></td>\n"
                    f"<td><a href='{game['url']}'>{game['name']}</a></td>\n"
                    f"<td>{game['release_date']}</td>\n"
                    f"<td>{game['countries']}</td>\n"
                    f"<td><a href='{game['source_url']}'>{game['company_name']}</a></td></tr>\n"
                )
            file.write('</table>\n')
            file.write('</body></html>\n')
    except Exception as e:
        error_message = f"Error writing to file {output_file}: {e}"
        log_error(error_message)
        print(error_message)


def main():
    # 清理旧的错误文件
    clear_error_file()

    # 获取当前脚本目录
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    file_path = os.path.join(base_dir, 'urls.txt')  # 包含驱动路径、截止日期和网址的txt文件路径
    output_file = os.path.join(base_dir, 'FindGame.html')  # 生成的HTML文件路径

    driver_path, cutoff_date, urls = read_urls_from_file(file_path)
    if driver_path is None or cutoff_date is None:
        print(f"Invalid input file format. Please ensure the file starts with driver path and cutoff date in the correct format.")
        return

    driver = init_driver(driver_path)
    if not driver:
        print(f"Failed to initialize web driver.")
        return

    games = []
    try:
        for i, url in enumerate(urls):
            html = fetch_url_with_selenium(driver, url)
            if html:
                game_info_list = extract_all_game_info(html, url)
                games.extend(game_info_list)
                print(f"Processed {i + 1}/{len(urls)}: {url}")  # 显示进度
    finally:
        driver.quit()

    filtered_and_sorted_games = filter_and_sort_games(games, cutoff_date)
    generate_html_file(filtered_and_sorted_games, output_file)
    print(f"Generated HTML file: {output_file}")

    # 检查错误文件是否存在，如果没有错误，删除该文件
    if not os.path.exists(error_file_path) or os.stat(error_file_path).st_size == 0:
        clear_error_file()


if __name__ == '__main__':
    main()