# 录取分数线数据架构 - 测试评估指标

## 一、验收标准概览

| 模块 | 指标 | 目标值 | 测试方法 |
|------|------|--------|----------|
| 数据转换 | 转换完整率 | ≥ 99.5% | 对比源文件行数 |
| 数据转换 | 字段正确率 | 100% | 抽样验证 |
| API 查询 | 响应时间 | ≤ 500ms (P95) | 性能测试 |
| API 查询 | 数据准确率 | 100% | 对比源数据 |
| Dify RAG | 检索召回率 | ≥ 90% | 测试集验证 |
| 综合报告 | 推荐相关性 | ≥ 80% | 人工评分 |
| 综合报告 | 数据真实率 | 100% | 零编造原则 |

## 二、数据转换测试 (Phase 1)

### 2.1 转换完整性

**测试命令**：
```bash
# 运行转换
python3 data/convert_scores_to_json.py

# 验证输出
python3 tests/test_scores_conversion.py
```

**验收指标**：

| 指标 | 计算方式 | 目标 | 失败阈值 |
|------|----------|------|----------|
| 解析文件数 | 成功解析的 .md 文件 / 总文件数 | 31/31 | < 30 |
| 解析学校数 | 解析出的学校总数 | ≥ 10 万 | < 9.5 万 |
| 解析专业数 | 解析出的专业记录数 | ≥ 源文件行数 | < 源文件 99% |
| 字段完整率 | 非空字段数 / 总字段数 | ≥ 99% | < 95% |

**自动化测试脚本**：
```python
# tests/test_scores_conversion.py

def test_conversion_completeness():
    """测试转换完整性"""
    source_count = count_markdown_records()
    json_count = count_json_records()

    completeness = json_count / source_count
    assert completeness >= 0.995, f"转换完整率 {completeness:.2%} 低于 99.5%"

def test_field_correctness():
    """测试字段正确性 (抽样验证)"""
    sample = load_sample_data(n=100)

    for record in sample:
        # 必填字段检查
        assert record.get('year'), "缺少 year 字段"
        assert record.get('province_name'), "缺少 province_name"
        assert record.get('school_name'), "缺少 school_name"
        assert record.get('major_name'), "缺少 major_name"

        # 数据类型检查
        assert isinstance(record['year'], int)
        assert isinstance(record.get('min_score', 0), int)
        assert isinstance(record.get('min_rank', 0), int)

        # 合理性检查
        if record.get('min_score'):
            assert 400 <= record['min_score'] <= 750, f"分数异常: {record['min_score']}"

def test_year_coverage():
    """测试年份覆盖"""
    years = get_distinct_years()
    assert set(years) == {2023, 2024, 2025}, f"年份覆盖不全: {years}"

def test_province_coverage():
    """测试省份覆盖"""
    provinces = get_distinct_provinces()
    assert len(provinces) == 31, f"省份数量不足: {len(provinces)}/31"
```

### 2.2 数据质量检查

| 检查项 | 说明 | 目标 |
|--------|------|------|
| 重复记录 | 同一学校+专业+年份+省份不重复 | 0 重复 |
| 孤儿记录 | 学校ID或专业ID不应为空 | ≤ 0.1% |
| 异常值 | 分数在 400-750 之间，位次 > 0 | 100% 合规 |
| 编码一致性 | 省份ID、学校ID符合规范 | 100% 合规 |

## 三、API 查询测试 (Phase 2)

### 3.1 功能正确性测试

**测试用例集**：

```python
# tests/test_scores_api.py

# 用例 1: 分数匹配 - 广东600分物理类
def test_match_by_score_guangdong_600():
    """广东物理类600分匹配"""
    resp = api.match_schools(province='广东', score=600, category='物理类')

    # 验证响应结构
    assert '冲' in resp and '稳' in resp and '保' in resp

    # 验证返回数量
    assert len(resp['冲']) >= 3, "冲一档学校不足"
    assert len(resp['稳']) >= 5, "稳一档学校不足"
    assert len(resp['保']) >= 5, "保一档学校不足"

    # 验证分数逻辑 (冲 > 稳 > 保)
    冲_分数 = [s['min_score'] for s in resp['冲']]
    稳_分数 = [s['min_score'] for s in resp['稳']]
    保_分数 = [s['min_score'] for s in resp['保']]

    assert min(冲_分数) > max(稳_分数), "冲档分数应高于稳档"
    assert min(稳_分数) >= max(保_分数), "稳档分数应不低于保档"

# 用例 2: 学校查询 - 中山大学在广东
def test_school_query_sun_yat_sen():
    """查询中山大学在广东的专业分数线"""
    resp = api.get_school_scores('中山大学', '广东')

    assert resp['school_name'] == '中山大学'
    assert len(resp['majors']) >= 20, "专业数量不足"

    # 验证关键字段
    for major in resp['majors']:
        assert 'major_name' in major
        assert 'min_score' in major
        assert major.get('min_score', 0) > 0, "分数线不能为0或空"

# 用例 3: 专业查询 - 计算机专业
def test_major_query_computer():
    """查询计算机专业各校分数线"""
    resp = api.get_majors_by_keyword('计算机', province='广东')

    assert len(resp) >= 10, "计算机专业结果不足"

    # 验证专业名匹配
    for item in resp:
        assert '计算机' in item['major_name'] or 'Computer' in item['major_name']

# 用例 4: 边界条件 - 最高分和最低分
def test_boundary_cases():
    """测试边界条件"""
    # 极高分 (750分)
    resp_high = api.match_schools(province='广东', score=750, category='物理类')
    assert len(resp_high['冲']) == 0, "750分不应有冲一档"

    # 极低分 (400分)
    resp_low = api.match_schools(province='广东', score=400, category='物理类')
    assert len(resp_low['保']) >= 3, "低分应有保底学校"

# 用例 5: 不存在的查询
def test_not_found_cases():
    """测试不存在的情况"""
    # 不存在的省份
    resp = api.match_schools(province='火星', score=600)
    assert resp['error'] or len(resp['冲']) == 0

    # 不存在的学校
    resp = api.get_school_scores('霍格沃茨魔法学校', '广东')
    assert resp.get('error') or len(resp.get('majors', [])) == 0
```

