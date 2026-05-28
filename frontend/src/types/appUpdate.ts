export type UpdateStatus = 'idle' | 'checking' | 'up_to_date' | 'available' | 'downloading' | 'paused' | 'downloaded' | 'error'

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
  requiredVersion: string
  latestVersion: string
  releaseDate: string
  notes: string[]
  url: string
  checkedAt: string
}

export type BackendUpdateGuardStatus = {
  checked: boolean
  checkSucceeded: boolean
  hasUpdate: boolean
  mandatoryDetected: boolean
  currentVersion: string
  latestVersion: string
  requiredVersion: string
  minSupportedVersion: string
  mandatory: boolean
  downloadUrl: string
  releaseDate: string
  notes: string[]
  enabled: boolean
  sourceUrl: string
  checkedAt: string
  errorMessage: string
}

export { compareVersions } from '@/lib/versionUtils'
