import csv
from pathlib import Path

# 路径配置
CSV_PATH = Path('高等院校名单.csv')
REPORTS_DIR = Path('data/大学评估报告')
STATUS_FILE = Path('evaluation_status.md')

# 获取已完成名单
finished = {f.stem for f in REPORTS_DIR.glob('*.md')}

# 读取大学列表并生成状态记录
status_list = []
current_province = ""
total_done = 0
total_all = 0

with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    next(reader) # 跳过表头
    for row in reader:
        if not row or not row[0].strip(): continue
        
        # 解析省份
        if '所）' in row[0] or '所)' in row[0]:
            current_province = row[0].split('（')[0].split('(')[0]
            continue
            
        # 筛选本科
        if len(row) > 5 and row[5].strip() == '本科':
            name = row[1].strip()
            total_all += 1
            is_done = name in finished
            if is_done: total_done += 1
            status_list.append({
                'province': current_province,
                'name': name,
                'status': '✅ 已完成' if is_done else '⏳ 待评估'
            })

# 写入 Markdown 表格
with open(STATUS_FILE, 'w', encoding='utf-8') as f:
    f.write(f"# 大学评估进度表 (总计: {total_done}/{total_all})\n\n")
    f.write("| 省份 | 大学名称 | 状态 |\n| :--- | :--- | :--- |\n")
    for item in status_list:
        f.write(f"| {item['province']} | {item['name']} | {item['status']} |\n")

print(f"进度表已生成: {STATUS_FILE}，共 {total_done} 已完成，{total_all - total_done} 待评估。")
