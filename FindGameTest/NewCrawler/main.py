import os
import time
import re
from bs4 import BeautifulSoup
from browser_simulator import BrowserSimulator
from datetime import datetime
import sys
import pygetwindow as gw

def read_config():
    """读取配置文件"""
    config = {
        'chrome_path': '',
        'start_date': '',
        'urls': []
    }
    
    # 获取可执行文件所在目录
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    config_path = os.path.join(base_path, 'config', 'urls.txt')
    1
    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            # 移除行首行尾的空白字符（包括空格、制表符、换行符）
            line = line.strip()
            if not line:  # 跳过空行
                continue
            
            # 处理配置项
            if line.startswith('chrome_path='):
                # 提取等号后的内容并清理空白字符
                config['chrome_path'] = line.split('=', 1)[1].strip()
            elif line.startswith('start_date='):
                config['start_date'] = line.split('=', 1)[1].strip()
            else:
                # 清理URL并添加到列表
                url = line.strip()
                if url:  # 确保URL不是空字符串
                    config['urls'].append(url)
    
    return config

def extract_game_info(row, source_url, company_name):
    """提取单个游戏的信息"""
    game_info = {}

    # 提取游戏名字和游戏网址
    game_name_tag = row.find('a', class_='g-app-name')
    game_info['name'] = game_name_tag.text.strip() if game_name_tag else 'N/A'
    game_info['url'] = game_name_tag['href'] if game_name_tag else 'N/A'

    # 添加完整的域名，如果URL是相对路径
    if game_name_tag and game_name_tag['href'].startswith('/'):
        game_info['url'] = 'https://appmagic.rocks' + game_name_tag['href']

    # 提取上线日期
    release_date_tag = row.find('app-release-date').find('span', class_='release-date').find('span') if row.find('app-release-date') else None
    game_info['release_date'] = release_date_tag.text.strip() if release_date_tag else 'N/A'

    # 提取发布国家数
    countries_tag = row.find('span', attrs={'analyticsevent': 'publisher_page_show_countries_tooltip'})
    game_info['countries'] = countries_tag.text.strip() if countries_tag else 'N/A'

    # 添加公司名称
    game_info['company_name'] = company_name

    # 添加来源网站的信息
    game_info['source_url'] = source_url

    return game_info

def extract_all_game_info(html, source_url):
    """提取所有游戏的信息"""
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

def filter_and_sort_games(games, cutoff_date):
    """过滤和排序游戏信息"""
    filtered_games = []
    cutoff_date = datetime.strptime(cutoff_date, '%Y.%m.%d')

    for game in games:
        try:
            # 跳过无效的日期
            if game['release_date'] == 'N/A' or not game['release_date']:
                continue
                
            release_date = datetime.strptime(game['release_date'], '%Y-%m-%d')
            if release_date > cutoff_date:
                game['parsed_date'] = release_date
                filtered_games.append(game)
        except Exception as e:
            print(f"Error parsing date for game {game['name']}: {e}")
            continue

    # 按日期倒序排序
    filtered_games.sort(key=lambda x: x['parsed_date'], reverse=True)
    return filtered_games

def generate_html_file(games, output_file):
    """生成新的HTML文件"""
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write('<html><head><title>数据分析</title></head><body>\n')
        file.write('<h1>数据分析</h1>\n')
        file.write('<table border="1">\n')
        file.write('<tr><th>游戏名</th><th>发布日期</th><th>国家</th><th>所属公司</th></tr>\n')
        for game in games:
            file.write(
                f"<tr><td><a href='{game['url']}'>{game['name']}</a></td>\n"
                f"<td>{game['release_date']}</td>\n"
                f"<td>{game['countries']}</td>\n"
                f"<td><a href='{game['source_url']}'>{game['company_name']}</a></td></tr>\n"
            )
        file.write('</table>\n')
        file.write('</body></html>\n')

def get_next_file_index(result_dir, date_str):
    """获取下一个文件索引"""
    # 查找当前日期的所有文件
    pattern = f'FindGame_{date_str}_*.html'
    existing_files = [f for f in os.listdir(result_dir) if f.startswith(f'FindGame_{date_str}_') and f.endswith('.html')]
    
    if not existing_files:
        return 1
        
    # 提取所有索引
    indices = []
    for file in existing_files:
        try:
            index = int(file.split('_')[-1].replace('.html', ''))
            indices.append(index)
        except ValueError:
            continue
    
    # 返回最大索引+1
    return max(indices) + 1 if indices else 1

