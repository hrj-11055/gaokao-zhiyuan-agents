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
  npm run commerce-ops -- lookup --user-id u_xxx [--json]
  npm run commerce-ops -- lookup --openid openid_xxx [--json]
  npm run commerce-ops -- lookup --order-id ord_xxx [--json]
  npm run commerce-ops -- lookup --out-trade-no GKxxx [--json]
  npm run commerce-ops -- lookup --transaction-id 420xxx [--json]
  npm run commerce-ops -- activate-membership --user-id u_xxx --operator name --reason "paid order verified"
  npm run commerce-ops -- activate-membership --openid openid_xxx --operator name --reason "paid order verified"
  npm run commerce-ops -- issue-code --recipient openid_or_note --operator name --reason "compensation"

Options:
  --db <path>           SQLite database path. Defaults to COMMERCE_DB_PATH or gaokao-proxy/data/gaokao-commerce.sqlite.
  --operator <name>     Support operator name or ticket owner.
  --reason <text>       Required for write operations; include ticket/order evidence.
  --recipient <text>    Recipient marker for a compensation invite code.
  --prefix <text>       Compensation code prefix. Default: COMP.
  --expires-days <n>    Days until code expiration. Default: 30.
  --dry-run             Show the write result without committing.
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

function resolveDbPath(options) {
  return options.db || process.env.COMMERCE_DB_PATH || DEFAULT_DB_PATH
}

function openDb(dbPath, { ensureSupport = false, ensureVip = false } = {}) {
  if (dbPath !== ':memory:') {
    fs.mkdirSync(path.dirname(dbPath), { recursive: true })
  }
  const db = new Database(dbPath)
  db.pragma('journal_mode = WAL')
  db.pragma('foreign_keys = ON')
  if (ensureSupport) {
    db.exec(`
      CREATE TABLE IF NOT EXISTS support_operations (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        operator TEXT NOT NULL,
        reason TEXT NOT NULL,
        target_user_id TEXT,
        target_openid TEXT,
        result_json TEXT,
        created_at INTEGER NOT NULL
      );
    `)
  }
  if (ensureVip) {
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
  }
  return db
}

function tableExists(db, name) {
  return Boolean(db.prepare(`
    SELECT name FROM sqlite_master
    WHERE type = 'table' AND name = ?
  `).get(name))
}

function toIso(ms) {
  if (!ms) return ''
  return new Date(ms).toISOString()
}

function operationId() {
  return `sup_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`
}

function normalizeCodePrefix(prefix) {
  return String(prefix || 'COMP')
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 12) || 'COMP'
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
  return `${normalizeCodePrefix(prefix)}-${monthStamp()}-${randomSuffix(6)}`
}

function asPositiveInteger(value, fallback, name) {
  if (value === undefined || value === null || value === '') return fallback
  const number = Number(value)
  if (!Number.isInteger(number) || number <= 0) {
    throw new Error(`${name} must be a positive integer`)
  }
  return number
}

function requireWriteAudit(options) {
  const operator = String(options.operator || '').trim()
  const reason = String(options.reason || '').trim()
  if (!operator) throw new Error('Missing --operator for write operation')
  if (!reason) throw new Error('Missing --reason for write operation')
  return { operator, reason }
}

function rowToUser(row) {
  if (!row) return null
  return {
    userId: row.id,
    openid: row.openid,
    unionid: row.unionid || '',
    invitedByUserId: row.invited_by_user_id || '',
    profileCompletedAt: toIso(row.profile_completed_at),
    createdAt: toIso(row.created_at),
    updatedAt: toIso(row.updated_at),
  }
}

function rowToOrder(row) {
  if (!row) return null
  return {
    orderId: row.id,
    userId: row.user_id,
    outTradeNo: row.out_trade_no,
    transactionId: row.transaction_id || '',
    amountCents: row.amount_cents,
    status: row.status,
    prepayId: row.prepay_id || '',
    paidAt: toIso(row.paid_at),
    createdAt: toIso(row.created_at),
    updatedAt: toIso(row.updated_at),
  }
}

function rowToOperation(row) {
  return {
    id: row.id,
    type: row.type,
    operator: row.operator,
    reason: row.reason,
    targetUserId: row.target_user_id || '',
    targetOpenid: row.target_openid || '',
    result: row.result_json ? JSON.parse(row.result_json) : null,
    createdAt: toIso(row.created_at),
  }
}

