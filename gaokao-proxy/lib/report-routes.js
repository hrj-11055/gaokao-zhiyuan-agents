'use strict'

const { query, checkConnection } = require('./pg')
const {
  fetchReportDetail,
  fetchReportHealth,
  fetchReportStats,
  hasReportDataApi,
  listReports,
} = require('./report-data-client')

const DEFAULT_PAGE_SIZE = 20
const MAX_PAGE_SIZE = 100

function parsePagination(query) {
  const page = Math.max(1, Number(query.page) || 1)
  const pageSize = Math.min(MAX_PAGE_SIZE, Math.max(1, Number(query.page_size) || DEFAULT_PAGE_SIZE))
  const offset = (page - 1) * pageSize
  return { page, pageSize, offset }
}

function buildMajorWhere(params) {
  const conditions = []
  const values = []
  let idx = 1

  if (params.category) {
    conditions.push(`category LIKE \$${idx++}`)
    values.push(`${params.category}%`)
  }
  if (params.level) {
    conditions.push(`(data->'layer1_overview'->>'recommendation_level') = \$${idx++}`)
    values.push(params.level)
  }
  if (params.search) {
    conditions.push(`(name ILIKE \$${idx} OR code ILIKE \$${idx})`)
    values.push(`%${params.search}%`)
    idx++
  }
  if (params.min_score) {
    conditions.push(`(data->'layer1_overview'->>'weighted_score')::float >= \$${idx++}`)
    values.push(Number(params.min_score))
  }

  return { conditions, values, idx }
}

function buildUnivWhere(params) {
  const conditions = []
  const values = []
  let idx = 1

  if (params.province) {
    conditions.push(`province LIKE \$${idx++}`)
    values.push(`%${params.province}%`)
  }
  if (params.type) {
    conditions.push(`univ_type = \$${idx++}`)
    values.push(params.type)
  }
  if (params.level) {
    conditions.push(`(data->'layer1_overview'->>'recommendation_level') = \$${idx++}`)
    values.push(params.level)
  }
  if (params.search) {
    conditions.push(`(name ILIKE \$${idx})`)
    values.push(`%${params.search}%`)
    idx++
  }
  if (params.min_score) {
    conditions.push(`(data->'layer1_overview'->>'weighted_score')::float >= \$${idx++}`)
    values.push(Number(params.min_score))
  }

  return { conditions, values, idx }
}

function stripPaidFields(row, hasFullAccess) {
  if (hasFullAccess) return row
  // Free users: layer1_overview + layer2_core summary only
  const data = row.data || {}
  return {
    code: row.code,
    name: row.name,
    category: row.category,
    overview: data.layer1_overview || null,
    summary: data.layer2_core?.summary || null,
  }
}

function stripPaidFieldsUniv(row, hasFullAccess) {
  if (hasFullAccess) return row
  const data = row.data || {}
  return {
    name: row.name,
    province: row.province,
    univ_type: row.univ_type,
    overview: data.layer1_overview || null,
    summary: data.layer2_core?.summary || null,
  }
}

function queryForAccess(params, hasFullAccess) {
  if (hasFullAccess) return params
  const safe = { ...params }
  delete safe.full
  return safe
}

