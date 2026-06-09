'use strict'

const DEFAULT_SCORE_API_URL = 'http://159.75.110.157/score-api'
const SCORE_CONTEXT_CACHE_TTL_MS = Number(process.env.SCORE_CONTEXT_CACHE_TTL_MS || 5 * 60 * 1000)
const SCORE_CONTEXT_CACHE_MAX = Number(process.env.SCORE_CONTEXT_CACHE_MAX || 500)
const recommendationCache = new Map()

function getRecommendationMode(profile = {}) {
  if (profile.planning_mode === 'early' || profile.report_mode === 'planning') return 'planning'
  if (profile.score_type === 'estimated' || profile.report_mode === 'estimated') return 'estimated'
  return 'official'
}

function hasRecommendationPosition(profile = {}) {
  return Boolean(profile.score || String(profile.score_range || '').trim())
}

function buildRecommendationContextUrl(profile = {}, options = {}) {
  const scoreApiUrl = options.scoreApiUrl || process.env.SCORE_API_URL || DEFAULT_SCORE_API_URL
  const year = Number(options.year || process.env.SCORE_DATA_YEAR || 2025)
  const url = new URL(`${scoreApiUrl.replace(/\/+$/, '')}/api/scores/recommendation-context`)
  url.searchParams.set('province', profile.province || '')
  url.searchParams.set('category', profile.category || '')
  url.searchParams.set('year', String(year))
  url.searchParams.set('mode', getRecommendationMode(profile))
  url.searchParams.set('limit_per_tier', String(options.limitPerTier || 10))
  if (profile.score) url.searchParams.set('score', String(profile.score))
  if (profile.rank) url.searchParams.set('rank', String(profile.rank))
  if (profile.score_range) url.searchParams.set('score_range', String(profile.score_range))
  return url
}

async function fetchRecommendationContext(profile = {}, options = {}) {
  if (!profile.province || !profile.category || !hasRecommendationPosition(profile)) return null
  const url = buildRecommendationContextUrl(profile, options)
  const cacheKey = url.toString()
  const cached = recommendationCache.get(cacheKey)
  if (cached && cached.expiresAt > Date.now()) return cached.value
  if (cached) recommendationCache.delete(cacheKey)

  const res = await fetch(url, { signal: AbortSignal.timeout(options.timeoutMs || 5000) })
  if (!res.ok) {
    throw new Error(`recommendation context API failed: ${res.status} ${await res.text()}`)
  }
  const value = await res.json()
  recommendationCache.set(cacheKey, {
    value,
    expiresAt: Date.now() + SCORE_CONTEXT_CACHE_TTL_MS,
  })
  if (recommendationCache.size > SCORE_CONTEXT_CACHE_MAX) {
    recommendationCache.delete(recommendationCache.keys().next().value)
  }
  return value
}

function flattenRecommendationContext(context = {}) {
  const tiers = context.tiers
  if (!tiers && Array.isArray(context.recommendations)) return context.recommendations
  const sourceTiers = tiers || context
  const orderedTiers = ['稳', '冲', '保']
  const rowsByTier = orderedTiers.map((tier) =>
    (Array.isArray(sourceTiers[tier]) ? sourceTiers[tier] : []).map((item) => ({
      ...item,
      tier: item.tier || tier,
      bucket: item.bucket || item.tier || tier,
    }))
  )
  const recommendations = []
  const maxLength = Math.max(0, ...rowsByTier.map((rows) => rows.length))
  for (let index = 0; index < maxLength; index += 1) {
    rowsByTier.forEach((rows) => {
      if (rows[index]) recommendations.push(rows[index])
    })
  }
  return recommendations
}

module.exports = {
  buildRecommendationContextUrl,
  fetchRecommendationContext,
  flattenRecommendationContext,
  getRecommendationMode,
  hasRecommendationPosition,
}
