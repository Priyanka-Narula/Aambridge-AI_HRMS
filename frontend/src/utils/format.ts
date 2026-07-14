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

/** Format a wall-clock HH:MM string (office schedule) for display. */
export function formatOfficeTime(hhmm: string): string {
  const [hours = 0, minutes = 0] = hhmm.split(':').map((part) => Number(part))
  const date = new Date(Date.UTC(2020, 0, 1, hours, minutes, 0))
  return date.toLocaleTimeString('en-AE', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone: 'UTC',
  })
}

/** Format an absolute timestamp in UAE (Dubai) office time. */
export function formatUaetime(
  iso: string | Date | null | undefined,
  options: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit' },
  timeZone: string = OFFICE_TIMEZONE,
): string {
  if (!iso) return EMPTY
  const date = iso instanceof Date ? iso : new Date(iso)
  if (Number.isNaN(date.getTime())) return EMPTY
  return date.toLocaleTimeString('en-AE', { ...options, timeZone })
}

/** Current UAE office-local hour (0–23). */
export function uaeHour(date: Date = new Date(), timeZone: string = OFFICE_TIMEZONE): number {
  const hour = new Intl.DateTimeFormat('en-GB', {
    hour: 'numeric',
    hour12: false,
    timeZone,
  }).format(date)
  return Number(hour)
}

export function avatarHue(seed: string): number {
  let hash = 0
  for (const ch of seed) hash = ch.charCodeAt(0) + ((hash << 5) - hash)
  return Math.abs(hash) % 360
}
