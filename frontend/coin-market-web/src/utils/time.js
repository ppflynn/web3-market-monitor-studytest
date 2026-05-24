const APP_TIME_ZONE = 'Asia/Shanghai'
const SHANGHAI_OFFSET = '+08:00'
const TZ_SUFFIX_RE = /(Z|[+-]\d{2}:?\d{2})$/i

export function parseAppDate(value) {
  if (value == null || value === '') return null

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value
  }

  if (typeof value === 'number') {
    const timestamp = Math.abs(value) < 1e12 ? value * 1000 : value
    const date = new Date(timestamp)
    return Number.isNaN(date.getTime()) ? null : date
  }

  if (Array.isArray(value) && value.length >= 3) {
    const [year, month, day, hour = 0, minute = 0, second = 0] = value
    return parseAppDate(
      `${year}-${pad(month)}-${pad(day)}T${pad(hour)}:${pad(minute)}:${pad(second)}`
    )
  }

  const raw = String(value).trim()
  if (!raw) return null

  if (/^\d+$/.test(raw)) {
    return parseAppDate(Number(raw))
  }

  const normalized = raw.replace(' ', 'T')
  const withZone = TZ_SUFFIX_RE.test(normalized)
    ? normalized
    : `${normalized}${SHANGHAI_OFFSET}`
  const date = new Date(withZone)

  if (!Number.isNaN(date.getTime())) return date

  const fallback = new Date(raw)
  return Number.isNaN(fallback.getTime()) ? null : fallback
}

export function formatAppDateTime(value, emptyText = '--') {
  const date = parseAppDate(value)
  if (!date) return emptyText

  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: APP_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    hourCycle: 'h23'
  }).format(date).replace(/\//g, '-')
}

export function formatAppShortDate(value, emptyText = '--') {
  const date = parseAppDate(value)
  if (!date) return emptyText

  return new Intl.DateTimeFormat('en-US', {
    timeZone: APP_TIME_ZONE,
    month: 'short',
    day: 'numeric'
  }).format(date)
}

function pad(value) {
  return String(value).padStart(2, '0')
}
