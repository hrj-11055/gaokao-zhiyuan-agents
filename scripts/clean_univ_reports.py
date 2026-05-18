#!/usr/bin/env python3
"""
院校评估报告清理脚本
功能：
1. 解析现有 .md 格式院校报告
2. 提取9模块内容并转换为标准化 JSON
3. 清理特殊标记（[待核实]、数据收集完成等）
4. 验证数据完整性
"""

import re
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class UnivReportParser:
    """院校报告解析器"""

    def __init__(self):
        self.markers_to_remove = ['[待核实]', '[需更新]', '[数据收集完成]', '所有研究均已完成']
        self.module_patterns = {
            'module1': r'## 模块一：学术资本',
            'module2': r'## 模块二：生源竞争力',
            'module3': r'## 模块三：毕业生价值实现',
            'module4': r'## 模块四：区位与产业势能',
            'module5': r'## 模块五：校园生态与品牌',
            'module6': r'## 模块六：综合评估与量化评分',
            'module7': r'## 模块七：文化揭秘卡片',
            'module8': r'## 模块八：原始数据汇总',
            'module9': r'## 模块九：结构化数据导出'
        }

    def clean_text(self, text: str) -> str:
        """清理文本中的特殊标记"""
        if not text:
            return ""
        for marker in self.markers_to_remove:
            text = text.replace(marker, '')
        return text.strip()

    def parse_univ_name(self, filename: str) -> str:
        """从文件名解析院校名称"""
        stem = Path(filename).stem
        # 移除可能的编号前缀
        stem = re.sub(r'^\d+_', '', stem)
        return stem

    def parse_location(self, content: str) -> str:
        """解析所在地"""
        match = re.search(r'\*\*所在地\*\*：(.+?)(?:\n|$)', content)
        if match:
            return self.clean_text(match.group(1))
        return ""

    def parse_univ_type(self, content: str) -> str:
        """解析院校类型"""
        type_patterns = {
            '中外合作办学': '中外合作办学',
            '双一流': '双一流',
            '985': '985',
            '211': '211',
            '民办': '民办'
        }
        for pattern, value in type_patterns.items():
            if pattern in content:
                return value
        return '公办'

    def parse_philosophy(self, content: str) -> str:
        """解析办学理念"""
        match = re.search(r'\*\*办学理念[\/\*特色\*]*\*\*：(.+?)(?:\n|$)', content)
        if match:
            return self.clean_text(match.group(1))
        return ""

    def parse_six_dimension_table(self, content: str) -> Dict:
        """解析六维评分表"""
        radar = {}
        dimension_map = {
            '学术资本': 'academic_capital',
            '毕业生价值实现': 'graduate_value',
            '区位与产业势能': 'location_advantage',
            '全球化能力': 'globalization',
            '学生赋权与自由度': 'student_empowerment',
            '品牌资产与文化印记': 'brand_asset'
        }
        # 院校报告格式: | 评估维度 | 核心依据摘要 | 维度得分 | 权重 | 加权得分 |
        pattern = r'\|\s*([^|\n]+?)\s*\|\s*[^|]+?\|\s*([\d.]+)\s*\|\s*[^|]+?\|\s*([\d.]+)\s*\|'
        for match in re.finditer(pattern, content):
            dimension, score, weighted = match.groups()
            dimension_clean = dimension.strip()
            if dimension_clean in dimension_map:
                try:
                    radar[dimension_map[dimension_clean]] = float(score)
                except ValueError:
                    continue
        return radar

    def parse_weighted_score(self, content: str) -> float:
        """解析加权总分"""
        # 院校报告格式（5列）: | **加权总分** | | **100%** | | **4.27** |
        # 专业报告格式（4列）: | **加权总分** | | **100%** | **4.21** |
        match = re.search(r'\*\*加权总分\*\*.*?\|\s*\*\*[^|]*\*\*\s*\|\s*\|?\s*\*\*([\d.]+)\*\*\s*\|', content)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return 0.0

    def parse_executive_summary(self, content: str) -> str:
        """解析执行摘要"""
        match = re.search(r'### 6\.2 执行摘要\s*\n(.+?)(?=###|\n\n---|$)', content, re.DOTALL)
        if match:
            return self.clean_text(match.group(1))
        return ""

    def parse_one_sentence_recommend(self, content: str) -> str:
        """解析一句话推荐"""
        match = re.search(r'### 6\.3 一句话推荐\s*\n\*\*(.+?)\*\*', content)
        if match:
            return self.clean_text(match.group(1))
        return ""

    def parse_academic_strength(self, content: str) -> Dict:
        """解析学术实力"""
        strength = {
            'esi_top_1_percent': [],
            'national_first_class_majors': [],
            'academician_count': 0,
            'teaching_language': '',
            'student_teacher_ratio': ''
        }

        # ESI 前1%学科
        esi_pattern = r'\|\s*([^|]+?)\s*\|\s*ESI\s*全球前\s*1%'
        for match in re.finditer(esi_pattern, content):
            strength['esi_top_1_percent'].append(match.group(1).strip())

        # 国家级一流本科专业
        first_class_match = re.search(r'\*\*国家级一流本科专业建设点\*\*[：:](.+?)(?:\n|$)', content)
        if first_class_match:
            majors_text = self.clean_text(first_class_match.group(1))
            strength['national_first_class_majors'] = [
                m.strip() for m in re.split(r'[,、、]', majors_text) if m.strip()
            ]

        # 院士人数
        academician_match = re.search(r'院士[：:].*?(\d+)', content)
        if academician_match:
            strength['academician_count'] = int(academician_match.group(1))

        # 教学语言
        if '全英文' in content:
            strength['teaching_language'] = 'English'
        elif '双语' in content:
            strength['teaching_language'] = 'Bilingual'
        else:
            strength['teaching_language'] = 'Chinese'

        # 生师比
        ratio_match = re.search(r'生师比[：:约]*\s*(\d+:\d+)', content)
        if ratio_match:
            strength['student_teacher_ratio'] = ratio_match.group(1)

        return strength

    def parse_admission_data(self, content: str) -> Dict:
        """解析录取数据"""
        admission = {
            'guangdong_history_rank': 0,
            'guangdong_physics_rank': 0,
            'comp_eval_ratio': '',
            'tuition_fee': ''
        }

        # 广东历史组位次
        history_match = re.search(r'\|\s*广东\s*\|[^|]*\|\s*(\d+)\s*\|', content)
        if history_match:
            admission['guangdong_history_rank'] = int(history_match.group(1))

        # 广东物理组位次
        physics_pattern = r'物理组[组]?[录取]?.*?广东.*?\|\s*[^|]*\|\s*(\d+)\s*\|'
        physics_match = re.search(physics_pattern, content)
        if physics_match:
            admission['guangdong_physics_rank'] = int(physics_match.group(1))

        # 综合评价比例
        comp_match = re.search(r'(\d+):(\d+):(\d+).*?综合评价', content)
        if comp_match:
            admission['comp_eval_ratio'] = f"{comp_match.group(1)}:{comp_match.group(2)}:{comp_match.group(3)}"

        # 学费
        tuition_match = re.search(r'学费[：:约]*.*?([\d,]+)\s*元', content)
        if tuition_match:
            admission['tuition_fee'] = f"{tuition_match.group(1)}元/年"

        return admission

    def parse_graduate_outcomes(self, content: str) -> Dict:
        """解析毕业生去向"""
        outcomes = {
            'further_study_rate': '',
            'qs_top_100_admission_rate': '',
            'starting_salary_median': 0,
            'top_destinations': [],
            'top_employers': []
        }

        # 深造率
        further_match = re.search(r'深造率[：:约]*\s*([\d.]+)%', content)
        if further_match:
            outcomes['further_study_rate'] = f"{further_match.group(1)}%"

        # QS前100录取率
        qs_match = re.search(r'QS\s*前\s*100.*?([\d.]+)%', content)
        if qs_match:
            outcomes['qs_top_100_admission_rate'] = f"{qs_match.group(1)}%"

        # 起薪中位数
        salary_match = re.search(r'起薪[中约位]+数[：:约]*.*?([\d,]+)\s*元', content)
        if salary_match:
            outcomes['starting_salary_median'] = int(salary_match.group(1).replace(',', ''))

        # 主要深造目的地
        dest_pattern = r'\|\s*([^|]+英国|香港|美国|澳洲|新加坡[^|]*)\s*\|\s*[^|]*\|\s*([^|]+?)\s*\|'
        for match in re.finditer(dest_pattern, content):
            outcomes['top_destinations'].append(match.group(1).strip())

        # 主要雇主
        employer_pattern = r'\|\s*([^|]+行业|金融|互联网[^|]*)\s*\|.*?\|\s*([^|]+?)\s*\|'
        for match in re.finditer(employer_pattern, content):
            employers = match.group(2)
            outcomes['top_employers'].extend([e.strip() for e in re.split(r'[、,]', employers) if e.strip()])

        return outcomes

    def parse_location_advantage(self, content: str) -> Dict:
        """解析区位优势"""
        location = {
            'city': '',
            'region': '',
            'industrial_clusters': [],
            'policy_benefits': []
        }

        # 城市
        city_match = re.search(r'位于(.+?)[市区区]', content)
        if city_match:
            location['city'] = city_match.group(1).strip()

        # 区域
        if '大湾区' in content or '粤港澳' in content:
            location['region'] = '粤港澳大湾区'
        elif '长三角' in content:
            location['region'] = '长三角'
        elif '京津冀' in content:
            location['region'] = '京津冀'

        # 产业集群
        cluster_pattern = r'(?:聚集|周边).*?([^、。]+?(?:公司|科技|企业|集团|软件))'
        for match in re.finditer(cluster_pattern, content):
            location['industrial_clusters'].append(match.group(1))

        return location

    def parse_horizontal_comparison(self, content: str) -> list:
        """解析横向对比"""
        comparisons = []
        pattern = r'\*\*对比(.+?)\*\*[：:](.+?)(?:\n|$|\*|对比)'
        for match in re.finditer(pattern, content):
            target = self.clean_text(match.group(1))
            difference = self.clean_text(match.group(2))
            if target and difference:
                comparisons.append({'name': target, 'similarity': '同类院校', 'key_difference': difference})
        return comparisons

    def parse_risks(self, content: str) -> list:
        """解析风险点"""
        risks = []
        risk_pattern = r'\d+\.\s*\*\*([^*]+)\*\*[：:](.+?)(?=\n\d+\.|$)'
        for match in re.finditer(risk_pattern, content, re.DOTALL):
            category = self.clean_text(match.group(1))
            description = self.clean_text(match.group(2))
            if category and description:
                risks.append({'category': category, 'description': description})
        return risks

    def parse_temperament_tags(self, content: str) -> list:
        """解析气质标签云"""
        tags = []
        tag_pattern = r'\`([^\`]+?)\`'
        for match in re.finditer(tag_pattern, content):
            tag = match.group(1).strip()
            if tag and tag.startswith('['):
                tags.append(tag.strip('[]'))
        return tags

    def parse_full_report(self, filepath: str) -> Dict[str, Any]:
        """解析完整报告文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        name = self.parse_univ_name(filepath)

        # 提取模块内容
        module_content = {}
        full_content = content
        for module_key, pattern in self.module_patterns.items():
            match = re.search(pattern + r'\s*\n(.*?)(?=## 模块|$)', full_content, re.DOTALL)
            if match:
                module_content[module_key] = match.group(1)

        # 模块六通常是综合评估，放在前面处理
        eval_content = module_content.get('module6', '')

        # 推荐等级判断（基于加权总分）
        weighted_score = self.parse_weighted_score(eval_content)
        if weighted_score >= 4.0:
            recommendation_level = 'green'
        elif weighted_score >= 3.0:
            recommendation_level = 'yellow'
        else:
            recommendation_level = 'red'

        # 构建结构化数据
        result = {
            'meta': {
                'version': '1.0.0',
                'generated_at': datetime.now().isoformat(),
                'updated_at': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                'data_sources': ['软科排名', '校友会排名', '各高校就业质量报告', '官方招生数据']
            },
            'layer1_overview': {
                'name': name,
                'english_name': '',
                'former_name': '',
                'location': self.parse_location(content),
                'type': self.parse_univ_type(content),
                'philosophy': self.parse_philosophy(content),
                'recommendation_level': recommendation_level,
                'summary': self.parse_one_sentence_recommend(eval_content),
                'radar': self.parse_six_dimension_table(eval_content),
                'weighted_score': weighted_score,
                'one_sentence_recommend': self.parse_one_sentence_recommend(eval_content)
            },
            'layer2_core': {
                'academic_strength': self.parse_academic_strength(module_content.get('module1', '')),
                'admission_data': self.parse_admission_data(module_content.get('module2', '')),
                'graduate_outcomes': self.parse_graduate_outcomes(module_content.get('module3', '')),
                'location_advantage': self.parse_location_advantage(module_content.get('module4', '')),
                'comparison_peers': self.parse_horizontal_comparison(eval_content),
                'risks': self.parse_risks(module_content.get('module5', ''))
            },
            'layer3_detail': {
                'module1_academic_capital': {},
                'module2_student_competitiveness': {},
                'module3_graduate_value': {},
                'module4_location_industry': {},
                'module5_campus_ecosystem': {},
                'module6_comprehensive_evaluation': {
                  'executive_summary': self.parse_executive_summary(eval_content),
                  'one_sentence_recommend': self.parse_one_sentence_recommend(eval_content),
                  'horizontal_comparison': self.parse_horizontal_comparison(eval_content)
                },
                'module7_culture_cards': {
                    'temperament_tags': self.parse_temperament_tags(module_content.get('module7', ''))
                }
            },
            'layer4_supplement': {
                'module8_raw_data': {},
                'module9_structured_export': {}
            }
        }

        return result


def process_directory(source_dir: str, output_dir: str):
    """批量处理目录中的所有报告"""
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    parser = UnivReportParser()
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

    source_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/大学评估报告'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'data/大学评估报告_json'

    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print("-" * 50)

    process_directory(source_dir, output_dir)
