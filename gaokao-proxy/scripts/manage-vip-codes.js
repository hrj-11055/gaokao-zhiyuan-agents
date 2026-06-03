#!/usr/bin/env node
'use strict'

const crypto = require('crypto')
const fs = require('fs')
const path = require('path')
const Database = require('better-sqlite3')
require('dotenv').config({ path: path.join(__dirname, '..', '.env') })

const DEFAULT_DB_PATH = path.join(__dirname, '..', 'data', 'gaokao-commerce.sqlite')
const CODE_ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'

function usage(exitCode = 0) {
  const text = `
Usage:
  npm run vip-codes -- generate --count 20 --prefix FG --max-uses 1 --expires-days 30
  npm run vip-codes -- list [--status active] [--limit 50] [--json]
  npm run vip-codes -- show --code FG-202605-ABC123 [--json]
  npm run vip-codes -- disable --code FG-202605-ABC123
  npm run vip-codes -- enable --code FG-202605-ABC123

Options:
  --db <path>           SQLite database path. Defaults to COMMERCE_DB_PATH or gaokao-proxy/data/gaokao-commerce.sqlite.
  --count <n>           Number of codes to generate. Default: 1.
  --prefix <text>       Code prefix. Default: FG.
  --max-uses <n>        Maximum redemptions per code. Omit for unlimited.
  --expires-days <n>    Days until expiration. Omit for no expiration.
  --dry-run             Print generated codes without writing to the database.
  --json                Print machine-readable JSON.
`
  console.log(text.trim())
  process.exit(exitCode)
}

function parseArgs(argv) {
  const [command, ...rest] = argv
  const options = { _: [] }

  for (let index = 0; index < rest.length; index += 1) {
    const arg = rest[index]
    if (!arg.startsWith('--')) {
      options._.push(arg)
      continue
    }
    const key = arg.slice(2)
    if (['dry-run', 'json', 'help'].includes(key)) {
      options[key] = true
      continue
    }
    const value = rest[index + 1]
    if (value === undefined || value.startsWith('--')) {
      throw new Error(`Missing value for --${key}`)
    }
    options[key] = value
    index += 1
  }

  return { command, options }
}

function asPositiveInteger(value, fallback, name) {
  if (value === undefined || value === null || value === '') return fallback
  const number = Number(value)
  if (!Number.isInteger(number) || number <= 0) {
    throw new Error(`${name} must be a positive integer`)
  }
  return number
}

function normalizeCode(code) {
  return String(code || '').trim().toUpperCase()
}

function monthStamp(date = new Date()) {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  return `${date.getFullYear()}${month}`
}

function randomSuffix(length = 6) {
  let result = ''
  while (result.length < length) {
    const byte = crypto.randomBytes(1)[0]
    if (byte >= CODE_ALPHABET.length * Math.floor(256 / CODE_ALPHABET.length)) continue
    result += CODE_ALPHABET[byte % CODE_ALPHABET.length]
  }
  return result
}

function createCode(prefix) {
  const cleanPrefix = String(prefix || 'FG')
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 12) || 'FG'
  return `${cleanPrefix}-${monthStamp()}-${randomSuffix(6)}`
}

function openDb(dbPath) {
  if (dbPath !== ':memory:') {
    fs.mkdirSync(path.dirname(dbPath), { recursive: true })
  }
  const db = new Database(dbPath)
  db.pragma('journal_mode = WAL')
  db.exec(`
    CREATE TABLE IF NOT EXISTS vip_invite_codes (
      code TEXT PRIMARY KEY,
      status TEXT NOT NULL,
      max_uses INTEGER,
      used_count INTEGER NOT NULL DEFAULT 0,
      created_at INTEGER NOT NULL,
      expires_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS vip_code_redemptions (
      id TEXT PRIMARY KEY,
      code TEXT NOT NULL,
      user_id TEXT NOT NULL,
      redeemed_at INTEGER NOT NULL,
      UNIQUE(code, user_id)
    );
  `)
  return db
}

function resolveDbPath(options) {
  return options.db || process.env.COMMERCE_DB_PATH || DEFAULT_DB_PATH
}

function toIso(ms) {
  if (!ms) return ''
  return new Date(ms).toISOString()
}

function codeRowToOutput(row) {
  return {
    code: row.code,
    status: row.status,
    maxUses: row.max_uses === null || row.max_uses === undefined ? null : row.max_uses,
    usedCount: row.used_count,
    createdAt: toIso(row.created_at),
    expiresAt: toIso(row.expires_at),
  }
}

function printTable(rows) {
  if (rows.length === 0) {
    console.log('No vip codes found.')
    return
  }

  console.log(['code', 'status', 'used/max', 'expires_at'].join('\t'))
  for (const row of rows) {
    const max = row.maxUses === null ? 'unlimited' : row.maxUses
    console.log([row.code, row.status, `${row.usedCount}/${max}`, row.expiresAt || '-'].join('\t'))
  }
}

