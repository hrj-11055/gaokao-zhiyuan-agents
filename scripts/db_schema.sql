-- ============================================================================
-- 高考志愿填报项目 - 报告数据库结构
-- 数据库: gaokao_db
-- 说明: 存储专业和院校评估报告的 JSON 数据
-- ============================================================================

-- 创建数据库（如果不存在）
-- CREATE DATABASE gaokao_db;

-- 连接到 gaokao_db 后执行以下脚本

-- ============================================================================
-- 1. 专业报告表 (majors)
-- ============================================================================
CREATE TABLE IF NOT EXISTS majors (
    -- 主键和基本信息
    code TEXT PRIMARY KEY,                         -- 专业代码（6位）
    name TEXT NOT NULL,                            -- 专业名称
    category TEXT NOT NULL,                        -- 学科门类（01哲学、02经济学等）

    -- JSON 数据（4层结构）
    data JSONB NOT NULL,                           -- 完整报告数据

    -- 元数据
    version TEXT DEFAULT '2.0.0',                  -- Schema 版本
    source_file TEXT,                             -- 原始文件名
    word_count INTEGER DEFAULT 0,                  -- 字数统计

    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 约束
    CONSTRAINT majors_name_not_empty CHECK (length(trim(name)) > 0)
);

-- 专业表注释
COMMENT ON TABLE majors IS '专业评估报告表';
COMMENT ON COLUMN majors.code IS '6位专业代码，如 080701';
COMMENT ON COLUMN majors.category IS '学科门类代码+名称';
COMMENT ON COLUMN majors.data IS 'JSONB格式的完整报告数据，包含 layer1_overview, layer2_core, layer3_detail, layer4_supplement';

-- ============================================================================
-- 2. 院校报告表 (universities)
-- ============================================================================
CREATE TABLE IF NOT EXISTS universities (
    -- 主键和基本信息
    name TEXT PRIMARY KEY,                         -- 院校名称（标准化）
    name_pinyin TEXT,                             -- 拼音（用于搜索）
    short_name TEXT,                              -- 简称
    english_name TEXT,                            -- 英文名

    -- 基本属性（便于快速查询）
    province TEXT,                                -- 所在省份
    city TEXT,                                    -- 所在城市
    univ_type TEXT,                               -- 院校类型（985/211/双一流/公办/民办/中外合作/独立学院）
    tier TEXT,                                    -- 层次（本科/专科）

    -- JSON 数据（4层结构）
    data JSONB NOT NULL,                           -- 完整报告数据

    -- 元数据
    version TEXT DEFAULT '2.0.0',                  -- Schema 版本
    source_file TEXT,                             -- 原始文件名
    word_count INTEGER DEFAULT 0,                  -- 字数统计

    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 约束
    CONSTRAINT univ_name_not_empty CHECK (length(trim(name)) > 0)
);

-- 院校表注释
COMMENT ON TABLE universities IS '院校评估报告表';
COMMENT ON COLUMN universities.name IS '院校标准名称';
COMMENT ON COLUMN universities.univ_type IS '985/211/双一流/公办/民办/中外合作办学/独立学院';
COMMENT ON COLUMN universities.data IS 'JSONB格式的完整报告数据';

-- ============================================================================
-- 3. JSON 数据结构验证（使用 JSONB 约束）
-- ============================================================================

-- 确保 data 字段包含必要的层
ALTER TABLE majors
ADD CONSTRAINT majors_data_structure
CHECK (
    data ? 'layer1_overview' AND
    data ? 'layer2_core' AND
    data ? 'layer3_detail'
);

ALTER TABLE universities
ADD CONSTRAINT universities_data_structure
CHECK (
    data ? 'layer1_overview' AND
    data ? 'layer2_core' AND
    data ? 'layer3_detail'
);

-- ============================================================================
-- 4. 索引设计（查询优化）
-- ============================================================================

-- 专业表索引
CREATE INDEX idx_majors_category ON majors(category);
CREATE INDEX idx_majors_name ON majors USING GIN (to_tsvector('simple', name));
CREATE INDEX idx_majors_data_gin ON majors USING GIN (data);
CREATE INDEX idx_majors_layer1_gin ON majors USING GIN (data->'layer1_overview');