function getMembershipStatus(db, userId) {
  const membership = db.prepare('SELECT * FROM memberships WHERE user_id = ?').get(userId)
  const inviteRow = db.prepare(`
    SELECT COUNT(*) AS count
    FROM invites
    WHERE inviter_user_id = ? AND status = 'effective'
  `).get(userId) || { count: 0 }
  const downloadRow = db.prepare(`
    SELECT COUNT(*) AS count
    FROM deep_report_downloads
    WHERE user_id = ?
  `).get(userId) || { count: 0 }
  const downloadLimit = Number(process.env.MEMBERSHIP_DEEP_REPORT_DOWNLOAD_LIMIT || 10)
  const active = membership?.status === 'active'
  return {
    status: active ? 'active' : 'inactive',
    source: active ? membership.source : '',
    unlockedAt: active ? toIso(membership.unlocked_at) : '',
    expiresAt: active ? toIso(membership.expires_at) : '',
    invite: {
      effectiveCount: inviteRow.count || 0,
      requiredCount: Number(process.env.MEMBERSHIP_INVITE_REQUIRED || 5),
    },
    downloadQuota: {
      used: downloadRow.count || 0,
      limit: Number.isFinite(downloadLimit) ? downloadLimit : 10,
      remaining: Math.max(0, (Number.isFinite(downloadLimit) ? downloadLimit : 10) - (downloadRow.count || 0)),
    },
  }
}

function findLookupTarget(db, options) {
  if (options['user-id']) {
    const user = db.prepare('SELECT * FROM users WHERE id = ?').get(options['user-id'])
    if (!user) throw new Error(`User not found: ${options['user-id']}`)
    return { user, selectedOrder: null }
  }
  if (options.openid) {
    const user = db.prepare('SELECT * FROM users WHERE openid = ?').get(options.openid)
    if (!user) throw new Error(`User not found for openid: ${options.openid}`)
    return { user, selectedOrder: null }
  }
  if (options['order-id']) {
    const order = db.prepare('SELECT * FROM payment_orders WHERE id = ?').get(options['order-id'])
    if (!order) throw new Error(`Order not found: ${options['order-id']}`)
    return {
      user: db.prepare('SELECT * FROM users WHERE id = ?').get(order.user_id),
      selectedOrder: order,
    }
  }
  if (options['out-trade-no']) {
    const order = db.prepare('SELECT * FROM payment_orders WHERE out_trade_no = ?').get(options['out-trade-no'])
    if (!order) throw new Error(`Order not found for out_trade_no: ${options['out-trade-no']}`)
    return {
      user: db.prepare('SELECT * FROM users WHERE id = ?').get(order.user_id),
      selectedOrder: order,
    }
  }
  if (options['transaction-id']) {
    const order = db.prepare('SELECT * FROM payment_orders WHERE transaction_id = ?').get(options['transaction-id'])
    if (!order) throw new Error(`Order not found for transaction_id: ${options['transaction-id']}`)
    return {
      user: db.prepare('SELECT * FROM users WHERE id = ?').get(order.user_id),
      selectedOrder: order,
    }
  }
  throw new Error('Provide one lookup selector: --user-id, --openid, --order-id, --out-trade-no, or --transaction-id')
}

function buildLookup(db, options) {
  const { user, selectedOrder } = findLookupTarget(db, options)
  if (!user) throw new Error('Order exists but linked user is missing')
  const orderRows = selectedOrder
    ? [selectedOrder]
    : db.prepare(`
        SELECT * FROM payment_orders
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
      `).all(user.id)
  const operations = tableExists(db, 'support_operations')
    ? db.prepare(`
        SELECT * FROM support_operations
        WHERE target_user_id = ? OR target_openid = ?
        ORDER BY created_at DESC
        LIMIT 20
      `).all(user.id, user.openid)
    : []

  return {
    user: rowToUser(user),
    membership: getMembershipStatus(db, user.id),
    orders: orderRows.map(rowToOrder),
    supportOperations: operations.map(rowToOperation),
  }
}

function printLookup(output) {
  console.log(`user\t${output.user.userId}\topenid=${output.user.openid}`)
  console.log(`membership\t${output.membership.status}\tsource=${output.membership.source || '-'}`)
  if (output.orders.length === 0) {
    console.log('orders\t-')
  } else {
    console.log('orders:')
    for (const order of output.orders) {
      console.log([
        order.orderId,
        order.status,
        `amount=${order.amountCents}`,
        `out_trade_no=${order.outTradeNo}`,
        `transaction_id=${order.transactionId || '-'}`,
        `paid_at=${order.paidAt || '-'}`,
      ].join('\t'))
    }
  }
  if (output.supportOperations.length > 0) {
    console.log('support_operations:')
    for (const op of output.supportOperations) {
      console.log([op.createdAt, op.type, op.operator, op.reason].join('\t'))
    }
  }
}

function runLookup(options) {
  const db = openDb(resolveDbPath(options))
  try {
    const output = buildLookup(db, options)
    if (options.json) {
      console.log(JSON.stringify(output, null, 2))
      return
    }
    printLookup(output)
  } finally {
    db.close()
  }
}

