#!/usr/bin/env python3
"""
院校评估报告完整提取脚本 v2
策略：保留原始 markdown 文本 + 提取结构化关键字段
"""

import re
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class UnivReportParser:
    """院校报告完整解析器"""

    # 985工程院校名单（39所）
    SCHOOL_985 = {
        '清华大学', '北京大学', '中国人民大学', '北京师范大学', '北京航空航天大学',
        '北京理工大学', '中国农业大学', '中央民族大学', '南开大学', '天津大学',
        '大连理工大学', '东北大学', '吉林大学', '哈尔滨工业大学', '复旦大学',
        '同济大学', '上海交通大学', '华东师范大学', '南京大学', '东南大学',
        '浙江大学', '中国科学技术大学', '厦门大学', '山东大学', '中国海洋大学',
        '武汉大学', '华中科技大学', '湖南大学', '中南大学', '中山大学',
        '华南理工大学', '四川大学', '重庆大学', '电子科技大学', '西安交通大学',
        '西北工业大学', '西北农林科技大学', '兰州大学', '国防科技大学',
    }

    # 211工程院校名单（不含985）
    SCHOOL_211 = {
        '北京交通大学', '北京工业大学', '北京科技大学', '北京化工大学', '北京邮电大学',
        '北京林业大学', '北京中医药大学', '北京外国语大学', '中国传媒大学', '对外经济贸易大学',
        '中央财经大学', '中国政法大学', '华北电力大学', '天津医科大学', '河北工业大学',
        '太原理工大学', '内蒙古大学', '辽宁大学', '大连海事大学', '延边大学', '东北师范大学',
        '哈尔滨工程大学', '东北农业大学', '东北林业大学', '华东理工大学', '东华大学',
        '上海外国语大学', '上海财经大学', '上海大学', '苏州大学', '南京航空航天大学',
        '南京理工大学', '中国矿业大学', '河海大学', '江南大学', '南京农业大学', '中国药科大学',
        '南京师范大学', '安徽大学', '合肥工业大学', '福州大学', '南昌大学', '中国石油大学',
        '郑州大学', '武汉理工大学', '华中农业大学', '华中师范大学', '中南财经政法大学',
        '湖南师范大学', '华南师范大学', '广西大学', '海南大学', '四川农业大学', '西南交通大学',
        '西南大学', '西南财经大学', '云南大学', '西藏大学', '西北大学', '西安交通大学',
        '西北工业大学', '西安电子科技大学', '长安大学', '青海大学', '宁夏大学', '新疆大学',
        '石河子大学'
    }

    # 中外合作办学院校
    SCHOOL_COOPERATIVE = {
        '上海纽约大学', '昆山杜克大学', '宁波诺丁汉大学', '西交利物浦大学', '温州肯恩大学',
        '深圳北理莫斯科大学', '香港中文大学(深圳)', '北京师范大学-香港浸会大学联合国际学院',
        '广东以色列理工学院', '北师香港浸会大学', '北师香港浸会大学'
    }

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

    def parse_univ_name(self, filename: str) -> str:
        """从文件名解析院校名称"""
        stem = Path(filename).stem
        # 移除可能的编号前缀
        stem = re.sub(r'^\d+_', '', stem)
        return stem

    # 模块编号 → (key, keywords)
    MODULE_MAP = {
        1: ('module1_academic_capital', ['学术资本', '学术实力', '学术资源']),
        2: ('module2_student_competitiveness', ['生源竞争力', '生源质量', '入学门槛']),
        3: ('module3_graduate_value', ['毕业生价值', '就业价值', '毕业价值']),
        4: ('module4_location_industry', ['区位', '产业', '全球化', '城市']),
        5: ('module5_campus_ecosystem', ['校园生态', '校园生活', '生活品质', '品牌', '宿舍', '转专业']),
        6: ('module6_comprehensive_evaluation', ['综合评估', '量化评分', '六维', '总分', '加权', '总结评价', '执行摘要', '报考建议', '横向对比']),
        7: ('module7_culture_cards', ['文化揭秘', '避坑', '生存指南', '气质标签', '报考指南', '校园真相', '刻板印象', '校园精神', '校园黑话', '风险提示']),
        8: ('module8_raw_data', ['原始数据', '数据汇总', '数据支撑', '数据源', '数据来源', '未检索']),
        9: ('module9_structured_export', ['结构化数据', '数据导出', '结构化导出']),
    }

    MODULE_TITLES = {
        1: '模块一：学术资本',
        2: '模块二：生源竞争力',
        3: '模块三：毕业生价值实现',
        4: '模块四：区位与产业势能',
        5: '模块五：校园生态',
        6: '模块六：综合评估与量化评分',
        7: '模块七：文化揭秘与避坑指南',
        8: '模块八：原始数据汇总',
        9: '模块九：结构化数据导出',
    }

    # 中文数字 → 阿拉伯数字
    CN_NUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}

    def _heading_to_module_num(self, heading: str) -> int:
        """从标题文本推断模块编号（1-9），返回 0 表示无法识别"""
        # 策略1: 语义关键词优先，避免 "六、校园生态" 被硬按编号归到模块六
        for num, (_, keywords) in self.MODULE_MAP.items():
            for kw in keywords:
                if kw in heading:
                    return num

        # 策略2: "模块X" / "模块X：" / "第X模块"
        m = re.search(r'模块([一二三四五六七八九\d])', heading)
        if m:
            cn = m.group(1)
            return self.CN_NUM.get(cn, int(cn) if cn.isdigit() else 0)

        # 策略3: "第X章" / "第X部分"
        m = re.search(r'第([一二三四五六七八九\d])[章部分]', heading)
        if m:
            cn = m.group(1)
            return self.CN_NUM.get(cn, int(cn) if cn.isdigit() else 0)

        # 策略4: "X、" (中文数字顿号)
        m = re.match(r'([一二三四五六七八九])、', heading.strip())
        if m:
            return self.CN_NUM.get(m.group(1), 0)

        # 策略5: 数字开头 "1." / "1、" 或子标题 "1.1"
        m = re.match(r'(\d)(?:[.、．]|\.\d+)', heading.strip())
        if m:
            return int(m.group(1))

        return 0

    def extract_module_by_number(self, content: str, module_num: int) -> Dict[str, str]:
        """按实际标题切模块，保留模块内的子标题和正文。"""
        headings = []
        for match in re.finditer(r'(?m)^(#{1,4})\s+(.+?)\s*$', content):
            title = match.group(2).strip()
            num = self._heading_to_module_num(title)
            if num:
                headings.append({
                    'num': num,
                    'title': title,
                    'start': match.start(),
                    'body_start': match.end(),
                    'level': len(match.group(1)),
                })

        for idx, heading in enumerate(headings):
            if heading['num'] != module_num:
                continue

            end = len(content)
            for next_heading in headings[idx + 1:]:
                if next_heading['num'] != module_num and next_heading['level'] <= heading['level']:
                    end = next_heading['start']
                    break

            return {
                'title': heading['title'],
                'raw_content': self.clean_text(content[heading['body_start']:end])
            }

        return {
            'title': self.MODULE_TITLES.get(module_num, f'模块{module_num}'),
            'raw_content': ''
        }

    def parse_all_modules(self, content: str) -> Dict[str, str]:
        """提取所有模块，标题用实际报告标题，key 保持稳定。"""
        return {
            self.MODULE_MAP[num][0]: self.extract_module_by_number(content, num)
            for num in sorted(self.MODULE_MAP)
        }

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
            dimension_clean = dimension.strip().replace('*', '').replace('**', '')
            if dimension_clean in dimension_map:
                try:
                    radar[dimension_map[dimension_clean]] = float(score)
                except ValueError:
                    continue
        return radar

    def parse_weighted_score(self, content: str) -> float:
        """解析加权总分"""
        # 支持多种格式
        patterns = [
            r'\*\*加权总分\*\*.*?\|\s*\*\*[^|]*\*\*\s*\|\s*\|?\s*\*\*([\d.]+)\*\*\s*\|',
            r'加权总分.*?[:：]\s*\**([\d.]+)\**',
            r'"total_weighted":\s*([\d.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return 0.0

    def parse_one_sentence_recommend(self, content: str) -> str:
        """解析一句话推荐"""
        patterns = [
            r'#{2,4}\s*\d+(?:\.\d+)?\s*一句话推荐\s*\n+\s*\*\*(.+?)\*\*',
            r'#{2,4}\s*\d+(?:\.\d+)?\s*一句话推荐\s*\n+\s*(.+?)(?:\n\n|#{2,4}\s|$)',
            r'一句话推荐[：:]\s*\*\*(.+?)\*\*',
            r'一句话推荐[：:]\s*\*(.+?)\*',
            r'一句话推荐[：:]\s*(.+?)(?:\n\n|#{2,4}\s|$)',
            r'一句话报考建议[：:]\s*(.+?)(?:\n\n|#{2,4}\s|$)',
            r'核心报考建议[：:]\s*(.+?)(?:\n\n|#{2,4}\s|$)',
            r'终极建议[：:]\s*(.+?)(?:\n\n|#{2,4}\s|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                value = self.clean_text(match.group(1))
                value = re.sub(r'^\s*[-*]\s*', '', value)
                value = value.split('\n')[0].strip()
                if value:
                    return value
        return ""

    def parse_summary_fallback(self, content: str, module6_raw: str = "") -> str:
        """为列表摘要提供兜底，优先一句话推荐，其次总结章节/序言首段。"""
        direct = self.parse_one_sentence_recommend(module6_raw) or self.parse_one_sentence_recommend(content)
        if direct:
            return direct[:260]

        summary_patterns = [
            r'#{2,4}\s*(?:第[七八九十]+章[:：]?)?总结评价[^\n]*\n+(.+?)(?:\n\n|#{2,4}\s|$)',
            r'#{2,4}\s*(?:结论|总结|报考建议)[^\n]*\n+(.+?)(?:\n\n|#{2,4}\s|$)',
            r'#{2,4}\s*(?:前言|序言)[^\n]*\n+(.+?)(?:\n\n|#{2,4}\s|$)',
        ]
        for pattern in summary_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                value = self.clean_text(match.group(1))
                value = re.sub(r'[#>*`|]', '', value)
                value = re.sub(r'\s+', ' ', value).strip()
                if value:
                    return value[:260]

        paragraphs = [
            self.clean_text(p)
            for p in re.split(r'\n\s*\n', content)
            if len(self.clean_text(p)) >= 80 and not p.lstrip().startswith('|')
        ]
        return re.sub(r'\s+', ' ', paragraphs[0]).strip()[:260] if paragraphs else ""

    def parse_location(self, content: str) -> str:
        """解析所在地"""
        patterns = [
            r'\*\*所在地\*\*：(.+?)(?:\n|$)',
            r'位于(.+?)(?:[，,。]|市|区|镇)',
            r'location.*?[:：](.+?)(?:\n|,|})'
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return self.clean_text(match.group(1))
        return ""

    def parse_univ_type(self, name: str, content: str) -> str:
        """解析院校类型，优先使用预定义名单"""
        # 标准化院校名称
        clean_name = name.strip().replace('（', '(').replace('）', ')')

        # 优先检查预定义名单（精确匹配）
        if clean_name in self.SCHOOL_COOPERATIVE:
            return '中外合作办学'
        if clean_name in self.SCHOOL_985:
            return '985'
        if clean_name in self.SCHOOL_211:
            return '211'

        # 检查名称中是否包含预定义院校名称（部分匹配，用于处理简称）
        for school in self.SCHOOL_COOPERATIVE:
            if school in clean_name or clean_name in school:
                return '中外合作办学'

        # 检查标题行是否明确标注为中外合作办学
        header_match = re.search(r'^#+\s*[^\n]*?(中外合作|合作办学).*?(大学|学院)', content, re.MULTILINE)
        if header_match:
            return '中外合作办学'

        # 检查是否为独立学院（基于命名模式）
        # 独立学院通常命名为：XX大学XX学院（母体+独立学院）
        independent_pattern = r'.{2,4}大学.{2,6}学院'
        if re.match(independent_pattern, clean_name):
            # 进一步确认：检查内容中是否明确说明是独立学院
            if re.search(r'是.*?独立学院|独立学院.*?创办', content):
                return '独立学院'
            # 或者名称中包含明显的独立学院关键词
            if any(kw in clean_name for kw in ['科技学院', '理工学院', '工商学院', '文理学院', '财经学院']):
                # 检查是否有母体大学（前面有"大学"二字）
                if re.search(r'大学.*?(科技|理工|工商|文理|财经)学院', clean_name):
                    return '独立学院'

        # 如果不在预定义名单中，检查内容中的明确标注
        # 检查是否明确标注为非某种类型
        if re.search(r'非[^\d]*(985|211|双一流)', content):
            # 如果明确说"非985/211/双一流"，继续检查其他类型
            pass
        else:
            # 检查双一流（需要明确标注，如"入选双一流"、"双一流建设高校"）
            if re.search(r'(入选|列为|是|属于).*?双一流.*?(建设高校|学科)', content):
                return '双一流'
            # 检查 985（需要明确标注）
            if re.search(r'(是|属于|入选)?.*985工程', content):
                return '985'
            # 检查 211（需要明确标注）
            if re.search(r'(是|属于|入选)?.*211工程', content):
                return '211'

        # 检查民办（需要明确标注）
        if re.search(r'^(#+\s*)?(民办|私立).*?(院校|大学|学院)', content, re.MULTILINE):
            return '民办'
        if re.search(r'(是|属于).*?(民办|私立).*?(院校|大学|学院)', content):
            return '民办'

        # 默认为公办
        return '公办'

    def parse_recommendation_level(self, content: str, weighted_score: float) -> str:
        """解析推荐等级"""
        if weighted_score >= 4.0:
            return 'green'
        elif weighted_score >= 3.0:
            return 'yellow'
        return 'red'

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

        name = self.parse_univ_name(filepath)

        # 提取所有模块（新的统一方法）
        all_modules = self.parse_all_modules(content)

        # 提取模块六（综合评估）用于评分
        module6_raw = all_modules.get('module6_comprehensive_evaluation', {}).get('raw_content', '')
        weighted_score = self.parse_weighted_score(module6_raw)
        # 如果模块六没提取到，从全文尝试
        if weighted_score == 0.0:
            weighted_score = self.parse_weighted_score(content)
        summary = self.parse_summary_fallback(content, module6_raw)

        # 构建结构化数据
        result = {
            'meta': {
                'version': '2.0.0',
                'generated_at': datetime.now().isoformat(),
                'updated_at': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                'source_file': Path(filepath).name,
                'data_sources': ['软科排名', '校友会排名', '各高校就业质量报告', '官方招生数据']
            },
            'layer1_overview': {
                'name': name,
                'location': self.parse_location(content),
                'type': self.parse_univ_type(name, content),
                'recommendation_level': self.parse_recommendation_level(content, weighted_score),
                'summary': summary,
                'radar': self.parse_six_dimension_table(module6_raw),
                'weighted_score': weighted_score,
                'one_sentence_recommend': summary
            },
            'layer2_core': {
                'summary': summary
            },
            'layer3_detail': {
                'module1_academic_capital': {
                    'title': all_modules.get('module1_academic_capital', {}).get('title', '模块一：学术资本'),
                    'raw_content': all_modules.get('module1_academic_capital', {}).get('raw_content', '')
                },
                'module2_student_competitiveness': {
                    'title': all_modules.get('module2_student_competitiveness', {}).get('title', '模块二：生源竞争力'),
                    'raw_content': all_modules.get('module2_student_competitiveness', {}).get('raw_content', '')
                },
                'module3_graduate_value': {
                    'title': all_modules.get('module3_graduate_value', {}).get('title', '模块三：毕业生价值实现'),
                    'raw_content': all_modules.get('module3_graduate_value', {}).get('raw_content', '')
                },
                'module4_location_industry': {
                    'title': all_modules.get('module4_location_industry', {}).get('title', '模块四：区位与产业势能'),
                    'raw_content': all_modules.get('module4_location_industry', {}).get('raw_content', '')
                },
                'module5_campus_ecosystem': {
                    'title': all_modules.get('module5_campus_ecosystem', {}).get('title', '模块五：校园生态'),
                    'raw_content': all_modules.get('module5_campus_ecosystem', {}).get('raw_content', '')
                },
                'module6_comprehensive_evaluation': {
                    'title': all_modules.get('module6_comprehensive_evaluation', {}).get('title', '模块六：综合评估与量化评分'),
                    'raw_content': module6_raw
                },
                'module7_culture_cards': {
                    'title': all_modules.get('module7_culture_cards', {}).get('title', '模块七：文化揭秘与避坑指南'),
                    'raw_content': all_modules.get('module7_culture_cards', {}).get('raw_content', '')
                },
                'module8_raw_data': {
                    'title': all_modules.get('module8_raw_data', {}).get('title', '模块八：原始数据汇总'),
                    'raw_content': all_modules.get('module8_raw_data', {}).get('raw_content', '')
                }
            },
            'layer4_supplement': {
                'full_raw_content': self.clean_text(content),
                'tables': self.extract_tables(content),
                'module9_structured_export': {
                    'title': '模块九：结构化数据导出',
                    'raw_content': all_modules.get('module9_structured_export', {}).get('raw_content', '')
                }
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

    source_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/大学评估报告'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'data/大学评估报告_json_v2'

    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print("-" * 50)

    process_directory(source_dir, output_dir)