-- 支持按推荐等级查询
CREATE INDEX idx_majors_recommendation ON majors
    USING GIN ((data->'layer1_overview'->>'recommendation_level'));

-- 支持按加权分数范围查询
CREATE INDEX idx_majors_score ON majors
    ((data->'layer1_overview'->>'weighted_score'));

-- 院校表索引
CREATE INDEX idx_univ_province ON universities(province);
CREATE INDEX idx_univ_type ON universities(univ_type);
CREATE INDEX idx_univ_name_gin ON universities USING GIN (to_tsvector('simple', name));
CREATE INDEX idx_univ_data_gin ON universities USING GIN (data);
CREATE INDEX idx_univ_layer1_gin ON universities USING GIN (data->'layer1_overview');

-- 支持按推荐等级查询
CREATE INDEX idx_univ_recommendation ON universities
    USING GIN ((data->'layer1_overview'->>'recommendation_level'));

-- 支持按加权分数范围查询
CREATE INDEX idx_univ_score ON universities
    ((data->'layer1_overview'->>'weighted_score'));

-- ============================================================================
-- 5. 视图（免费用户视图）
-- ============================================================================
CREATE OR REPLACE VIEW majors_free AS
SELECT
    code,
    name,
    category,
    data->'layer1_overview' as overview,
    data->'layer2_core'->>'summary' as summary,
    (data->'layer1_overview'->>'weighted_score')::float as score
FROM majors;

CREATE OR REPLACE VIEW universities_free AS
SELECT
    name,
    province,
    univ_type,
    data->'layer1_overview' as overview,
    data->'layer2_core'->>'summary' as summary,
    (data->'layer1_overview'->>'weighted_score')::float as score
FROM universities;

COMMENT ON VIEW majors_free IS '免费用户可访问的专业数据视图';
COMMENT ON VIEW universities_free IS '免费用户可访问的院校数据视图';

-- ============================================================================
-- 6. 统计视图
-- ============================================================================
CREATE OR REPLACE VIEW stats_overview AS
SELECT
    'majors' as table_name,
    COUNT(*) as total_count,
    COUNT(*) FILTER (WHERE (data->'layer1_overview'->>'recommendation_level') = 'green') as green_count,
    COUNT(*) FILTER (WHERE (data->'layer1_overview'->>'recommendation_level') = 'yellow') as yellow_count,
    COUNT(*) FILTER (WHERE (data->'layer1_overview'->>'recommendation_level') = 'red') as red_count,
    AVG((data->'layer1_overview'->>'weighted_score')::float) as avg_score
FROM majors
UNION ALL
SELECT
    'universities' as table_name,
    COUNT(*) as total_count,
    COUNT(*) FILTER (WHERE (data->'layer1_overview'->>'recommendation_level') = 'green') as green_count,
    COUNT(*) FILTER (WHERE (data->'layer1_overview'->>'recommendation_level') = 'yellow') as yellow_count,
    COUNT(*) FILTER (WHERE (data->'layer1_overview'->>'recommendation_level') = 'red') as red_count,
    AVG((data->'layer1_overview'->>'weighted_score')::float) as avg_score
FROM universities;

COMMENT ON VIEW stats_overview IS '数据统计概览视图';

-- ============================================================================
-- 7. 触发器（自动更新 updated_at）
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_majors_updated_at
    BEFORE UPDATE ON majors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_universities_updated_at
    BEFORE UPDATE ON universities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 8. 全文搜索配置
-- ============================================================================
-- 创建全文搜索配置
CREATE TEXT SEARCH CONFIGURATION simple_chinese (COPY = simple);

-- 全文搜索函数
CREATE OR REPLACE FUNCTION majors_search(query TEXT)
RETURNS TABLE(code TEXT, name TEXT, category TEXT, overview JSONB) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.code,
        m.name,
        m.category,
        m.data->'layer1_overview' as overview
    FROM majors m
    WHERE
        m.name % query OR
        m.code % query OR
        to_tsvector('simple', m.data->'layer3_detail'->'module1_image'->>'raw_content') @@ plainto_tsquery('simple', query)
    ORDER BY similarity(m.name, query) DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION universities_search(query TEXT)