### 3.2 性能测试

| 指标 | 测试方法 | 目标值 | 工具 |
|------|----------|--------|------|
| 响应时间 (P50) | 1000次请求中位数 | ≤ 200ms | wrk/ab |
| 响应时间 (P95) | 1000次请求95分位 | ≤ 500ms | wrk/ab |
| 响应时间 (P99) | 1000次请求99分位 | ≤ 1000ms | wrk/ab |
| QPS | 并发查询能力 | ≥ 100 | wrk |
| 并发稳定性 | 100并发持续1分钟 | 无错误 | wrk |

**性能测试脚本**：
```bash
# 安装 wrk
brew install wrk

# 测试分数匹配接口
wrk -t4 -c100 -d30s --latency \
  "http://159.75.110.157:5000/api/scores/match?province=广东&score=600&category=物理类"

# 验收标准:
# Latency avg < 200ms
# Latency p95 < 500ms
# 无错误响应
```

### 3.3 数据准确性测试

**对比源数据验证**：

```python
# tests/test_data_accuracy.py

def test_accuracy_against_source():
    """对比源 Markdown 数据验证准确性"""
    test_cases = [
        {'school': '中山大学', 'province': '广东', 'major': '计算机类', 'year': 2024},
        {'school': '清华大学', 'province': '北京', 'major': '临床医学', 'year': 2024},
        # ... 更多测试用例
    ]

    for case in test_cases:
        # 从 API 获取
        api_result = api.get_school_scores(case['school'], case['province'])

        # 从源文件获取
        source_result = parse_markdown_source(case['school'], case['province'])

        # 对比验证
        api_major = find_major(api_result, case['major'])
        source_major = find_major(source_result, case['major'])

        assert api_major['min_score'] == source_major['min_score'], \
            f"{case['school']} {case['major']} 分数不一致: API={api_major['min_score']}, Source={source_major['min_score']}"
```

## 四、Dify RAG 测试 (Phase 3)

### 4.1 检索召回率测试

**测试集**：20 个标准问题

```python
# tests/test_dify_rag.py

RAG_TEST_QUESTIONS = [
    # 分数查询类
    ("广东600分物理类能上什么学校？", "中山大学"),
    ("湖南650分历史类推荐哪些学校？", "湖南大学"),

    # 学校分数线查询
    ("中山大学在广东的录取分数线是多少？", "645"),
    ("清华大学的计算机专业要多少分？", "680+"),

    # 专业查询
    ("临床医学专业哪些学校比较好？", "中山大学"),
    ("人工智能专业分数线大概是多少？", "华南理工"),

    # 对比类
    ("中山大学和华南理工哪个更好考？", "分数线"),
]

def test_rag_recall():
    """测试 RAG 检索召回率"""
    recalled = 0
    total = len(RAG_TEST_QUESTIONS)

    for question, expected_keyword in RAG_TEST_QUESTIONS:
        result = dify_query(question)
        answer = result['answer']

        # 检查是否包含预期关键词
        if expected_keyword.lower() in answer.lower():
            recalled += 1

    recall_rate = recalled / total
    assert recall_rate >= 0.90, f"RAG 召回率 {recall_rate:.2%} 低于 90%"
```

### 4.2 检索精度测试

| 问题类型 | 预期结果类型 | 验证方法 |
|----------|-------------|----------|
| 分数查询 | 返回学校列表 | 检查是否为学校名称 |
| 线数查询 | 返回具体分数 | 检查是否为数字 |
| 专业推荐 | 返回专业名称 | 检查是否为专业 |

## 五、综合报告测试 (Phase 4)

### 5.1 报告生成测试

**测试场景**：

