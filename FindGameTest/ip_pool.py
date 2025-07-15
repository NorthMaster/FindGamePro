import random
import requests
import time
from typing import List, Optional

class IPPool:
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.ip_list: List[str] = []
        self.current_ip: Optional[str] = None
        self.test_url = "https://www.baidu.com"
        self.proxy_file = proxy_file
        self._load_proxies()
    
    def _load_proxies(self) -> None:
        """从文件加载代理IP"""
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                proxies = [line.strip() for line in f if line.strip()]
                self.add_ips(proxies)
        except FileNotFoundError:
            print(f"代理IP文件 {self.proxy_file} 不存在")
    
    def add_ip(self, ip: str) -> None:
        """添加单个IP到池中"""
        if self._test_ip(ip):
            self.ip_list.append(ip)
    
    def add_ips(self, ips: List[str]) -> None:
        """批量添加IP到池中"""
        for ip in ips:
            self.add_ip(ip)
    
    def get_random_ip(self) -> Optional[str]:
        """随机获取一个IP"""
        if not self.ip_list:
            return None
        self.current_ip = random.choice(self.ip_list)
        return self.current_ip
    
    def remove_current_ip(self) -> None:
        """从池中移除当前IP"""
        if self.current_ip and self.current_ip in self.ip_list:
            self.ip_list.remove(self.current_ip)
            self.current_ip = None
    
    def _test_ip(self, ip: str) -> bool:
        """测试IP是否可用"""
        try:
            print(f"正在测试IP: {ip}")
            proxies = {
                "http": f"http://{ip}",
                "https": f"http://{ip}"
            }
            # 只测试百度
            response = requests.get(
                "https://www.baidu.com", 
                proxies=proxies, 
                timeout=5,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
                }
            )
            success = response.status_code == 200
            print(f"测试结果: {'成功' if success else '失败'} (状态码: {response.status_code})")
            return success
        except Exception as e:
            print(f"测试出错: {str(e)}")
            return False

if __name__ == "__main__":
    print("开始测试IP池...")
    # 创建实例后再访问 proxy_file
    pool = IPPool()
    print(f"当前代理文件: {pool.proxy_file}")
    
    # 读取所有IP
    print("\n从文件读取的IP:")
    with open("proxies.txt", 'r', encoding='utf-8') as f:
        ips = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        for ip in ips:
            print(f"- {ip}")
    
    # 打印可用的IP列表
    print("\n测试后可用的IP列表:")
    for ip in pool.ip_list:
        print(f"- {ip}") 