RETURNS TABLE(name TEXT, province TEXT, univ_type TEXT, overview JSONB) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.name,
        u.province,
        u.univ_type,
        u.data->'layer1_overview' as overview
    FROM universities u
    WHERE
        u.name % query OR
        to_tsvector('simple', u.data->'layer3_detail'->'module1_academic_capital'->>'raw_content') @@ plainto_tsquery('simple', query)
    ORDER BY similarity(u.name, query) DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 9. 用户权限配置（根据需要调整）
-- ============================================================================
-- 创建只读用户（供 API 查询使用）
-- CREATE USER gaokao_read WITH PASSWORD 'your_password';
-- GRANT CONNECT ON DATABASE gaokao_db TO gaokao_read;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO gaokao_read;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO gaokao_read;

-- 创建读写用户（供数据导入使用）
-- CREATE USER gaokao_write WITH PASSWORD 'your_password';
-- GRANT CONNECT ON DATABASE gaokao_db TO gaokao_write;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO gaokao_write;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO gaokao_write;

-- ============================================================================
-- 10. 扩展性：预留字段（便于后期扩展）
-- ============================================================================
-- 为专业表添加标签字段（便于分类和推荐）
ALTER TABLE majors ADD COLUMN IF NOT EXISTS tags TEXT[];
CREATE INDEX idx_majors_tags ON majors USING GIN (tags);

-- 为院校表添加标签字段
ALTER TABLE universities ADD COLUMN IF NOT EXISTS tags TEXT[];
CREATE INDEX idx_univ_tags ON universities USING GIN (tags);

-- 为专业表添加热门度字段
ALTER TABLE majors ADD COLUMN IF NOT EXISTS popularity INTEGER DEFAULT 0;
CREATE INDEX idx_majors_popularity ON majors(popularity DESC);

-- 为院校表添加热门度字段
ALTER TABLE universities ADD COLUMN IF NOT EXISTS popularity INTEGER DEFAULT 0;
CREATE INDEX idx_univ_popularity ON universities(popularity DESC);

-- ============================================================================
-- 11. 数据质量检查函数
-- ============================================================================
CREATE OR REPLACE FUNCTION check_data_quality()
RETURNS TABLE(
    table_name TEXT,
    total_records BIGINT,
    null_layer1 BIGINT,
    null_layer2 BIGINT,
    null_layer3 BIGINT,
    empty_content BIGINT
) AS $$
BEGIN
    -- 检查专业表
    RETURN QUERY
    SELECT
        'majors'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(*) FILTER (WHERE data->'layer1_overview' IS NULL)::BIGINT,
        COUNT(*) FILTER (WHERE data->'layer2_core' IS NULL)::BIGINT,
        COUNT(*) FILTER (WHERE data->'layer3_detail' IS NULL)::BIGINT,
        COUNT(*) FILTER (WHERE (SELECT count(*) FROM jsonb_object_keys(data->'layer3_detail')) = 0)::BIGINT
    FROM majors
    UNION ALL
    -- 检查院校表
    SELECT
        'universities'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(*) FILTER (WHERE data->'layer1_overview' IS NULL)::BIGINT,
        COUNT(*) FILTER (WHERE data->'layer2_core' IS NULL)::BIGINT,
        COUNT(*) FILTER (WHERE data->'layer3_detail' IS NULL)::BIGINT,
        COUNT(*) FILTER (WHERE (SELECT count(*) FROM jsonb_object_keys(data->'layer3_detail')) = 0)::BIGINT
    FROM universities;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_data_quality() IS '检查数据质量：统计缺失层级和空内容的记录数';

-- ============================================================================
-- 初始化完成提示
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE '数据库结构创建完成！';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE '下一步：';
    RAISE NOTICE '1. 导入数据：使用 scripts/import_reports_to_pg.py';
    RAISE NOTICE '2. 验证数据：SELECT * FROM check_data_quality()';
    RAISE NOTICE '3. 启动 API 服务：cd gaokao-proxy && npm start';
    RAISE NOTICE '============================================================================';
END $$;
