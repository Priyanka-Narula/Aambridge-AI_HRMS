export const EMPTY = '-'
export const ELLIPSIS = '...'
const INR = '\u20B9'
export const OFFICE_TIMEZONE = 'Asia/Dubai'

export function orEmpty(value: string | null | undefined): string {
  if (value == null || String(value).trim() === '') return EMPTY
  return String(value)
}

export function formatInr(value: number | null | undefined): string {
  if (value == null) return EMPTY
  if (value >= 100_000) return `${INR}${(value / 100_000).toFixed(1)}L`
  return `${INR}${value.toLocaleString('en-IN')}`
}

export function initials(first: string, last: string): string {
  return `${first[0] ?? ''}${last[0] ?? ''}`.toUpperCase()
}

export function formatOfficeTime(hhmm: string): string {
  // Policy times are already UAE wall-clock (e.g. "09:15") — format as-is.
  const [hours = 0, minutes = 0] = hhmm.split(':').map((part) => Number(part))
  const ampm = hours >= 12 ? 'PM' : 'AM'
  const h12 = hours % 12 || 12
  return `${h12}:${String(minutes).padStart(2, '0')} ${ampm}`
}

export function formatUaeTime(
  iso: string | Date | null | undefined,
  opts: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  },
  timeZone: string = OFFICE_TIMEZONE,
): string {
  if (!iso) return '—'
  const d = typeof iso === 'string' ? new Date(iso) : iso
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleTimeString('en-AE', { ...opts, timeZone })
}

/** Office-local hour (0-23), used to pick a time-of-day greeting. */
export function uaeHour(date: Date = new Date(), timeZone: string = OFFICE_TIMEZONE): number {
  return Number(
    new Intl.DateTimeFormat('en-GB', { hour: 'numeric', hour12: false, timeZone }).format(date),
  )
}

export function formatUaeClock(date: Date = new Date()): string {
  return date.toLocaleTimeString('en-AE', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
    timeZone: OFFICE_TIMEZONE,
  })
}

export function avatarHue(seed: string): number {
  let hash = 0
  for (const ch of seed) hash = ch.charCodeAt(0) + ((hash << 5) - hash)
  return Math.abs(hash) % 360
}
