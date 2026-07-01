export const EMPTY = '-'
export const ELLIPSIS = '...'
const INR = '\u20B9'

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

export function avatarHue(seed: string): number {
  let hash = 0
  for (const ch of seed) hash = ch.charCodeAt(0) + ((hash << 5) - hash)
  return Math.abs(hash) % 360
}
