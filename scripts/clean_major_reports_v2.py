#!/usr/bin/env python3
"""
专业评估报告完整提取脚本 v2
策略：保留原始 markdown 文本 + 提取结构化关键字段
"""

import re
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class MajorReportParser:
    """专业报告完整解析器"""

    def __init__(self):
        self.markers_to_remove = ['[待核实]', '[需更新]', '[数据收集完成]', '所有研究均已完成。现在正在编制', '所有研究均已完成']

    def clean_text(self, text: str) -> str:
        """清理文本中的特殊标记"""
        if not text:
            return ""
        for marker in self.markers_to_remove:
            text = text.replace(marker, '')
        # 清理多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def parse_code_and_name(self, filename: str) -> tuple:
        """从文件名解析专业代码和名称"""
        stem = Path(filename).stem
        match = re.match(r'(\d{6}[TK]?)_(.+)', stem)
        if match:
            return match.group(1), match.group(2)
        return None, stem

    def extract_module_content(self, content: str, module_title: str) -> str:
        """提取指定模块的原始内容"""
        # 移除标题中的括号部分进行匹配
        base_title = re.sub(r'[（(].*?[）)]', '', module_title)
        # 使用简单的正则：匹配从标题到下一个"## 模块"或文件结尾
        pattern = rf'## {re.escape(base_title)}[^\n]*\s*\n(.*?)(?=## 模块|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return self.clean_text(match.group(1))
        return ""

    def parse_all_modules(self, content: str) -> Dict[str, str]:
        """提取所有9个模块的原始内容"""
        modules = {}
        module_list = [
            '模块一：专业画像与总评',
            '模块二：六维量化评估',
            '模块三：院校分档与定位',
            '模块四：横向对决台',
            '模块五：职业路径图',
            '模块六：反差与揭秘趣味卡片',
            '模块七：专业气质人格标签',
            '模块八：原始数据支撑'
        ]

        for module in module_list:
            raw_content = self.extract_module_content(content, module)
            if raw_content:
                key = module.replace('模块', 'module').replace('：', '_').replace(' ', '_').lower()
                # 简化键名
                key_map = {
                    '模块一：专业画像与总评': 'module1_image',
                    '模块二：六维量化评估': 'module2_six_dimensions',
                    '模块三：院校分档与定位': 'module3_university_tiers',
                    '模块四：横向对决台': 'module4_comparison',
                    '模块五：职业路径图': 'module5_career_paths',
                    '模块六：反差与揭秘趣味卡片': 'module6_fun_cards',
                    '模块七：专业气质人格标签': 'module7_personality_tags',
                    '模块八：原始数据支撑': 'module8_raw_data'
                }
                key = key_map.get(module, key)
                modules[key] = {
                    'title': module,
                    'raw_content': raw_content
                }

        return modules

    def parse_radar_table(self, content: str) -> Dict:
        """解析六维雷达图表"""
        radar = {}
        dimension_map = {
            '市场回报': 'market_return',
            '产业景气': 'industry_outlook',
            '未来适应': 'future_adaptability',
            '发展路径': 'career_path',
            '教育资源': 'education_resources',
            '学科内核': 'discipline_core'
        }
        pattern = r'\|\s*([^|\n]+?)\s*\|\s*([\d.]+)\s*\|\s*[^|]+?\|\s*([\d.]+)\s*\|'
        for match in re.finditer(pattern, content):
            dimension, score, weighted = match.groups()
            dimension_clean = dimension.strip()
            if dimension_clean in dimension_map:
                try:
                    radar[dimension_map[dimension_clean]] = float(score)
                except ValueError:
                    continue
        return radar

    def parse_ai_summary(self, content: str) -> str:
        """解析 AI 总评"""
        match = re.search(r'### 1\.1 AI 总评.*?\n>(.*?)\n', content, re.DOTALL)
        if match:
            return self.clean_text(match.group(1))
        # 备用模式
        match = re.search(r'>(.*?)\n', content)
        if match:
            return self.clean_text(match.group(1))
        return ""

    def parse_recommendation_level(self, content: str) -> str:
        """解析推荐等级"""
        if '🟢 **绿灯推荐**' in content or '绿灯推荐' in content:
            return 'green'
        elif '🟡 **黄灯推荐**' in content or '黄灯推荐' in content:
            return 'yellow'
        elif '🔴 **红灯推荐**' in content or '红灯推荐' in content:
            return 'red'
        # 根据加权总分判断
        weighted = self.parse_weighted_score(content)
        if weighted >= 4.0:
            return 'green'
        elif weighted >= 3.0:
            return 'yellow'
        return 'red'

    def parse_weighted_score(self, content: str) -> float:
        """解析加权总分"""
        match = re.search(r'\*\*加权总分\*\*.*?\|\s*\*\*[^|]*\*\*\s*\|\s*\*\*([\d.]+)\*\*\s*\|', content)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return 0.0

    def parse_category(self, code: str) -> str:
        """根据专业代码推断学科门类"""
        if not code or len(code) < 2:
            return '未知'
        category_map = {
            '01': '哲学', '02': '经济学', '03': '法学', '04': '教育学',
            '05': '文学', '06': '历史学', '07': '理学', '08': '工学',
            '09': '农学', '10': '医学', '11': '军事学', '12': '管理学',
            '13': '艺术学', '14': '交叉学科'
        }
        return category_map.get(code[:2], '未知')

    def extract_tables(self, content: str) -> list:
        """提取所有表格数据"""
        tables = []
        table_pattern = r'(\|[^\n]+\|[^\n]*\n)+'
        for match in re.finditer(table_pattern, content):
            table_text = match.group(0)
            rows = []
            for line in table_text.strip().split('\n'):
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if cells:
                    rows.append(cells)
            if len(rows) >= 2:
                tables.append(rows)
        return tables

    def parse_full_report(self, filepath: str) -> Dict[str, Any]:
        """解析完整报告文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        code, name = self.parse_code_and_name(filepath)

        # 提取所有模块的原始内容
        module1_raw = self.extract_module_content(content, '模块一：专业画像与总评')
        module2_raw = self.extract_module_content(content, '模块二：六维量化评估')

        # 构建结构化数据
        result = {
            'meta': {
                'version': '2.0.0',
                'generated_at': datetime.now().isoformat(),
                'updated_at': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                'source_file': Path(filepath).name,
                'data_sources': ['麦可思就业报告', '教育部数据', '各高校就业质量报告']
            },
            'layer1_overview': {
                'code': code,
                'name': name,
                'category': self.parse_category(code),
                'recommendation_level': self.parse_recommendation_level(module1_raw),
                'summary': self.parse_ai_summary(module1_raw),
                'radar': self.parse_radar_table(module1_raw),
                'weighted_score': self.parse_weighted_score(module1_raw)
            },
            'layer2_core': {
                'summary': self.parse_ai_summary(module1_raw),
                'recommendation_level': self.parse_recommendation_level(module1_raw)
            },
            'layer3_detail': {
                'module1_image': {
                    'title': '模块一：专业画像与总评',
                    'raw_content': module1_raw
                },
                'module2_six_dimensions': {
                    'title': '模块二：六维量化评估',
                    'raw_content': module2_raw
                },
                'module3_university_tiers': {
                    'title': '模块三：院校分档与定位',
                    'raw_content': self.extract_module_content(content, '模块三：院校分档与定位')
                },
                'module4_comparison': {
                    'title': '模块四：横向对决台',
                    'raw_content': self.extract_module_content(content, '模块四：横向对决台')
                },
                'module5_career_paths': {
                    'title': '模块五：职业路径图',
                    'raw_content': self.extract_module_content(content, '模块五：职业路径图')
                },
                'module6_fun_cards': {
                    'title': '模块六：反差与揭秘趣味卡片',
                    'raw_content': self.extract_module_content(content, '模块六：反差与揭秘趣味卡片')
                },
                'module7_personality_tags': {
                    'title': '模块七：专业气质人格标签',
                    'raw_content': self.extract_module_content(content, '模块七：专业气质人格标签')
                },
                'module8_raw_data': {
                    'title': '模块八：原始数据支撑',
                    'raw_content': self.extract_module_content(content, '模块八：原始数据支撑')
                }
            },
            'layer4_supplement': {
                'full_raw_content': self.clean_text(content),
                'tables': self.extract_tables(content)
            }
        }

        return result


def process_directory(source_dir: str, output_dir: str):
    """批量处理目录中的所有报告"""
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    parser = MajorReportParser()
    results = []
    success_count = 0
    error_count = 0

    for md_file in sorted(source_path.glob('*.md')):
        if md_file.name.startswith('_'):
            continue

        print(f"Processing: {md_file.name}")

        try:
            result = parser.parse_full_report(str(md_file))

            # 保存 JSON 文件
            output_file = output_path / f"{md_file.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            success_count += 1
            results.append({
                'source': md_file.name,
                'output': output_file.name,
                'status': 'success',
                'size_kb': len(json.dumps(result, ensure_ascii=False)) // 1024
            })

        except Exception as e:
            error_count += 1
            print(f"  Error: {e}")
            results.append({
                'source': md_file.name,
                'output': None,
                'status': f'error: {e}'
            })

    # 生成处理报告
    report_file = output_path / '_processing_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total': len(results),
                'success': success_count,
                'error': error_count
            },
            'files': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\nCompleted: {success_count}/{len(results)} files processed successfully")
    print(f"Errors: {error_count}")
    print(f"Report saved to: {report_file}")


if __name__ == '__main__':
    import sys

    source_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/专业评估报告'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'data/专业评估报告_json_v2'

    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print("-" * 50)

    process_directory(source_dir, output_dir)