function createReportRoutes(hasFullAccess) {
  return {
    // GET /api/reports/majors?search=&category=&level=&min_score=&page=&page_size=
    async listMajors(req, res) {
      try {
        if (hasReportDataApi()) {
          res.json(await listReports('major', queryForAccess(req.query, hasFullAccess)))
          return
        }

        const { page, pageSize, offset } = parsePagination(req.query)
        const { conditions, values, idx } = buildMajorWhere(req.query)

        const whereClause = conditions.length > 0
          ? `WHERE ${conditions.join(' AND ')}`
          : ''

        const countResult = await query(
          `SELECT COUNT(*) AS total FROM majors ${whereClause}`,
          values
        )
        const total = Number(countResult.rows[0].total)

        const result = await query(
          `SELECT code, name, category, data
           FROM majors ${whereClause}
           ORDER BY (data->'layer1_overview'->>'weighted_score')::float DESC NULLS LAST
           LIMIT \$${idx} OFFSET \$${idx + 1}`,
          [...values, pageSize, offset]
        )

        const rows = result.rows.map(r => stripPaidFields(r, hasFullAccess))

        res.json({
          total,
          page,
          page_size: pageSize,
          data: rows,
        })
      } catch (err) {
        console.error('List majors error:', err.message)
        res.status(500).json({ error: '查询失败' })
      }
    },

    // GET /api/reports/majors/:code
    async getMajor(req, res) {
      try {
        if (hasReportDataApi()) {
          res.json(await fetchReportDetail('major', req.params.code, { full: hasFullAccess }))
          return
        }

        const { code } = req.params
        const result = await query(
          'SELECT code, name, category, data FROM majors WHERE code = $1',
          [code]
        )
        if (result.rows.length === 0) {
          return res.status(404).json({ error: '专业不存在' })
        }
        res.json(stripPaidFields(result.rows[0], hasFullAccess))
      } catch (err) {
        console.error('Get major error:', err.message)
        res.status(500).json({ error: '查询失败' })
      }
    },

    // GET /api/reports/universities?search=&province=&type=&level=&min_score=&page=&page_size=
    async listUniversities(req, res) {
      try {
        if (hasReportDataApi()) {
          res.json(await listReports('university', queryForAccess(req.query, hasFullAccess)))
          return
        }

        const { page, pageSize, offset } = parsePagination(req.query)
        const { conditions, values, idx } = buildUnivWhere(req.query)

        const whereClause = conditions.length > 0
          ? `WHERE ${conditions.join(' AND ')}`
          : ''

        const countResult = await query(
          `SELECT COUNT(*) AS total FROM universities ${whereClause}`,
          values
        )
        const total = Number(countResult.rows[0].total)

        const result = await query(
          `SELECT name, province, univ_type, data
           FROM universities ${whereClause}
           ORDER BY (data->'layer1_overview'->>'weighted_score')::float DESC NULLS LAST
           LIMIT \$${idx} OFFSET \$${idx + 1}`,
          [...values, pageSize, offset]
        )

        const rows = result.rows.map(r => stripPaidFieldsUniv(r, hasFullAccess))

        res.json({
          total,
          page,
          page_size: pageSize,
          data: rows,
        })
      } catch (err) {
        console.error('List universities error:', err.message)
        res.status(500).json({ error: '查询失败' })
      }
    },

    // GET /api/reports/universities/:name
    async getUniversity(req, res) {
      try {
        if (hasReportDataApi()) {
          res.json(await fetchReportDetail('university', req.params.name, { full: hasFullAccess }))
          return
        }

        const name = decodeURIComponent(req.params.name)
        const result = await query(
          'SELECT name, province, univ_type, data FROM universities WHERE name = $1',
          [name]
        )
        if (result.rows.length === 0) {
          return res.status(404).json({ error: '院校不存在' })
        }
        res.json(stripPaidFieldsUniv(result.rows[0], hasFullAccess))
      } catch (err) {
        console.error('Get university error:', err.message)
        res.status(500).json({ error: '查询失败' })
      }
    },

    // GET /api/reports/stats
    async getStats(_req, res) {
      try {
        if (hasReportDataApi()) {
          res.json(await fetchReportStats())
          return
        }

        const result = await query('SELECT * FROM stats_overview')
        const stats = {}
        for (const row of result.rows) {
          stats[row.table_name] = {
            total: Number(row.total_count),
            green: Number(row.green_count),
            yellow: Number(row.yellow_count),
            red: Number(row.red_count),
            avg_score: row.avg_score ? Number(row.avg_score).toFixed(2) : '0.00',
          }
        }
        res.json(stats)
      } catch (err) {
        console.error('Get stats error:', err.message)
        res.status(500).json({ error: '查询失败' })
      }
    },

    // GET /api/reports/health
    async healthCheck(_req, res) {
      if (hasReportDataApi()) {
        try {
          res.json(await fetchReportHealth())
          return
        } catch (err) {
          res.json({
            status: 'degraded',
            postgres: 'disconnected',
            data_api: 'failed',
            error: err.message,
          })
          return
        }
      }

      const pgOk = await checkConnection()
      res.json({
        status: pgOk ? 'ok' : 'degraded',
        postgres: pgOk ? 'connected' : 'disconnected',
      })
    },
  }
}

module.exports = { createReportRoutes }
