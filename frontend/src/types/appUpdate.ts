export type UpdateStatus = 'idle' | 'checking' | 'up_to_date' | 'available' | 'downloading' | 'downloaded' | 'error'

export type UpdateCheckResult = {
  currentVersion: string
  latestVersion: string | null
  hasUpdate: boolean
  enabled: boolean
  releaseDate: string | null
  notes: string[]
  mandatory: boolean
  url: string | null
  downloadedFilePath: string | null
  errorMessage?: string | null
}

export type UpdateHistoryEntry = {
  version: string
  title: string
  releaseDate: string
  notes: string[]
  url: string
  releasePageUrl?: string
}

export type ForceUpdateSnapshot = {
  version: string
  releaseDate: string
  notes: string[]
  url: string
}

export function compareVersions(left: string, right: string): number {
  const leftParts = String(left || '')
    .split('.')
    .map((part) => Number.parseInt(part, 10) || 0)
  const rightParts = String(right || '')
    .split('.')
    .map((part) => Number.parseInt(part, 10) || 0)
  const maxLength = Math.max(leftParts.length, rightParts.length)

  for (let index = 0; index < maxLength; index += 1) {
    const leftValue = leftParts[index] ?? 0
    const rightValue = rightParts[index] ?? 0
    if (leftValue > rightValue) return 1
    if (leftValue < rightValue) return -1
  }

  return 0
}
