'use strict'

const fs = require('fs')
const path = require('path')

const SCHOOL_NAME_URL = 'https://static-data.gaokao.cn/www/2.0/school/name.json'
const LOGO_BASE_URL = 'https://static-data.gaokao.cn/upload/logo'
const CACHE_DIR = path.join(__dirname, '..', 'public', 'university-logos')
const MANIFEST_PATH = path.join(CACHE_DIR, 'manifest.json')
const SCHOOL_LIST_TTL_MS = 24 * 60 * 60 * 1000

let schoolListCache = null
let schoolListFetchedAt = 0
let manifestCache = null

function normalizeName(name = '') {
  return String(name || '')
    .replace(/^\d+_/, '')
    .replace(/_(深度研究报告|deep_research)$/i, '')
    .replace(/(大学深度评估报告|大学深度研究报告|深度评估报告|深度研究报告)$/, '')
    .replace(/[（）]/g, (char) => (char === '（' ? '(' : ')'))
    .replace(/\s+/g, '')
    .trim()
}

function ensureCacheDir() {
  fs.mkdirSync(CACHE_DIR, { recursive: true })
}

function loadManifest() {
  if (manifestCache) return manifestCache
  try {
    manifestCache = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'))
  } catch {
    manifestCache = {}
  }
  return manifestCache
}

function saveManifest(manifest) {
  ensureCacheDir()
  manifestCache = manifest
  fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2))
}

async function fetchJson(url) {
  const res = await fetch(url, {
    headers: { Accept: 'application/json' },
    signal: AbortSignal.timeout(Number(process.env.UNIVERSITY_LOGO_TIMEOUT_MS || 10000)),
  })
  if (!res.ok) {
    throw new Error(`院校数据请求失败 ${res.status}`)
  }
  return res.json()
}

async function getSchoolList() {
  const now = Date.now()
  if (schoolListCache && now - schoolListFetchedAt < SCHOOL_LIST_TTL_MS) {
    return schoolListCache
  }
  const payload = await fetchJson(SCHOOL_NAME_URL)
  schoolListCache = Array.isArray(payload.data) ? payload.data : []
  schoolListFetchedAt = now
  return schoolListCache
}

function matchSchoolByName(schools, name) {
  const target = normalizeName(name)
  if (!target) return null

  const exact = schools.find((school) => normalizeName(school.name) === target)
  if (exact) return exact

  return schools.find((school) => {
    const aliases = [
      school.name,
      school.short,
      school.answer_short,
      school.old_name,
    ]
      .filter(Boolean)
      .flatMap((value) => String(value).split(/[,，、]/))
      .map(normalizeName)
      .filter(Boolean)
    return aliases.includes(target)
  }) || null
}

function logoFilePath(schoolId) {
  return path.join(CACHE_DIR, `${schoolId}.jpg`)
}

async function downloadLogo(schoolId) {
  const url = `${LOGO_BASE_URL}/${encodeURIComponent(schoolId)}.jpg`
  const res = await fetch(url, {
    headers: { Accept: 'image/jpeg,image/png,image/*' },
    signal: AbortSignal.timeout(Number(process.env.UNIVERSITY_LOGO_TIMEOUT_MS || 10000)),
  })
  if (!res.ok) {
    throw new Error(`校徽下载失败 ${res.status}`)
  }
  const contentType = res.headers.get('content-type') || 'image/jpeg'
  if (!contentType.startsWith('image/')) {
    throw new Error(`校徽响应类型异常 ${contentType}`)
  }
  const buffer = Buffer.from(await res.arrayBuffer())
  ensureCacheDir()
  fs.writeFileSync(logoFilePath(schoolId), buffer)
  return { buffer, contentType, url }
}

async function resolveUniversityLogo(name) {
  const manifest = loadManifest()
  const normalizedName = normalizeName(name)
  const existing = manifest[normalizedName]
  if (existing?.school_id) {
    const localPath = logoFilePath(existing.school_id)
    if (fs.existsSync(localPath)) {
      return {
        buffer: fs.readFileSync(localPath),
        contentType: existing.content_type || 'image/jpeg',
        schoolId: existing.school_id,
      }
    }
  }

  const schools = await getSchoolList()
  const matched = matchSchoolByName(schools, name)
  if (!matched?.school_id) {
    return null
  }

  const { buffer, contentType, url } = await downloadLogo(matched.school_id)
  manifest[normalizedName] = {
    name: matched.name,
    school_id: String(matched.school_id),
    content_type: contentType,
    source_url: url,
    cached_at: new Date().toISOString(),
  }
  saveManifest(manifest)

  return {
    buffer,
    contentType,
    schoolId: String(matched.school_id),
  }
}

module.exports = {
  resolveUniversityLogo,
}
