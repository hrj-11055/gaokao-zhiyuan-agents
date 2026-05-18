'use strict'

const { Pool } = require('pg')

const pool = new Pool({
  host: process.env.PG_HOST || '127.0.0.1',
  port: Number(process.env.PG_PORT || 5432),
  database: process.env.PG_DATABASE || 'gaokao_db',
  user: process.env.PG_USER || 'postgres',
  password: process.env.PG_PASSWORD || '',
  max: 5,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 3000,
})

pool.on('error', (err) => {
  console.error('PG pool error:', err.message)
})

async function query(text, params) {
  const start = Date.now()
  const res = await pool.query(text, params)
  const duration = Date.now() - start
  if (duration > 500) {
    console.log(`[PG slow] ${text.slice(0, 80)} (${duration}ms, ${res.rowCount} rows)`)
  }
  return res
}

async function getClient() {
  return pool.connect()
}

async function checkConnection() {
  try {
    const res = await pool.query('SELECT 1 AS ok')
    return res.rows[0].ok === 1
  } catch {
    return false
  }
}

module.exports = { query, getClient, checkConnection, pool }