function generateCodes(options) {
  const count = asPositiveInteger(options.count, 1, 'count')
  const maxUses = options['max-uses'] === undefined ? null : asPositiveInteger(options['max-uses'], null, 'max-uses')
  const expiresDays = options['expires-days'] === undefined ? null : asPositiveInteger(options['expires-days'], null, 'expires-days')
  const createdAt = Date.now()
  const expiresAt = expiresDays ? createdAt + expiresDays * 24 * 60 * 60 * 1000 : null
  const codes = new Set()

  while (codes.size < count) {
    codes.add(createCode(options.prefix || 'FG'))
  }

  const rows = [...codes].map((code) => ({
    code,
    status: 'active',
    maxUses,
    usedCount: 0,
    createdAt: toIso(createdAt),
    expiresAt: toIso(expiresAt),
  }))

  if (!options['dry-run']) {
    const db = openDb(resolveDbPath(options))
    try {
      const insert = db.prepare(`
        INSERT INTO vip_invite_codes (code, status, max_uses, used_count, created_at, expires_at)
        VALUES (@code, 'active', @maxUses, 0, @createdAt, @expiresAt)
      `)
      const tx = db.transaction((items) => {
        for (const code of items) {
          insert.run({ code, maxUses, createdAt, expiresAt })
        }
      })
      tx([...codes])
    } finally {
      db.close()
    }
  }

  if (options.json) {
    console.log(JSON.stringify(rows, null, 2))
    return
  }
  printTable(rows)
  console.log(`\nComma list: ${[...codes].join(',')}`)
}

function listCodes(options) {
  const db = openDb(resolveDbPath(options))
  try {
    const limit = asPositiveInteger(options.limit, 50, 'limit')
    const status = options.status ? String(options.status).trim() : ''
    const rows = status
      ? db.prepare(`
          SELECT * FROM vip_invite_codes
          WHERE status = ?
          ORDER BY created_at DESC
          LIMIT ?
        `).all(status, limit)
      : db.prepare(`
          SELECT * FROM vip_invite_codes
          ORDER BY created_at DESC
          LIMIT ?
        `).all(limit)
    const output = rows.map(codeRowToOutput)
    if (options.json) {
      console.log(JSON.stringify(output, null, 2))
    } else {
      printTable(output)
    }
  } finally {
    db.close()
  }
}

function showCode(options) {
  const code = normalizeCode(options.code)
  if (!code) throw new Error('Missing --code')

  const db = openDb(resolveDbPath(options))
  try {
    const row = db.prepare('SELECT * FROM vip_invite_codes WHERE code = ?').get(code)
    if (!row) throw new Error(`VIP code not found: ${code}`)
    const redemptions = db.prepare(`
      SELECT code, user_id AS userId, redeemed_at AS redeemedAt
      FROM vip_code_redemptions
      WHERE code = ?
      ORDER BY redeemed_at DESC
    `).all(code).map((item) => ({
      code: item.code,
      userId: item.userId,
      redeemedAt: toIso(item.redeemedAt),
    }))
    const output = { ...codeRowToOutput(row), redemptions }
    if (options.json) {
      console.log(JSON.stringify(output, null, 2))
      return
    }
    printTable([output])
    if (redemptions.length > 0) {
      console.log('\nredemptions:')
      for (const item of redemptions) {
        console.log(`${item.redeemedAt}\t${item.userId}`)
      }
    }
  } finally {
    db.close()
  }
}

function setCodeStatus(options, status) {
  const code = normalizeCode(options.code)
  if (!code) throw new Error('Missing --code')

  const db = openDb(resolveDbPath(options))
  try {
    const result = db.prepare('UPDATE vip_invite_codes SET status = ? WHERE code = ?').run(status, code)
    if (result.changes === 0) throw new Error(`VIP code not found: ${code}`)
    const row = codeRowToOutput(db.prepare('SELECT * FROM vip_invite_codes WHERE code = ?').get(code))
    if (options.json) {
      console.log(JSON.stringify(row, null, 2))
    } else {
      printTable([row])
    }
  } finally {
    db.close()
  }
}

function main() {
  const { command, options } = parseArgs(process.argv.slice(2))
  if (!command || command === 'help' || command === '--help' || options.help) usage(0)

  switch (command) {
    case 'generate':
      generateCodes(options)
      break
    case 'list':
      listCodes(options)
      break
    case 'show':
      showCode(options)
      break
    case 'disable':
      setCodeStatus(options, 'inactive')
      break
    case 'enable':
      setCodeStatus(options, 'active')
      break
    default:
      throw new Error(`Unknown command: ${command}`)
  }
}

try {
  main()
} catch (err) {
  console.error(err.message)
  usage(1)
}