function resolveUserForWrite(db, options) {
  if (options['user-id']) {
    const user = db.prepare('SELECT * FROM users WHERE id = ?').get(options['user-id'])
    if (!user) throw new Error(`User not found: ${options['user-id']}`)
    return user
  }
  if (options.openid) {
    const user = db.prepare('SELECT * FROM users WHERE openid = ?').get(options.openid)
    if (!user) throw new Error(`User not found for openid: ${options.openid}`)
    return user
  }
  throw new Error('Provide --user-id or --openid')
}

function recordOperation(db, { type, operator, reason, userId = '', openid = '', result }) {
  const row = {
    id: operationId(),
    type,
    operator,
    reason,
    userId,
    openid,
    resultJson: JSON.stringify(result || {}),
    createdAt: Date.now(),
  }
  db.prepare(`
    INSERT INTO support_operations (
      id, type, operator, reason, target_user_id, target_openid, result_json, created_at
    ) VALUES (
      @id, @type, @operator, @reason, @userId, @openid, @resultJson, @createdAt
    )
  `).run(row)
  return rowToOperation(db.prepare('SELECT * FROM support_operations WHERE id = ?').get(row.id))
}

function runActivateMembership(options) {
  const { operator, reason } = requireWriteAudit(options)
  const db = openDb(resolveDbPath(options), { ensureSupport: true })
  try {
    const user = resolveUserForWrite(db, options)
    const activatedAt = Date.now()
    const tx = db.transaction(() => {
      db.prepare(`
        INSERT INTO memberships (user_id, status, source, unlocked_at, expires_at)
        VALUES (?, 'active', 'support_manual', ?, NULL)
        ON CONFLICT(user_id) DO UPDATE SET
          status = 'active',
          source = CASE
            WHEN memberships.status = 'active' THEN memberships.source
            ELSE excluded.source
          END,
          unlocked_at = COALESCE(memberships.unlocked_at, excluded.unlocked_at),
          expires_at = NULL
      `).run(user.id, activatedAt)
      const membership = getMembershipStatus(db, user.id)
      const operation = recordOperation(db, {
        type: 'activate_membership',
        operator,
        reason,
        userId: user.id,
        openid: user.openid,
        result: { membership },
      })
      return { user: rowToUser(user), membership, operation }
    })

    const output = options['dry-run']
      ? { user: rowToUser(user), membership: getMembershipStatus(db, user.id), dryRun: true }
      : tx()
    if (options.json) {
      console.log(JSON.stringify(output, null, 2))
      return
    }
    console.log(`membership\t${output.membership.status}\tsource=${output.membership.source}`)
    if (output.operation) console.log(`operation\t${output.operation.id}`)
  } finally {
    db.close()
  }
}

function runIssueCode(options) {
  const { operator, reason } = requireWriteAudit(options)
  const db = openDb(resolveDbPath(options), { ensureSupport: true, ensureVip: true })
  try {
    const createdAt = Date.now()
    const expiresDays = asPositiveInteger(options['expires-days'], 30, 'expires-days')
    const expiresAt = createdAt + expiresDays * 24 * 60 * 60 * 1000
    const recipient = String(options.recipient || options.openid || options['user-id'] || '').trim()
    let code = createCode(options.prefix)
    while (db.prepare('SELECT code FROM vip_invite_codes WHERE code = ?').get(code)) {
      code = createCode(options.prefix)
    }
    const targetUser = options['user-id']
      ? db.prepare('SELECT * FROM users WHERE id = ?').get(options['user-id'])
      : options.openid
        ? db.prepare('SELECT * FROM users WHERE openid = ?').get(options.openid)
        : null
    const result = {
      code,
      status: 'active',
      maxUses: 1,
      usedCount: 0,
      recipient,
      createdAt: toIso(createdAt),
      expiresAt: toIso(expiresAt),
    }

    const tx = db.transaction(() => {
      db.prepare(`
        INSERT INTO vip_invite_codes (code, status, max_uses, used_count, created_at, expires_at)
        VALUES (?, 'active', 1, 0, ?, ?)
      `).run(code, createdAt, expiresAt)
      const operation = recordOperation(db, {
        type: 'issue_compensation_code',
        operator,
        reason,
        userId: targetUser?.id || '',
        openid: targetUser?.openid || recipient,
        result,
      })
      return { ...result, operation }
    })

    const output = options['dry-run'] ? { ...result, dryRun: true } : tx()
    if (options.json) {
      console.log(JSON.stringify(output, null, 2))
      return
    }
    console.log(`code\t${output.code}`)
    console.log(`expires_at\t${output.expiresAt}`)
    if (output.operation) console.log(`operation\t${output.operation.id}`)
  } finally {
    db.close()
  }
}

function main() {
  const { command, options } = parseArgs(process.argv.slice(2))
  if (!command || command === 'help' || command === '--help' || options.help) usage(0)

  switch (command) {
    case 'lookup':
      runLookup(options)
      break
    case 'activate-membership':
      runActivateMembership(options)
      break
    case 'issue-code':
      runIssueCode(options)
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
