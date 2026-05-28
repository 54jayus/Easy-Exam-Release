import type { Ref } from 'vue'
import { computed, ref } from 'vue'
import { compareVersions } from '@/lib/versionUtils'
import type { BackendUpdateGuardStatus, ForceUpdateSnapshot, UpdateCheckResult, UpdateStatus } from '@/types/appUpdate'

const FORCE_UPDATE_STORAGE_KEY = 'easy_exam_force_update_state'

function loadForceUpdateSnapshot(): ForceUpdateSnapshot | null {
  const raw = localStorage.getItem(FORCE_UPDATE_STORAGE_KEY)
  if (!raw) return null

  try {
    const parsed = JSON.parse(raw)
    const requiredVersion =
      typeof parsed?.requiredVersion === 'string' ? parsed.requiredVersion.trim() : ''
    const latestVersion =
      typeof parsed?.latestVersion === 'string' ? parsed.latestVersion.trim() : ''
    if (!requiredVersion) return null

    return {
      requiredVersion,
      latestVersion: latestVersion || requiredVersion,
      releaseDate: typeof parsed?.releaseDate === 'string' ? parsed.releaseDate.trim() : '',
      notes: Array.isArray(parsed?.notes)
        ? parsed.notes.map((item: unknown) => String(item ?? '').trim()).filter(Boolean)
        : [],
      url: typeof parsed?.url === 'string' ? parsed.url.trim() : '',
      checkedAt: typeof parsed?.checkedAt === 'string' ? parsed.checkedAt.trim() : '',
    }
  } catch {
    return null
  }
}

function persistForceUpdateSnapshot(snapshot: ForceUpdateSnapshot) {
  localStorage.setItem(FORCE_UPDATE_STORAGE_KEY, JSON.stringify(snapshot))
}

function clearForceUpdateSnapshotFromStorage() {
  localStorage.removeItem(FORCE_UPDATE_STORAGE_KEY)
}

function isSnapshotBlockingCurrentVersion(snapshot: ForceUpdateSnapshot, currentVersion: string) {
  return compareVersions(currentVersion, snapshot.requiredVersion) < 0
}

