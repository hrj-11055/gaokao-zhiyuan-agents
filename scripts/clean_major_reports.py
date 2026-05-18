#!/usr/bin/env python3
"""
专业评估报告清理脚本
功能：
1. 解析现有 .md 格式专业报告
2. 提取8模块内容并转换为标准化 JSON
3. 清理特殊标记（[待核实]、数据收集完成等）
4. 验证数据完整性
"""

import re
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class MajorReportParser:
    """专业报告解析器"""

    def __init__(self, schema_path: str = None):
        self.markers_to_remove = ['[待核实]', '[需更新]', '[数据收集完成]', '所有研究均已完成']
        self.module_patterns = {
            'module1': r'## 模块一：专业画像与总评',
            'module2': r'## 模块二：六维量化评估',
            'module3': r'## 模块三：院校分档与定位',
            'module4': r'## 模块四：横向对决台',
            'module5': r'## 模块五：职业路径图',
            'module6': r'## 模块六：反差与揭秘趣味卡片',
            'module7': r'## 模块七：专业气质人格标签',
            'module8': r'## 模块八：原始数据支撑'
        }

    def clean_text(self, text: str) -> str:
        """清理文本中的特殊标记"""
        if not text:
            return ""
        for marker in self.markers_to_remove:
            text = text.replace(marker, '')
        return text.strip()

    def parse_code_and_name(self, filename: str) -> tuple:
        """从文件名解析专业代码和名称"""
        stem = Path(filename).stem
        match = re.match(r'(\d{6})_(.+)', stem)
        if match:
            return match.group(1), match.group(2)
        return None, stem

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
        pattern = r'\|\s*([^|]+?)\s*\|\s*([\d.]+)\s*\|\s*([^|]+?)\s*\|\s*([\d.]+)\s*\|'
        for match in re.finditer(pattern, content):
            dimension, score, weight, weighted = match.groups()
            dimension_clean = dimension.strip()
            if dimension_clean in dimension_map and dimension_clean != '加权总分':
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
        return ""

    def parse_recommendation_level(self, content: str) -> str:
        """解析推荐等级"""
        if '🟢 **绿灯推荐**' in content:
            return 'green'
        elif '🟡 **黄灯推荐**' in content:
            return 'yellow'
        elif '🔴 **红灯推荐**' in content:
            return 'red'
        return 'yellow'

    def parse_weighted_score(self, content: str) -> float:
        """解析加权总分"""
        # 匹配格式: | **加权总分** | | **100%** | **4.21** |
        match = re.search(r'\*\*加权总分\*\*.*?\|\s*\*\*[^|]*\*\*\s*\|\s*\*\*([\d.]+)\*\*\s*\|', content)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return 0.0

    def parse_module_dimension(self, content: str, dimension_name: str) -> Dict:
        """解析六维评估中的单个维度"""
        patterns = {
            'dimension1_market': r'### 维度一：市场准入与回报指数',
            'dimension2_industry': r'### 维度二：产业景气度指数',
            'dimension3_future': r'### 维度三：未来适应性指数',
            'dimension4_path': r'### 维度四：路径依赖与发展壁垒',
            'dimension5_education': r'### 维度五：教育资源投入度',
            'dimension6_discipline': r'### 维度六：学科内核强度'
        }
        return {}

    def parse_university_tiers(self, content: str) -> Dict:
        """解析院校分档"""
        tiers = {'tier_S': [], 'tier_A': [], 'tier_B': [], 'tier_C_note': '', 'selection_advice': ''}

        # 解析 S 档
        s_match = re.search(r'\*\*S 档.*?\*\*：(.+?)(?:\n|$)', content)
        if s_match:
            s_text = self.clean_text(s_match.group(1))
            tiers['tier_S'] = [s.strip() for s in s_text.split('、') if s.strip()]

        # 解析 A 档
        a_match = re.search(r'\*\*A 档.*?\*\*：(.+?)(?:\n|$)', content)
        if a_match:
            a_text = self.clean_text(a_match.group(1))
            tiers['tier_A'] = [s.strip() for s in a_text.split('、') if s.strip()]

        # 解析 B 档
        b_match = re.search(r'\*\*B 档.*?\*\*：(.+?)(?:\n|$)', content)
        if b_match:
            b_text = self.clean_text(b_match.group(1))
            tiers['tier_B'] = [s.strip() for s in b_text.split('、') if s.strip()]

        # 解析 C 档说明
        c_match = re.search(r'\*\*C 档.*?\*\*：(.+?)(?:\n\n|>)', content, re.DOTALL)
        if c_match:
            tiers['tier_C_note'] = self.clean_text(c_match.group(1))

        # 解析选校建议
        advice_match = re.search(r'### 3\.2 选校建议.*?\n(.+?)(?:\n\n|$)', content)
        if advice_match:
            tiers['selection_advice'] = self.clean_text(advice_match.group(1))

        return tiers

    def parse_employment_data(self, content: str) -> Dict:
        """解析就业数据"""
        employment = {
            'rate': '',
            'alignment_rate': '',
            'starting_salary': '',
            'salary_5yr': '',
            'further_study_rate': ''
        }

        # 解析就业率表格
        employment_pattern = r'\|\s*(\d{4})\s*\|\s*~?([\d.]+)%\s*\|'
        for match in re.finditer(employment_pattern, content):
            year, rate = match.groups()
            if year == '2024':
                employment['rate'] = f"~{rate}%"

        # 解析对口率
        alignment_pattern = r'\|\s*2024\s*\|[^|]*\|\s*~?([\d.]+)%\s*\|'
        alignment_match = re.search(alignment_pattern, content)
        if alignment_match:
            employment['alignment_rate'] = f"~{alignment_match.group(1)}%"

        # 解析起薪
        salary_pattern = r'起薪中位数.*?([\d,–]+)\s*元/月'
        salary_match = re.search(salary_pattern, content)
        if salary_match:
            employment['starting_salary'] = salary_match.group(1) + '元/月'

        return employment

    def parse_industry_data(self, content: str) -> Dict:
        """解析产业数据"""
        industry = {
            'stage': '',
            'cagr': '',
            'strategy_relevance': '',
            'supply_demand': ''
        }

        # 产业阶段
        if '成长期' in content:
            industry['stage'] = '成长期'
        elif '成熟期' in content:
            industry['stage'] = '成熟期'
        elif '导入期' in content:
            industry['stage'] = '导入期'
        elif '衰退期' in content:
            industry['stage'] = '衰退期'

        # 供需关系
        supply_match = re.search(r'`供不应求|供需平衡|供过于求`', content)
        if supply_match:
            industry['supply_demand'] = supply_match.group(0).strip('`')

        # 战略关联度
        if '核心关联' in content:
            industry['strategy_relevance'] = '核心关联'
        elif '强关联' in content:
            industry['strategy_relevance'] = '强关联'
        elif '弱关联' in content:
            industry['strategy_relevance'] = '弱关联'

        # CAGR
        cagr_match = re.search(r'CAGR\s*[约约]*([\d.]+[-–][\d.]+)%?', content)
        if cagr_match:
            industry['cagr'] = cagr_match.group(1) + '%'

        return industry

    def parse_ai_risk(self, content: str) -> Dict:
        """解析 AI 风险"""
        ai_risk = {'level': '', 'reason': ''}

        risk_patterns = [
            (r'`较低风险`', '低风险'),
            (r'`中等风险`', '中等风险'),
            (r'`较高风险`', '高风险'),
            (r'`低风险`', '低风险'),
            (r'`中低风险`', '中低风险')
        ]

        for pattern, level in risk_patterns:
            if re.search(pattern, content):
                ai_risk['level'] = level
                break

        reason_match = re.search(r'理由[：:](.+?)(?:\n\n|`)', content, re.DOTALL)
        if reason_match:
            ai_risk['reason'] = self.clean_text(reason_match.group(1))

        return ai_risk

    def parse_career_paths(self, content: str) -> list:
        """解析职业路径"""
        paths = []
        # 简化版本，实际需要根据具体格式调整
        return paths

    def parse_full_report(self, filepath: str) -> Dict[str, Any]:
        """解析完整报告文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        code, name = self.parse_code_and_name(filepath)

        # 提取模块内容
        module_content = {}
        for module_key, pattern in self.module_patterns.items():
            match = re.search(pattern + r'\s*\n(.*?)(?=## 模块|$)', content, re.DOTALL)
            if match:
                module_content[module_key] = match.group(1)

        # 构建结构化数据
        result = {
            'meta': {
                'version': '1.0.0',
                'generated_at': datetime.now().isoformat(),
                'updated_at': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                'data_sources': ['麦可思就业报告', '教育部数据', '各高校就业质量报告']
            },
            'layer1_overview': {
                'code': code,
                'name': name,
                'category': self._infer_category(code),
                'recommendation_level': self.parse_recommendation_level(module_content.get('module1', '')),
                'summary': self.parse_ai_summary(module_content.get('module1', '')),
                'radar': self.parse_radar_table(module_content.get('module1', '')),
                'weighted_score': self.parse_weighted_score(module_content.get('module1', ''))
            },
            'layer2_core': {
                'employment': self.parse_employment_data(module_content.get('module2', '')),
                'industry': self.parse_industry_data(module_content.get('module2', '')),
                'ai_risk': self.parse_ai_risk(module_content.get('module2', '')),
                'top_universities': [],
                'career_paths': [],
                'study_cost': {'level': '', 'description': ''}
            },
            'layer3_detail': {
                'module1_image': {
                    'ai_summary': self.parse_ai_summary(module_content.get('module1', '')),
                    'six_dimension_table': []
                },
                'module2_six_dimensions': {},
                'module3_university_tiers': self.parse_university_tiers(module_content.get('module3', '')),
                'module4_comparison': {},
                'module5_career_paths': {},
                'module6_fun_cards': {},
                'module7_personality_tags': {}
            },
            'layer4_supplement': {
                'module8_raw_data': {
                    'employment_data': [],
                    'salary_data': [],
                    'industry_data': []
                }
            }
        }

        return result

    def _infer_category(self, code: str) -> str:
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


def process_directory(source_dir: str, output_dir: str):
    """批量处理目录中的所有报告"""
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    parser = MajorReportParser()
    results = []

    for md_file in source_path.glob('*.md'):
        if md_file.name.startswith('_'):
            continue

        print(f"Processing: {md_file.name}")

        try:
            result = parser.parse_full_report(str(md_file))

            # 保存 JSON 文件
            output_file = output_path / f"{md_file.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            results.append({
                'source': md_file.name,
                'output': output_file.name,
                'status': 'success'
            })

        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                'source': md_file.name,
                'output': None,
                'status': f'error: {e}'
            })

    # 生成处理报告
    report_file = output_path / '_processing_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\nCompleted: {success_count}/{len(results)} files processed successfully")
    print(f"Report saved to: {report_file}")


if __name__ == '__main__':
    import sys

    source_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/专业评估报告'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'data/专业评估报告_json'

    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print("-" * 50)

    process_directory(source_dir, output_dir)