```python
# tests/test_report_generation.py

TEST_PROFILES = [
    {
        'name': '高分考生',
        'province': '广东',
        'score': 660,
        'category': '物理类',
        'expectations': {
            '冲_数量': '>= 3',
            '985学校': '>= 2',
            '数据真实性': '100%',
        }
    },
    {
        'name': '中等分考生',
        'province': '广东',
        'score': 550,
        'category': '物理类',
        'expectations': {
            '稳_数量': '>= 5',
            '保_数量': '>= 5',
            '数据真实性': '100%',
        }
    },
    {
        'name': '低分考生',
        'province': '广东',
        'score': 450,
        'category': '物理类',
        'expectations': {
            '冲_数量': '>= 2',
            '保_数量': '>= 3',
            '本地学校': '>= 2',
        }
    },
]

def test_report_generation():
    """测试综合报告生成"""
    for profile in TEST_PROFILES:
        report = generate_report(profile)

        # 验证报告完整性 (6个Tab)
        assert len(report['tabs']) == 6, "报告必须包含6个Tab"

        # 验证 Tab 5 (大学深度研究) 数据来源
        univ_tab = report['tabs'][4]
        assert len(univ_tab['schools']) >= 3, "推荐学校数量不足"

        # 验证数据真实性 (零编造)
        for school in univ_tab['schools']:
            validate_data真实性(school, profile['province'])
```

### 5.2 数据真实性验证

**零编造原则测试**：

```python
def test_no_hallucination():
    """验证报告不编造数据"""
    profile = {'province': '广东', 'score': 600, 'category': '物理类'}
    report = generate_report(profile)

    # 提取报告中所有学校-专业-分数组合
    mentioned = extract_school_major_scores(report)

    # 逐一验证
    for item in mentioned:
        school, major, score = item['school'], item['major'], item['score']

        # 查询数据库验证
        db_result = query_database(school, major, profile['province'])

        # 必须存在于数据库
        assert db_result is not None, f"编造数据: {school} {major} 不存在"

        # 分数必须匹配
        assert abs(db_result['min_score'] - score) <= 5, \
            f"分数不准确: 报告={score}, 数据库={db_result['min_score']}"
```

## 六、端到端测试 (真实场景)

### 6.1 用户场景测试

| 场景 | 操作步骤 | 预期结果 | 验收标准 |
|------|----------|----------|----------|
| 场景1: 分数查询 | 小程序输入省份/分数/选科 → 查询 | 显示可报学校列表 | 响应 < 1s, 数据准确 |
| 场景2: 学校详情 | 点击学校 → 查看专业分数线 | 显示完整专业列表 | 包含 ≥ 20 专业 |
| 场景3: AI 咨询 | Dify 对话 "600分能上什么" | 返回冲稳保建议 | 召回率 ≥ 90% |
| 场景4: 综合报告 | 填问卷 → 生成报告 | 6个Tab完整 | 无编造数据 |
| 场景5: 历年对比 | 查学校 → 看三年趋势 | 显示 2023-2025 数据 | 三年完整 |

### 6.2 压力测试

| 场景 | 并发数 | 持续时间 | 验收标准 |
|------|--------|----------|----------|
| 高峰查询 | 100 用户 | 10 分钟 | P95 < 1s, 错误率 < 1% |
| 报告生成 | 20 并发 | 5 分钟 | 全部成功, 无超时 |

## 七、验收流程

### 7.1 开发完成自检

```bash
# 1. 单元测试
python -m pytest tests/test_scores_conversion.py -v
python -m pytest tests/test_scores_api.py -v

# 2. 性能测试
./scripts/performance_test.sh

# 3. 数据质量检查
python3 data/validate_scores.py --strict

# 4. 端到端测试
python3 tests/e2e_test.py
```

### 7.2 真实场景验证

在以下环境中验证：

1. **开发环境** - 本地 PostgreSQL + 本地 Flask API
2. **测试环境** - 服务器部署 + 真实数据
3. **生产环境** - 小程序真实用户测试

### 7.3 最终验收条件

**全部满足以下条件才能通过验收**：

- [ ] 数据转换完整率 ≥ 99.5%
- [ ] API 响应时间 P95 ≤ 500ms
- [ ] 数据准确率 = 100% (抽样 100 条验证)
- [ ] Dify RAG 召回率 ≥ 90% (20 题测试集)
- [ ] 综合报告零编造 (验证所有提到的数据)
- [ ] 5 个用户场景测试通过
- [ ] 压力测试达标

## 八、失败处理

| 测试项 | 失败阈值 | 处理方式 |
|--------|----------|----------|
| 转换完整率 | < 99% | 检查源文件格式, 修复解析逻辑 |
| API 响应时间 | P95 > 1s | 添加索引, 考虑缓存 |
| 数据准确率 | < 100% | 定位错误数据, 修复源文件或转换逻辑 |
| RAG 召回率 | < 80% | 调整知识库格式, 优化块大小 |
| 综合报告编造 | 任何编造 | 检查数据源, 修复 prompt |

## 九、持续监控

上线后监控指标：

- API 错误率 (目标 < 0.1%)
- API 平均响应时间 (目标 < 200ms)
- 缓存命中率 (目标 > 80%)
- 用户查询满意度 (目标 > 90%)
