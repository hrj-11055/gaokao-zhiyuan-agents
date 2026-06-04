export const PROFILE_IDENTITY_KEY = 'profile_identity'

export const PROFILE_PERSONALITIES = [
  '勇敢',
  '温柔',
  '好奇',
  '沉稳',
  '浪漫',
  '热情',
  '机灵',
  '从容',
  '坚定',
  '自在',
  '认真',
  '开朗',
]

export const PROFILE_ANIMALS = [
  { key: 'panda', label: '熊猫', avatar: '/static/avatars/panda.png' },
  { key: 'penguin', label: '企鹅', avatar: '/static/avatars/penguin.png' },
  { key: 'otter', label: '水獭', avatar: '/static/avatars/otter.png' },
  { key: 'fox', label: '狐狸', avatar: '/static/avatars/fox.png' },
  { key: 'rabbit', label: '兔子', avatar: '/static/avatars/rabbit.png' },
  { key: 'owl', label: '猫头鹰', avatar: '/static/avatars/owl.png' },
  { key: 'bear', label: '小熊', avatar: '/static/avatars/bear.png' },
  { key: 'shiba', label: '柴犬', avatar: '/static/avatars/shiba.png' },
]

function pickRandom(items, random) {
  const value = Number(random())
  const normalized = Number.isFinite(value)
    ? Math.max(0, Math.min(value, 0.999999999))
    : 0
  return items[Math.floor(normalized * items.length)]
}

function resolveProfileIdentity(identity) {
  if (!identity || !PROFILE_PERSONALITIES.includes(identity.personality)) {
    return null
  }
  const animal = PROFILE_ANIMALS.find((item) => item.key === identity.animal)
  if (!animal) return null
  return {
    personality: identity.personality,
    animal: animal.key,
    nickname: `${identity.personality}的${animal.label}`,
    avatar: animal.avatar,
  }
}

export function generateProfileIdentity(random = Math.random) {
  const personality = pickRandom(PROFILE_PERSONALITIES, random)
  const animal = pickRandom(PROFILE_ANIMALS, random)
  return resolveProfileIdentity({ personality, animal: animal.key })
}

export function getOrCreateProfileIdentity(random = Math.random) {
  const stored = uni.getStorageSync(PROFILE_IDENTITY_KEY)
  if (stored) {
    try {
      const resolved = resolveProfileIdentity(
        typeof stored === 'string' ? JSON.parse(stored) : stored
      )
      if (resolved) return resolved
    } catch {
      // Regenerate invalid local identity data.
    }
  }

  const generated = generateProfileIdentity(random)
  uni.setStorageSync(PROFILE_IDENTITY_KEY, JSON.stringify({
    personality: generated.personality,
    animal: generated.animal,
  }))
  return generated
}
