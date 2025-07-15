from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Browser:
    def __init__(self, chrome_path):
        self.chrome_path = chrome_path
        self.driver = None
    
    def start(self):
        """启动浏览器"""
        service = Service(self.chrome_path)
        self.driver = webdriver.Chrome(service=service)
        
    def visit(self, url):
        """访问网页"""
        self.driver.get(url)
        # 等待页面加载
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        ) 