export function useForceUpdate(params: {
  currentVersion: Ref<string>
  latestVersion: Ref<string>
  releaseDate: Ref<string>
  notes: Ref<string[]>
  updateDownloadUrl: Ref<string>
  updateStatus: Ref<UpdateStatus>
  updateStatusMessage: Ref<string>
  showUpdateDialog: Ref<boolean>
  downloadedFilePath: Ref<string>
  downloadedVersion: Ref<string>
  downloadProgress: Ref<number>
  hasMatchingDownloadedPackage: (version: string) => boolean
  clearDownloadedArtifact: (resetProgress?: boolean) => void
}) {
  const forceUpdateActive = ref(false)
  const forceUpdatePending = ref(false)
  const forceUpdateMeta = ref<ForceUpdateSnapshot | null>(null)

  const isForceUpdateMode = computed(() => forceUpdateActive.value || forceUpdatePending.value)

  const resolveTargetVersion = (fallback = '') => {
    const metaVersion = forceUpdateMeta.value?.latestVersion || ''
    const latest = params.latestVersion.value || ''
    const version = metaVersion || latest || fallback
    return typeof version === 'string' ? version.trim() : ''
  }

  const applyReleaseFields = (snapshot: ForceUpdateSnapshot) => {
    params.latestVersion.value = snapshot.latestVersion || snapshot.requiredVersion
    params.releaseDate.value = snapshot.releaseDate
    params.notes.value = [...snapshot.notes]
    params.updateDownloadUrl.value = snapshot.url
  }

  const clearForceUpdateState = (clearPersisted = true) => {
    forceUpdateActive.value = false
    forceUpdatePending.value = false
    forceUpdateMeta.value = null
    if (clearPersisted) {
      clearForceUpdateSnapshotFromStorage()
    }
  }

  const createForceUpdateSnapshotFromResult = (result: UpdateCheckResult): ForceUpdateSnapshot | null => {
    const latest = typeof result.latestVersion === 'string' ? result.latestVersion.trim() : ''
    if (!latest) return null
    return {
      requiredVersion: latest,
      latestVersion: latest,
      releaseDate: result.releaseDate || '',
      notes: Array.isArray(result.notes) ? [...result.notes] : [],
      url: result.url || '',
      checkedAt: '',
    }
  }

  const createForceUpdateSnapshotFromBackendStatus = (
    status: BackendUpdateGuardStatus
  ): ForceUpdateSnapshot | null => {
    const requiredVersion = String(status.requiredVersion || '').trim()
    const latestVersion = String(status.latestVersion || requiredVersion).trim()
    if (!requiredVersion) return null
    return {
      requiredVersion,
      latestVersion: latestVersion || requiredVersion,
      releaseDate: String(status.releaseDate || '').trim(),
      notes: Array.isArray(status.notes) ? [...status.notes] : [],
      url: String(status.downloadUrl || '').trim(),
      checkedAt: String(status.checkedAt || '').trim(),
    }
  }

  const applyForceUpdateActive = (
    snapshot: ForceUpdateSnapshot,
    options?: { fromPersistence?: boolean; message?: string }
  ) => {
    forceUpdateActive.value = true
    forceUpdatePending.value = false
    forceUpdateMeta.value = snapshot
    params.showUpdateDialog.value = false
    applyReleaseFields(snapshot)

    if (options?.fromPersistence) {
      params.clearDownloadedArtifact(true)
    }

    params.updateStatus.value = params.hasMatchingDownloadedPackage(snapshot.latestVersion || snapshot.requiredVersion)
      ? 'downloaded'
      : snapshot.url
        ? 'available'
        : 'error'
    params.updateStatusMessage.value =
      options?.message ||
      (snapshot.url
        ? '当前版本已被标记为必须更新，请先完成升级后再继续使用软件。'
        : '当前版本已被标记为必须更新，但更新源暂未提供安装包地址，请稍后重试。')
  }

  const applyForceUpdatePending = (
    snapshot: ForceUpdateSnapshot,
    options?: { message?: string; keepPersisted?: boolean }
  ) => {
    forceUpdateActive.value = false
    forceUpdatePending.value = true
    forceUpdateMeta.value = snapshot
    applyReleaseFields(snapshot)

    if (options?.keepPersisted !== false) {
      persistForceUpdateSnapshot(snapshot)
    }

    params.updateStatus.value = params.hasMatchingDownloadedPackage(snapshot.latestVersion || snapshot.requiredVersion)
      ? 'downloaded'
      : snapshot.url
        ? 'available'
        : 'error'
    params.updateStatusMessage.value =
      options?.message ||
      (snapshot.url
        ? '已检测到必须更新版本，当前会话可继续使用，重启后需先完成升级。'
        : '已检测到必须更新版本，但更新源暂未提供安装包地址；当前会话仍可继续使用。')
  }

  const restorePersistedForceUpdate = () => {
    const snapshot = loadForceUpdateSnapshot()
    if (!snapshot) return false

    if (!isSnapshotBlockingCurrentVersion(snapshot, params.currentVersion.value)) {
      clearForceUpdateState()
      return false
    }

    applyForceUpdateActive(snapshot, {
      fromPersistence: true,
      message: snapshot.url
        ? '已恢复上次确认的强制更新要求，请先完成升级后再继续使用软件。'
        : '已恢复上次确认的强制更新要求，但当前没有可用安装包地址，请稍后重新检查。',
    })
    return true
  }

  return {
    forceUpdateActive,
    forceUpdatePending,
    forceUpdateMeta,
    isForceUpdateMode,
    resolveTargetVersion,
    clearForceUpdateState,
    createForceUpdateSnapshotFromResult,
    createForceUpdateSnapshotFromBackendStatus,
    applyForceUpdateActive,
    applyForceUpdatePending,
    restorePersistedForceUpdate,
    clearForceUpdateSnapshot: clearForceUpdateSnapshotFromStorage,
  }
}
