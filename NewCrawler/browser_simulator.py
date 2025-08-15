import webbrowser
import time
import pyautogui
import pyperclip
import pygetwindow as gw

class BrowserSimulator:
    def __init__(self, chrome_path=None):
        # 如果没有提供路径，使用默认路径
        self.chrome_path = chrome_path or r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        webbrowser.register('chrome', None, 
            webbrowser.BackgroundBrowser(self.chrome_path))
    
    def open_url(self, url, max_retries=5):
        """打开URL并获取页面内容"""
        # 启动Chrome
        webbrowser.get('chrome').open('about:blank')
        time.sleep(2)
        
        # 找到并激活Chrome窗口
        chrome_window = gw.getWindowsWithTitle('Chrome')[0]
        chrome_window.activate()
        
        # 访问URL
        pyautogui.hotkey('ctrl', 'l')  # 选中地址栏
        time.sleep(0.5)
        pyperclip.copy(url)  # 复制URL到剪贴板
        pyautogui.hotkey('ctrl', 'v')  # 粘贴URL
        time.sleep(0.5)
        pyautogui.press('enter')  # 访问URL
        
        # 循环检查页面是否加载完成
        for attempt in range(max_retries):
            time.sleep(1)  # 等待基本加载时间
            
            # 获取页面内容
            pyautogui.press('f12')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'shift', 'p')
            time.sleep(0.5)
            pyperclip.copy("显示元素")
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(0.5)
            pyautogui.press('home')
            time.sleep(0.5)
            pyautogui.press('down')
            time.sleep(0.5)
            pyautogui.press('f2')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            # 检查内容
            content = pyperclip.paste()
            if 'publisher-name' in content and 'publisher-app-row' in content:
                print(f"页面加载完成，尝试次数: {attempt + 1}")
                pyautogui.press('f12')  # 关闭开发者工具
                return content
                
            print(f"页面未完全加载，重试中... ({attempt + 1}/{max_retries})")
            pyautogui.press('f12')  # 关闭开发者工具
            time.sleep(1)
        
        raise Exception(f"页面加载失败，已重试 {max_retries} 次")

if __name__ == "__main__":
    browser = BrowserSimulator()
    content = browser.open_url("https://www.baidu.com")
    print("获取到的内容长度:", len(content))
    
    with open('baidu.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("内容已保存到 baidu.html") 