def combine_html_files(result_dir, start_date):
    """合并HTML文件并按开始日期筛选"""
    all_games = {}  # 使用字典来存储游戏，以游戏名和发布日期作为键
    
    # 遍历所有HTML文件
    for file in os.listdir(result_dir):
        if file.startswith('FindGame_') and file.endswith('.html'):
            file_path = os.path.join(result_dir, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # 提取表格行
            rows = soup.select('table tr')[1:]  # 跳过表头
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    game_info = {
                        'name': cols[0].text.strip(),
                        'url': cols[0].find('a')['href'] if cols[0].find('a') else '',
                        'release_date': cols[1].text.strip(),
                        'countries': cols[2].text.strip(),
                        'company_name': cols[3].text.strip(),
                        'source_url': cols[3].find('a')['href'] if cols[3].find('a') else ''
                    }
                    # 使用游戏名和发布日期组合作为唯一标识
                    game_key = f"{game_info['name']}_{game_info['release_date']}"
                    all_games[game_key] = game_info
    
    # 过滤和排序
    filtered_games = []
    start_date = datetime.strptime(start_date, '%Y.%m.%d')
    
    # 处理去重后的游戏列表
    for game in all_games.values():
        try:
            release_date = datetime.strptime(game['release_date'], '%Y-%m-%d')
            if release_date >= start_date:
                game['parsed_date'] = release_date
                filtered_games.append(game)
        except Exception as e:
            print(f"Error parsing date for game {game['name']}: {e}")
            continue
    
    # 按日期倒序排序
    filtered_games.sort(key=lambda x: x['parsed_date'], reverse=True)
    
    # 生成合并后的文件
    output_file = os.path.join(result_dir, f'FindGame_Combine_{start_date.strftime("%Y.%m.%d")}.html')
    generate_html_file(filtered_games, output_file)
    
    # 打印统计信息
    print(f"\n统计信息:")
    print(f"总游戏数: {len(all_games)}")
    print(f"筛选后游戏数: {len(filtered_games)}")
    
    return output_file

def open_html_file(file_path):
    """打开HTML文件"""
    try:
        import webbrowser
        webbrowser.open(file_path)
    except Exception as e:
        print(f"打开文件失败: {str(e)}")

def main():
    try:
        # 获取当前命令行窗口的标题
        current_window = None
        try:
            # 尝试获取命令行窗口（可能是"AppMagicCrawler"或"Python"）
            current_window = gw.getWindowsWithTitle('AppMagicCrawler')[0]
        except IndexError:
            try:
                current_window = gw.getWindowsWithTitle('Python')[0]
            except IndexError:
                pass
        
        # 获取可执行文件所在目录
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        print("请选择操作：")
        print("1. 抓取新数据")
        print("2. 合并历史数据")
        choice = input("请输入选项（1或2）：").strip()
        
        if choice == "1":
            # 原有的抓取逻辑
            config = read_config()
            browser = BrowserSimulator(chrome_path=config['chrome_path'])
            
            games = []
            for url in config['urls']:
                try:
                    print(f'正在处理: {url}')
                    content = browser.open_url(url)
                    game_info_list = extract_all_game_info(content, url)
                    games.extend(game_info_list)
                    time.sleep(2)
                except Exception as e:
                    print(f'处理 {url} 时出错: {str(e)}')
                    continue
            
            filtered_games = filter_and_sort_games(games, config['start_date'])
            
            result_dir = os.path.join(base_path, 'result')
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)
            
            current_date = datetime.now().strftime('%Y-%m-%d')
            next_index = get_next_file_index(result_dir, current_date)
            output_file = os.path.join(result_dir, f'FindGame_{current_date}_{next_index}.html')
            
            generate_html_file(filtered_games, output_file)
            print(f'已生成分析结果: {output_file}')
            
            # 打开结果文件
            open_html_file(output_file)
            
            # 重新激活命令行窗口
            if current_window:
                current_window.activate()
            
        elif choice == "2":
            date_str = input("请输入开始日期（格式：2024.01.01）：").strip()  # 修改提示文本
            try:
                # 验证日期格式
                datetime.strptime(date_str, '%Y.%m.%d')
                
                result_dir = os.path.join(base_path, 'result')
                if not os.path.exists(result_dir):
                    raise Exception("没有找到历史数据文件夹")
                
                output_file = combine_html_files(result_dir, date_str)
                print(f'已生成合并结果: {output_file}')
                
                # 打开结果文件
                open_html_file(output_file)
                
                # 重新激活命令行窗口
                if current_window:
                    current_window.activate()
                
            except ValueError:
                raise Exception("日期格式错误，请使用正确的格式：2024.01.01")
        else:
            raise Exception("无效的选项，请输入1或2")
        
        print('\n处理完成! 按任意键退出...')
        
    except Exception as e:
        print(f'\n发生错误: {str(e)}')
        print('按任意键退出...')
        # 发生错误时也重新激活窗口
        if current_window:
            current_window.activate()
    finally:
        try:
            import msvcrt
            msvcrt.getch()
        except ImportError:
            input()

if __name__ == '__main__':
    main() 