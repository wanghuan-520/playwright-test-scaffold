# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Service Health Checker
# ═══════════════════════════════════════════════════════════════
"""
服务健康检查器 - 测试前检查服务是否可用
"""

import time
import urllib.request
import urllib.error
import ssl
from typing import Dict, Tuple
from utils.config import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class ServiceChecker:
    """
    服务健康检查器
    
    使用方式:
        checker = ServiceChecker()
        
        # 检查单个服务
        is_ok, msg = checker.check_service("frontend")
        
        # 检查所有服务
        results = checker.check_all_services()
        
        # 等待服务启动
        checker.wait_for_service("frontend")
    """
    
    def __init__(self):
        self.config = ConfigManager()
        self.health_config = self.config.get_health_check_config()
    
    def check_service(self, name: str) -> Tuple[bool, str]:
        """
        检查单个服务是否可用
        
        Args:
            name: 服务名称 (frontend/backend)
            
        Returns:
            Tuple[bool, str]: (是否可用, 消息)
        """
        url = self.config.get_health_check_url(name)
        if not url:
            return False, f"服务 {name} 未配置 URL"
        
        timeout = self.health_config.get("timeout", 10)
        
        try:
            # 忽略 SSL 证书验证（本地开发环境）
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            request = urllib.request.Request(url, method='GET')
            request.add_header('User-Agent', 'ServiceChecker/1.0')
            
            with urllib.request.urlopen(request, timeout=timeout, context=ctx) as response:
                status = response.getcode()
                if 200 <= status < 400:
                    return True, f"✅ {name}: {url} (HTTP {status})"
                else:
                    return False, f"❌ {name}: {url} (HTTP {status})"
                    
        except urllib.error.HTTPError as e:
            # 即使返回 4xx/5xx，服务也算是在运行
            if e.code < 500:
                return True, f"✅ {name}: {url} (HTTP {e.code})"
            return False, f"❌ {name}: {url} (HTTP {e.code})"
            
        except urllib.error.URLError as e:
            return False, f"❌ {name}: {url} (连接失败: {e.reason})"
            
        except Exception as e:
            return False, f"❌ {name}: {url} (错误: {str(e)})"
    
    def check_all_services(self) -> Dict[str, Tuple[bool, str]]:
        """
        检查所有配置的服务
        
        Returns:
            Dict[str, Tuple[bool, str]]: 服务名 -> (是否可用, 消息)
        """
        services = self.config.get_all_services()
        results = {}
        
        for name in services.keys():
            results[name] = self.check_service(name)
        
        return results
    
    def wait_for_service(self, name: str, timeout: int = None) -> bool:
        """
        等待服务启动
        
        Args:
            name: 服务名称
            timeout: 超时时间（秒），默认使用配置值
            
        Returns:
            bool: 服务是否可用
        """
        if timeout is None:
            timeout = self.health_config.get("timeout", 10)
        
        retry_count = self.health_config.get("retry_count", 3)
        retry_interval = self.health_config.get("retry_interval", 2)
        
        url = self.config.get_service_url(name)
        logger.info(f"等待服务 {name} 启动: {url}")
        
        for i in range(retry_count):
            is_ok, msg = self.check_service(name)
            if is_ok:
                logger.info(msg)
                return True
            
            if i < retry_count - 1:
                logger.info(f"重试 {i + 1}/{retry_count}，等待 {retry_interval} 秒...")
                time.sleep(retry_interval)
        
        logger.error(f"服务 {name} 启动超时")
        return False
    
    def wait_for_all_services(self) -> bool:
        """
        等待所有服务启动
        
        Returns:
            bool: 所有服务是否都可用
        """
        services = self.config.get_all_services()
        all_ok = True
        
        for name in services.keys():
            if not self.wait_for_service(name):
                all_ok = False
        
        return all_ok
    
    def get_status_report(self) -> str:
        """
        获取服务状态报告（格式化输出）
        
        Returns:
            str: 格式化的状态报告
        """
        results = self.check_all_services()
        
        if not results:
            return "⚠️ 未配置任何服务"
        
        lines = ["", "═" * 50, "服务状态检查", "═" * 50]
        
        all_ok = True
        for name, (is_ok, msg) in results.items():
            lines.append(msg)
            if not is_ok:
                all_ok = False
        
        lines.append("═" * 50)
        
        if all_ok:
            lines.append("✅ 所有服务正常运行")
        else:
            lines.append("❌ 部分服务不可用，请先启动服务")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def is_enabled(self) -> bool:
        """检查健康检查是否启用"""
        return self.health_config.get("enabled", True)


def check_services_before_test() -> bool:
    """
    测试前检查服务（便捷函数）
    
    Returns:
        bool: 是否可以继续测试
    """
    checker = ServiceChecker()
    
    if not checker.is_enabled():
        logger.info("服务健康检查已禁用")
        return True
    
    report = checker.get_status_report()
    print(report)
    
    results = checker.check_all_services()
    return all(is_ok for is_ok, _ in results.values())

