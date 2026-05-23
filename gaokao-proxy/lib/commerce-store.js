const fs = require('fs')
const path = require('path')
const Database = require('better-sqlite3')

function defaultIdFactory(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}

function toUser(row) {
  if (!row) return null
  return {
    userId: row.id,
    openid: row.openid,
    unionid: row.unionid || '',
    invitedByUserId: row.invited_by_user_id || '',
    profileCompletedAt: row.profile_completed_at || 0,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  }
}

function toOrder(row) {
  if (!row) return null
  return {
    orderId: row.id,
    userId: row.user_id,
    outTradeNo: row.out_trade_no,
    transactionId: row.transaction_id || '',
    amountCents: row.amount_cents,
    status: row.status,
    prepayId: row.prepay_id || '',
    paidAt: row.paid_at || 0,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  }
}

function toIntOrEmpty(value) {
  if (value === '' || value === null || value === undefined) {
    return ''
  }
  const number = Number(value)
  return Number.isFinite(number) ? Math.trunc(number) : ''
}

function createCommerceStore({
  dbPath = process.env.COMMERCE_DB_PATH || path.join(__dirname, '..', 'data', 'gaokao-commerce.sqlite'),
  now = () => Date.now(),
  idFactory = defaultIdFactory,
  inviteRequired = Number(process.env.MEMBERSHIP_INVITE_REQUIRED || 3),
  priceCents = Number(process.env.MEMBERSHIP_PRICE_CENTS || 2900),
} = {}) {
  if (dbPath !== ':memory:') {
    fs.mkdirSync(path.dirname(dbPath), { recursive: true })
  }

  const db = new Database(dbPath)
  db.pragma('journal_mode = WAL')
  db.pragma('foreign_keys = ON')

  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      openid TEXT UNIQUE NOT NULL,
      unionid TEXT,
      nickname TEXT,
      avatar_url TEXT,
      invited_by_user_id TEXT,
      profile_completed_at INTEGER,
      profile_json TEXT,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS memberships (
      user_id TEXT PRIMARY KEY,
      status TEXT NOT NULL,
      source TEXT NOT NULL,
      unlocked_at INTEGER,
      expires_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS invites (
      id TEXT PRIMARY KEY,
      inviter_user_id TEXT NOT NULL,
      invitee_user_id TEXT NOT NULL UNIQUE,
      status TEXT NOT NULL,
      effective_at INTEGER,
      created_at INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS payment_orders (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      out_trade_no TEXT UNIQUE NOT NULL,
      transaction_id TEXT,
      amount_cents INTEGER NOT NULL,
      status TEXT NOT NULL,
      prepay_id TEXT,
      paid_at INTEGER,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL,
      raw_notify TEXT
    );
  `)

  const userColumns = db.prepare('PRAGMA table_info(users)').all().map((column) => column.name)
  if (!userColumns.includes('profile_json')) {
    db.exec('ALTER TABLE users ADD COLUMN profile_json TEXT')
  }

  const getUserById = db.prepare('SELECT * FROM users WHERE id = ?')
  const getUserByOpenid = db.prepare('SELECT * FROM users WHERE openid = ?')
  const insertUser = db.prepare(`
    INSERT INTO users (
      id, openid, unionid, nickname, avatar_url, invited_by_user_id,
      profile_completed_at, created_at, updated_at
    ) VALUES (
      @id, @openid, @unionid, @nickname, @avatarUrl, @invitedByUserId,
      @profileCompletedAt, @createdAt, @updatedAt
    )
  `)
  const updateUser = db.prepare(`
    UPDATE users
    SET unionid = COALESCE(@unionid, unionid),
        nickname = COALESCE(@nickname, nickname),
        avatar_url = COALESCE(@avatarUrl, avatar_url),
        invited_by_user_id = COALESCE(invited_by_user_id, @invitedByUserId),
        updated_at = @updatedAt
    WHERE id = @id
  `)
  const insertInvite = db.prepare(`
    INSERT OR IGNORE INTO invites (
      id, inviter_user_id, invitee_user_id, status, effective_at, created_at
    ) VALUES (
      @id, @inviterUserId, @inviteeUserId, 'pending', NULL, @createdAt
    )
  `)
  const getMembership = db.prepare('SELECT * FROM memberships WHERE user_id = ?')
  const upsertMembership = db.prepare(`
    INSERT INTO memberships (user_id, status, source, unlocked_at, expires_at)
    VALUES (@userId, 'active', @source, @unlockedAt, NULL)
    ON CONFLICT(user_id) DO UPDATE SET
      status = 'active',
      source = excluded.source,
      unlocked_at = COALESCE(memberships.unlocked_at, excluded.unlocked_at),
      expires_at = NULL
  `)
  const countEffectiveInvites = db.prepare(`
    SELECT COUNT(*) AS count
    FROM invites
    WHERE inviter_user_id = ? AND status = 'effective'
  `)
  const getPendingInviteForInvitee = db.prepare(`
    SELECT * FROM invites
    WHERE invitee_user_id = ? AND status = 'pending'
  `)
  const markInviteEffective = db.prepare(`
    UPDATE invites
    SET status = 'effective', effective_at = @effectiveAt
    WHERE id = @id AND status = 'pending'
  `)
  const markProfileCompleted = db.prepare(`
    UPDATE users
    SET profile_completed_at = COALESCE(profile_completed_at, @completedAt),
        updated_at = @completedAt
    WHERE id = @userId
  `)
  const saveUserProfile = db.prepare(`
    UPDATE users
    SET profile_json = @profileJson,
        profile_completed_at = COALESCE(profile_completed_at, @updatedAt),
        updated_at = @updatedAt
    WHERE id = @userId
  `)
  const insertOrder = db.prepare(`
    INSERT INTO payment_orders (
      id, user_id, out_trade_no, transaction_id, amount_cents,
      status, prepay_id, paid_at, created_at, updated_at, raw_notify
    ) VALUES (
      @id, @userId, @outTradeNo, NULL, @amountCents,
      'created', @prepayId, NULL, @createdAt, @updatedAt, NULL
    )
  `)
  const getOrderById = db.prepare('SELECT * FROM payment_orders WHERE id = ?')
  const getOrderByTradeNo = db.prepare('SELECT * FROM payment_orders WHERE out_trade_no = ?')
  const markPaid = db.prepare(`
    UPDATE payment_orders
    SET status = 'paid',
        transaction_id = @transactionId,
        paid_at = COALESCE(paid_at, @paidAt),
        updated_at = @paidAt,
        raw_notify = @rawNotify
    WHERE out_trade_no = @outTradeNo
  `)
  const attachPrepay = db.prepare(`
    UPDATE payment_orders
    SET prepay_id = @prepayId,
        status = CASE WHEN status = 'created' THEN 'paying' ELSE status END,
        updated_at = @updatedAt
    WHERE id = @orderId
  `)

  function activeFeatures(active) {
    return {
      universityResearch: active,
      comprehensiveReport: active,
      pdfDownload: active,
      familyShare: active,
    }
  }

  function activateMembership(userId, source = 'admin') {
    const row = getUserById.get(userId)
    if (!row) throw new Error('user not found')
    upsertMembership.run({ userId, source, unlockedAt: now() })
    return getMembershipStatus(userId)
  }

  function getMembershipStatus(userId) {
    const membership = getMembership.get(userId)
    const effectiveCount = countEffectiveInvites.get(userId)?.count || 0
    const active = membership?.status === 'active'
    return {
      status: active ? 'active' : 'inactive',
      source: active ? membership.source : '',
      unlockedAt: active ? membership.unlocked_at || 0 : 0,
      invite: {
        effectiveCount,
        requiredCount: inviteRequired,
      },
      features: activeFeatures(active),
    }
  }

  function normalizeProfile(profile = {}, timestamp = now()) {
    const score = toIntOrEmpty(profile.score)
    const rank = toIntOrEmpty(profile.rank)
    return {
      province: typeof profile.province === 'string' ? profile.province.trim() : '',
      category: typeof profile.category === 'string' ? profile.category.trim() : '',
      score,
      rank,
      family_resources: typeof profile.family_resources === 'string' ? profile.family_resources.trim() : '',
      interest_subjects: typeof profile.interest_subjects === 'string' ? profile.interest_subjects.trim() : '',
      region_preference: typeof profile.region_preference === 'string' ? profile.region_preference.trim() : '',
      career_goal: typeof profile.career_goal === 'string' ? profile.career_goal.trim() : '',
      updatedAt: timestamp,
    }
  }

  function validateProfile(profile) {
    if (!profile.province) {
      throw new Error('province is required')
    }
    if (!['物理类', '历史类'].includes(profile.category)) {
      throw new Error('category is invalid')
    }
    if (typeof profile.score !== 'number' || profile.score < 0 || profile.score > 750) {
      throw new Error('score is invalid')
    }
  }

  function parseProfile(row) {
    if (!row || !row.profile_json) {
      return normalizeProfile({ updatedAt: 0 }, 0)
    }
    try {
      const profile = JSON.parse(row.profile_json)
      return normalizeProfile(profile, profile.updatedAt || row.updated_at || 0)
    } catch {
      return normalizeProfile({ updatedAt: 0 }, 0)
    }
  }

  const upsertWechatUserTx = db.transaction(({ openid, unionid = '', nickname = '', avatarUrl = '', inviterId = '' }) => {
    if (!openid || typeof openid !== 'string') {
      throw new Error('openid is required')
    }

    const existing = getUserByOpenid.get(openid)
    const timestamp = now()
    let userId

    if (existing) {
      userId = existing.id
      updateUser.run({
        id: userId,
        unionid: unionid || null,
        nickname: nickname || null,
        avatarUrl: avatarUrl || null,
        invitedByUserId: inviterId || null,
        updatedAt: timestamp,
      })
    } else {
      userId = idFactory('u')
      insertUser.run({
        id: userId,
        openid,
        unionid,
        nickname,
        avatarUrl,
        invitedByUserId: inviterId || '',
        profileCompletedAt: 0,
        createdAt: timestamp,
        updatedAt: timestamp,
      })
    }

    if (inviterId && inviterId !== userId && getUserById.get(inviterId)) {
      insertInvite.run({
        id: idFactory('inv'),
        inviterUserId: inviterId,
        inviteeUserId: userId,
        createdAt: timestamp,
      })
    }

    return toUser(getUserById.get(userId))
  })

  const completeProfileTx = db.transaction((userId) => {
    const row = getUserById.get(userId)
    if (!row) throw new Error('user not found')

    const completedAt = now()
    markProfileCompleted.run({ userId, completedAt })

    const pendingInvite = getPendingInviteForInvitee.get(userId)
    let inviteCounted = false
    if (pendingInvite) {
      markInviteEffective.run({ id: pendingInvite.id, effectiveAt: completedAt })
      inviteCounted = true

      const effectiveCount = countEffectiveInvites.get(pendingInvite.inviter_user_id)?.count || 0
      if (effectiveCount >= inviteRequired) {
        upsertMembership.run({
          userId: pendingInvite.inviter_user_id,
          source: 'invite',
          unlockedAt: completedAt,
        })
      }
    }

    return {
      user: toUser(getUserById.get(userId)),
      inviteCounted,
      membership: getMembershipStatus(userId),
    }
  })

  function createPaymentOrder(userId) {
    const row = getUserById.get(userId)
    if (!row) throw new Error('user not found')

    const timestamp = now()
    const orderId = idFactory('ord')
    const outTradeNo = `${orderId}_${timestamp}`
    insertOrder.run({
      id: orderId,
      userId,
      outTradeNo,
      amountCents: priceCents,
      prepayId: '',
      createdAt: timestamp,
      updatedAt: timestamp,
    })
    return toOrder(getOrderById.get(orderId))
  }

  function attachPrepayId(orderId, prepayId) {
    attachPrepay.run({ orderId, prepayId, updatedAt: now() })
    return toOrder(getOrderById.get(orderId))
  }

  const markOrderPaidTx = db.transaction((outTradeNo, transactionId = '', rawNotify = {}) => {
    const order = getOrderByTradeNo.get(outTradeNo)
    if (!order) throw new Error('order not found')

    markPaid.run({
      outTradeNo,
      transactionId,
      paidAt: now(),
      rawNotify: JSON.stringify(rawNotify || {}),
    })
    upsertMembership.run({
      userId: order.user_id,
      source: 'payment',
      unlockedAt: now(),
    })
    return toOrder(getOrderByTradeNo.get(outTradeNo))
  })

  return {
    upsertWechatUser: upsertWechatUserTx,
    completeProfile: completeProfileTx,
    saveProfile(userId, profile) {
      const row = getUserById.get(userId)
      if (!row) throw new Error('user not found')
      const normalized = normalizeProfile(profile)
      validateProfile(normalized)
      saveUserProfile.run({
        userId,
        profileJson: JSON.stringify(normalized),
        updatedAt: normalized.updatedAt,
      })
      return normalized
    },
    getProfile(userId) {
      return parseProfile(getUserById.get(userId))
    },
    getMembershipStatus,
    activateMembership,
    createPaymentOrder,
    attachPrepayId,
    markOrderPaid: markOrderPaidTx,
    getOrder(orderId) {
      return toOrder(getOrderById.get(orderId))
    },
    getOrderByTradeNo(outTradeNo) {
      return toOrder(getOrderByTradeNo.get(outTradeNo))
    },
    close() {
      db.close()
    },
  }
}

module.exports = {
  createCommerceStore,
}
