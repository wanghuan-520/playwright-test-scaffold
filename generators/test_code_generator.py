# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Code Generator (Coordinator)
# ═══════════════════════════════════════════════════════════════
"""
测试代码生成器 - 协调器
统一协调 Page Object、测试用例、测试数据的生成
"""

from typing import Dict
from pathlib import Path
import json

from generators.page_analyzer import PageInfo
from generators.page_object_generator import PageObjectGenerator
from generators.test_case_generator import TestCaseGenerator
from generators.test_data_generator import TestDataGenerator
from generators.utils import get_file_name_from_url
from utils.logger import get_logger

logger = get_logger(__name__)


class TestCodeGenerator:
    """
    测试代码生成器 - 协调器
    
    使用方式:
        generator = TestCodeGenerator()
        generator.generate_all(page_info, output_dir=".")
    """
    
    def __init__(self):
        """初始化各个子生成器"""
        self.page_object_gen = PageObjectGenerator()
        self.test_case_gen = TestCaseGenerator()
        self.test_data_gen = TestDataGenerator()
    
    def generate_all(self, page_info: PageInfo, output_dir: str = ".") -> Dict[str, str]:
        """生成所有文件"""
        output = Path(output_dir)
        files = {}
        file_name = get_file_name_from_url(page_info.url)
        
        # Page Object
        page_code = self.page_object_gen.generate_page_object(page_info)
        page_file = output / "pages" / f"{file_name}_page.py"
        self._save(page_file, page_code)
        files["page_object"] = str(page_file)
        
        # Test Cases
        test_code = self.test_case_gen.generate_test_cases(page_info)
        test_file = output / "tests" / f"test_{file_name}.py"
        self._save(test_file, test_code)
        files["test_cases"] = str(test_file)
        
        # Test Data
        test_data = self.test_data_gen.generate_test_data(page_info)
        data_file = output / "test-data" / f"{file_name}_data.json"
        self._save(data_file, json.dumps(test_data, indent=2, ensure_ascii=False))
        files["test_data"] = str(data_file)
        
        logger.info(f"代码生成完成: {len(files)} 个文件")
        return files
    
    def _save(self, file_path: Path, content: str) -> None:
        """保存文件"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"已保存: {file_path}")
