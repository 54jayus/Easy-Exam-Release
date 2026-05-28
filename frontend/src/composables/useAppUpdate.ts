import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { pythonBackend } from '@/lib/pythonBackend'
import { createUiFeedback, formatActionError } from '@/lib/uiFeedback'
import {
  type BackendUpdateGuardStatus,
  compareVersions,
  type ForceUpdateSnapshot,
  type UpdateCheckResult,
  type UpdateHistoryEntry,
  type UpdateStatus,
} from '@/types/appUpdate'

const FORCE_UPDATE_STORAGE_KEY = 'easy_exam_force_update_state'
const SILENT_UPDATE_CHECK_INTERVAL_MS = 10 * 60 * 1000
const MOCK_UPDATE_PREVIEW_VERSION = '3.5.0001'
const MOCK_UPDATE_PREVIEW_DATE = '2026-06-01'
const MOCK_UPDATE_PREVIEW_NOTES = [
  '新增更新弹窗交互优化，支持更清晰的状态提示与历史版本查看。',
  '改进下载进度展示与完成反馈，便于演示完整更新流程。',
  '优化安装前确认文案与异常提示，让更新操作更易理解。',
]
const MOCK_UPDATE_PREVIEW_URL = `mock://easy-exam/EasyExam-Setup-${MOCK_UPDATE_PREVIEW_VERSION}.exe`
const MOCK_UPDATE_PREVIEW_FILE_PATH = `mock-preview/EasyExam-Setup-${MOCK_UPDATE_PREVIEW_VERSION}.exe`
const MOCK_FORCE_UPDATE_PREVIEW_VERSION = '3.5.9001'
const MOCK_FORCE_UPDATE_PREVIEW_DATE = '2026-06-08'
const MOCK_FORCE_UPDATE_PREVIEW_NOTES = [
  '演示强制更新遮罩层：检测到目标版本后，未升级前限制继续使用软件。',
  '演示强制更新下载与安装状态流转，便于验证按钮、提示语与交互顺序。',
  '演示强制更新恢复逻辑，确保重新打开应用后仍能保持升级限制。',
]
const MOCK_FORCE_UPDATE_PREVIEW_URL = `mock://easy-exam/EasyExam-Setup-${MOCK_FORCE_UPDATE_PREVIEW_VERSION}.exe`
const MOCK_FORCE_UPDATE_PREVIEW_FILE_PATH = `mock-preview/EasyExam-Setup-${MOCK_FORCE_UPDATE_PREVIEW_VERSION}.exe`
const MOCK_DOWNLOAD_PROGRESS_STEP_COUNT = 60
const MOCK_DOWNLOAD_TOTAL_DURATION_MS = 60 * 1000

function buildMockDownloadProgressSteps(stepCount: number): number[] {
  return Array.from({ length: stepCount }, (_value, index) =>
    Math.round((((index + 1) / stepCount) * 1000)) / 10
  )
}

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

function clearForceUpdateSnapshot() {
  localStorage.removeItem(FORCE_UPDATE_STORAGE_KEY)
}

function isSnapshotBlockingCurrentVersion(snapshot: ForceUpdateSnapshot, currentVersion: string) {
  return compareVersions(currentVersion, snapshot.requiredVersion) < 0
}

export function useAppUpdate() {
  const feedback = createUiFeedback()

  const currentVersion = ref('--')
  const updateStatus = ref<UpdateStatus>('idle')
  const latestVersion = ref('')
  const releaseDate = ref('')
  const notes = ref<string[]>([])
  const downloadProgress = ref(0)
  const downloadedFilePath = ref('')
  const downloadedVersion = ref('')
  const activeDownloadVersion = ref('')
  const updateDownloadUrl = ref('')
  const updateStatusMessage = ref('')
  const showUpdateDialog = ref(false)
  const showHistoryPanel = ref(false)
  const historyLoading = ref(false)
  const historyLoaded = ref(false)
  const historyError = ref('')
  const updateHistory = ref<UpdateHistoryEntry[]>([])
  const showAllNotes = ref(false)
  const mockUpdatePreviewActive = ref(false)
  const mockForceUpdatePreviewActive = ref(false)
  const mockDownloadPaused = ref(false)
  const backgroundDownloadActive = ref(false)
  const forceUpdateActive = ref(false)
  const forceUpdatePending = ref(false)
  const forceUpdateMeta = ref<ForceUpdateSnapshot | null>(null)

  let silentCheckTimer: ReturnType<typeof setInterval> | null = null
  let removeProgressListener: (() => void) | undefined
  let removeDownloadedListener: (() => void) | undefined
  let removeErrorListener: (() => void) | undefined

  const isMockPreviewRunning = () => mockUpdatePreviewActive.value || mockForceUpdatePreviewActive.value

  const isForceUpdateMode = computed(() => forceUpdateActive.value || forceUpdatePending.value)

  const normalizeVersion = (value: unknown) =>
    typeof value === 'string' ? value.trim() : ''

  const resolveTargetVersion = (fallback = '') =>
    normalizeVersion(forceUpdateMeta.value?.latestVersion || latestVersion.value || fallback)

  const clearDownloadedArtifact = (resetProgress = false) => {
    downloadedFilePath.value = ''
    downloadedVersion.value = ''
    if (resetProgress) {
      downloadProgress.value = 0
    }
  }

  const setDownloadedArtifact = (filePath: string, version: string) => {
    downloadedFilePath.value = filePath
    downloadedVersion.value = normalizeVersion(version)
    downloadProgress.value = filePath ? 100 : 0
  }

  const clearActiveDownloadTarget = () => {
    activeDownloadVersion.value = ''
  }

  const setActiveDownloadTarget = (version: string) => {
    activeDownloadVersion.value = normalizeVersion(version)
  }

  const hasMatchingDownloadedPackage = (version: string) => {
    const normalizedVersion = normalizeVersion(version)
    return Boolean(
      downloadedFilePath.value
      && downloadedVersion.value
      && normalizedVersion
      && downloadedVersion.value === normalizedVersion
    )
  }

  const clearStaleDownloadedArtifact = (nextVersion: string) => {
    const normalizedVersion = normalizeVersion(nextVersion)
    if (!normalizedVersion || updateStatus.value === 'downloading') {
      return
    }
    if (downloadedVersion.value && downloadedVersion.value !== normalizedVersion) {
      clearDownloadedArtifact(true)
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

  const applyReleaseFields = (snapshot: ForceUpdateSnapshot) => {
    latestVersion.value = snapshot.latestVersion || snapshot.requiredVersion
    releaseDate.value = snapshot.releaseDate
    notes.value = [...snapshot.notes]
    updateDownloadUrl.value = snapshot.url
  }

  const clearForceUpdateState = (clearPersisted = true) => {
    forceUpdateActive.value = false
    forceUpdatePending.value = false
    forceUpdateMeta.value = null
    if (clearPersisted) {
      clearForceUpdateSnapshot()
    }
  }

  const applyForceUpdateActive = (
    snapshot: ForceUpdateSnapshot,
    options?: { fromPersistence?: boolean; message?: string }
  ) => {
    forceUpdateActive.value = true
    forceUpdatePending.value = false
    forceUpdateMeta.value = snapshot
    showUpdateDialog.value = false
    applyReleaseFields(snapshot)

    if (options?.fromPersistence) {
      clearDownloadedArtifact(true)
    }

    updateStatus.value = hasMatchingDownloadedPackage(snapshot.latestVersion || snapshot.requiredVersion)
      ? 'downloaded'
      : snapshot.url
        ? 'available'
        : 'error'
    updateStatusMessage.value =
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

    updateStatus.value = hasMatchingDownloadedPackage(snapshot.latestVersion || snapshot.requiredVersion)
      ? 'downloaded'
      : snapshot.url
        ? 'available'
        : 'error'
    updateStatusMessage.value =
      options?.message ||
      (snapshot.url
        ? '已检测到必须更新版本，当前会话可继续使用，重启后需先完成升级。'
        : '已检测到必须更新版本，但更新源暂未提供安装包地址；当前会话仍可继续使用。')
  }

  const restorePersistedForceUpdate = () => {
    const snapshot = loadForceUpdateSnapshot()
    if (!snapshot) return false

    if (!isSnapshotBlockingCurrentVersion(snapshot, currentVersion.value)) {
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

  const createMockUpdateResult = (mandatory = false): UpdateCheckResult => {
    const version = mandatory ? MOCK_FORCE_UPDATE_PREVIEW_VERSION : MOCK_UPDATE_PREVIEW_VERSION
    return {
      currentVersion: currentVersion.value,
      latestVersion: version,
      hasUpdate: true,
      enabled: true,
      releaseDate: mandatory ? MOCK_FORCE_UPDATE_PREVIEW_DATE : MOCK_UPDATE_PREVIEW_DATE,
      notes: mandatory ? [...MOCK_FORCE_UPDATE_PREVIEW_NOTES] : [...MOCK_UPDATE_PREVIEW_NOTES],
      mandatory,
      url: mandatory ? MOCK_FORCE_UPDATE_PREVIEW_URL : MOCK_UPDATE_PREVIEW_URL,
      downloadedFilePath:
        hasMatchingDownloadedPackage(version) && downloadedFilePath.value
          ? downloadedFilePath.value
          : null,
    }
  }

  const createMockUpdateHistoryEntry = (mandatory = false): UpdateHistoryEntry => {
    const version = mandatory ? MOCK_FORCE_UPDATE_PREVIEW_VERSION : MOCK_UPDATE_PREVIEW_VERSION
    return {
      version,
      title: `Easy Exam.v${version}`,
      releaseDate: mandatory ? MOCK_FORCE_UPDATE_PREVIEW_DATE : MOCK_UPDATE_PREVIEW_DATE,
      notes: mandatory ? [...MOCK_FORCE_UPDATE_PREVIEW_NOTES] : [...MOCK_UPDATE_PREVIEW_NOTES],
      url: mandatory ? MOCK_FORCE_UPDATE_PREVIEW_URL : MOCK_UPDATE_PREVIEW_URL,
      releasePageUrl: '',
    }
  }

  const mergeMockUpdateHistory = (entries: UpdateHistoryEntry[]) => {
    if (!isMockPreviewRunning()) return entries
    const mockEntry = createMockUpdateHistoryEntry(mockForceUpdatePreviewActive.value)
    return [mockEntry, ...entries.filter((entry) => entry.version !== mockEntry.version)]
  }

  const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

  const showUpdateBadge = computed(() =>
    isForceUpdateMode.value || ['available', 'downloading', 'paused', 'downloaded'].includes(updateStatus.value)
  )

  const updateTooltip = computed(() => {
    if (forceUpdateActive.value) {
      switch (updateStatus.value) {
        case 'downloading':
          return '正在下载必须安装的新版本'
        case 'downloaded':
          return '必须安装新版本后才能继续使用'
        case 'error':
          return '强制更新检查失败，点击重试'
        default:
          return '检测到必须更新版本'
      }
    }
    if (forceUpdatePending.value) {
      switch (updateStatus.value) {
        case 'downloading':
          return '正在下载必须更新包，下次启动会生效'
        case 'downloaded':
          return '已下载必须更新包，下次启动需先安装'
        case 'error':
          return '必须更新信息待确认'
        default:
          return '已检测到必须更新版本，将于下次启动生效'
      }
    }
    switch (updateStatus.value) {
      case 'checking':
        return '正在检查更新'
      case 'available':
        return '发现新版本，点击查看详情'
      case 'downloading':
        return backgroundDownloadActive.value ? '正在后台下载更新包' : '正在下载更新包'
      case 'paused':
        return '下载已暂停，点击查看详情'
      case 'downloaded':
        return '更新包已准备好，点击立即安装'
      case 'up_to_date':
        return '当前已是最新版本'
      case 'error':
        return '更新检查失败，点击重试'
      default:
        return '检查更新'
    }
  })

  const updateButtonClass = computed(() => {
    if (isForceUpdateMode.value) {
      return '!text-rose-300 hover:!text-rose-200'
    }
    if (updateStatus.value === 'available' || updateStatus.value === 'downloading' || updateStatus.value === 'downloaded') {
      return '!text-amber-400 hover:!text-amber-300'
    }
    if (updateStatus.value === 'checking') {
      return '!text-primary-300 hover:!text-white'
    }
    return '!text-primary-400 hover:!text-white'
  })

  const updateStatusTitle = computed(() => {
    if (forceUpdateActive.value) {
      switch (updateStatus.value) {
        case 'checking':
          return '正在验证必须安装的版本'
        case 'available':
          return '检测到必须更新版本'
        case 'downloading':
          return '必须更新包下载中'
        case 'downloaded':
          return '安装包已准备完成'
        case 'error':
          return '强制更新暂时不可用'
        default:
          return '请先完成版本升级'
      }
    }
    if (forceUpdatePending.value) {
      switch (updateStatus.value) {
        case 'checking':
          return '正在确认必须安装的版本'
        case 'available':
          return '检测到必须更新版本（下次启动生效）'
        case 'downloading':
          return '必须更新包下载中'
        case 'downloaded':
          return '更新包已准备完成'
        case 'error':
          return '必须更新信息待确认'
        default:
          return '已记录必须更新要求'
      }
    }
    switch (updateStatus.value) {
      case 'checking':
        return '正在检查最新版本'
      case 'available':
        return '发现新版本'
      case 'downloading':
        return backgroundDownloadActive.value ? '更新包后台下载中' : '更新包下载中'
      case 'paused':
        return '下载已暂停'
      case 'downloaded':
        return '更新包已下载完成'
      case 'up_to_date':
        return '当前已是最新版本'
      case 'error':
        return '更新流程遇到问题'
      default:
        return '尚未执行更新检查'
    }
  })

  const updateStatusDescription = computed(() => {
    if (forceUpdateActive.value) {
      if (updateStatus.value === 'available' && !updateDownloadUrl.value) {
        return '检测到必须更新版本，但当前更新源没有可下载的安装包地址。'
      }
      switch (updateStatus.value) {
        case 'checking':
          return '正在连接更新源并确认必须安装的目标版本。'
        case 'available':
          return '检测到新版本后，必须完成下载和安装，软件才可继续使用。'
        case 'downloading':
          return '安装包会下载到本机更新缓存目录，完成后可直接启动安装。'
        case 'paused':
          return '下载已暂停，可稍后继续下载或直接安装已有进度。'
        case 'downloaded':
          return '安装新版本后，当前的强制更新限制会自动解除。'
        case 'error':
          return '请重新检查更新；如果问题持续存在，请确认网络或更新源配置。'
        default:
          return '当前版本需要先升级后才能继续使用。'
      }
    }
    if (forceUpdatePending.value) {
      if (updateStatus.value === 'available' && !updateDownloadUrl.value) {
        return '已检测到必须更新版本，但当前更新源没有可下载的安装包地址。'
      }
      switch (updateStatus.value) {
        case 'checking':
          return '正在连接更新源并确认必须安装的目标版本。'
        case 'available':
          return '当前会话仍可继续使用；重启软件后需要先完成升级。'
        case 'downloading':
          return '更新包会下载到本机更新缓存目录，完成后下次启动可直接安装。'
        case 'paused':
          return '下载已暂停，可稍后继续；重启软件后需要先完成升级。'
        case 'downloaded':
          return '当前会话仍可继续使用；下次启动前请先安装新版本。'
        case 'error':
          return '必须更新要求已记录，但本次检查失败；当前会话仍可继续使用。'
        default:
          return '已检测到必须更新版本，下次启动后会限制进入软件。'
      }
    }
    if (mockUpdatePreviewActive.value) {
      switch (updateStatus.value) {
        case 'available':
          return '当前是开发者预演模式，可直接演示新版本提示与下载入口。'
        case 'downloading':
          return '正在本地模拟下载进度，不会访问真实更新源或安装包。'
        case 'paused':
          return '模拟下载已暂停，可点击继续恢复下载进度。'
        case 'downloaded':
          return '可以继续查看安装确认交互，真实安装程序不会被启动。'
        default:
          break
      }
    }
    if (updateStatus.value === 'available' && !updateDownloadUrl.value) {
      return '检测到新版本，但当前更新源缺少下载地址，请稍后再试。'
    }
    switch (updateStatus.value) {
      case 'checking':
        return '正在连接更新源并比对版本信息。'
      case 'available':
        return '可以开始下载最新安装包，下载完成后即可直接安装。'
      case 'downloading':
        return backgroundDownloadActive.value
          ? '更新包正在后台下载，你可以继续使用软件；下载完成后会提示安装。'
          : '更新包将下载到本机更新缓存目录，下载完成后可直接启动安装。'
      case 'paused':
        return '下载已暂停，可稍后继续下载。'
      case 'downloaded':
        return '安装时将关闭当前软件，请先确认当前工作已保存。'
      case 'up_to_date':
        return '暂时没有比当前版本更高的正式更新。'
      case 'error':
        return '你可以稍后重新检查，或确认网络和更新源配置是否正常。'
      default:
        return '启动后会静默检测更新，你也可以手动点击图标检查。'
    }
  })

  const updateStatusChipText = computed(() => {
    if (forceUpdateActive.value) {
      switch (updateStatus.value) {
        case 'checking':
          return '校验中'
        case 'available':
          return '必须更新'
        case 'downloading':
          return '强更下载中'
        case 'downloaded':
          return '等待安装'
        case 'error':
          return '需重试'
        default:
          return '已锁定'
      }
    }
    if (forceUpdatePending.value) {
      switch (updateStatus.value) {
        case 'checking':
          return '校验中'
        case 'available':
          return '下次强更'
        case 'downloading':
          return '准备升级'
        case 'downloaded':
          return '待重启安装'
        case 'error':
          return '待确认'
        default:
          return '已记录'
      }
    }
    switch (updateStatus.value) {
      case 'checking':
        return '检查中'
      case 'available':
        return '可更新'
      case 'downloading':
        return backgroundDownloadActive.value ? '后台下载中' : '下载中'
      case 'paused':
        return '已暂停'
      case 'downloaded':
        return '可安装'
      case 'up_to_date':
        return '已最新'
      case 'error':
        return '异常'
      default:
        return '空闲'
    }
  })

  const updateStatusChipClass = computed(() => {
    if (isForceUpdateMode.value) {
      switch (updateStatus.value) {
        case 'available':
        case 'downloading':
        case 'downloaded':
          return 'bg-rose-100 text-rose-700'
        case 'checking':
          return 'bg-orange-100 text-orange-700'
        case 'error':
          return 'bg-rose-50 text-rose-600'
        default:
          return 'bg-slate-100 text-slate-500'
      }
    }
    switch (updateStatus.value) {
      case 'available':
      case 'downloading':
      case 'paused':
      case 'downloaded':
        return 'bg-primary-100 text-primary-700'
      case 'checking':
        return 'bg-slate-100 text-slate-600'
      case 'error':
        return 'bg-rose-50 text-rose-600'
      case 'up_to_date':
        return 'bg-emerald-50 text-emerald-600'
      default:
        return 'bg-slate-100 text-slate-500'
    }
  })

  const updateStatusPanelClass = computed(() => {
    if (isForceUpdateMode.value) {
      switch (updateStatus.value) {
        case 'available':
        case 'downloading':
        case 'downloaded':
          return 'border-rose-100 bg-rose-50/70'
        case 'error':
          return 'border-amber-100 bg-amber-50/80'
        default:
          return 'border-slate-200 bg-slate-50'
      }
    }
    switch (updateStatus.value) {
      case 'available':
      case 'downloading':
      case 'paused':
      case 'downloaded':
        return 'border-primary-100 bg-primary-50/70'
      case 'error':
        return 'border-rose-100 bg-rose-50/80'
      case 'up_to_date':
        return 'border-emerald-100 bg-emerald-50/80'
      default:
        return 'border-slate-200 bg-slate-50'
    }
  })

  const updateStatusTitleClass = computed(() => {
    if (isForceUpdateMode.value) {
      switch (updateStatus.value) {
        case 'available':
        case 'downloading':
        case 'downloaded':
          return 'text-rose-700'
        case 'error':
          return 'text-amber-700'
        default:
          return 'text-slate-700'
      }
    }
    switch (updateStatus.value) {
      case 'available':
      case 'downloading':
      case 'paused':
      case 'downloaded':
        return 'text-primary-700'
      case 'error':
        return 'text-rose-600'
      case 'up_to_date':
        return 'text-emerald-600'
      default:
        return 'text-slate-700'
    }
  })

  const visibleNotes = computed(() =>
    showAllNotes.value || notes.value.length <= 4 ? notes.value : notes.value.slice(0, 4)
  )

  const applyOrdinaryUpdateResult = (result: UpdateCheckResult, manual: boolean) => {
    clearForceUpdateState()
    showAllNotes.value = false
    currentVersion.value = result.currentVersion || currentVersion.value
    latestVersion.value = result.latestVersion || ''
    releaseDate.value = result.releaseDate || ''
    notes.value = result.notes || []
    updateDownloadUrl.value = result.url || ''
    if (result.downloadedFilePath) {
      setDownloadedArtifact(result.downloadedFilePath, result.latestVersion || '')
    } else {
      clearDownloadedArtifact(true)
    }
    updateStatusMessage.value = ''

    if (!result.enabled) {
      updateStatus.value = 'idle'
      if (manual) {
        showUpdateDialog.value = true
        feedback.info('当前没有可用更新', { toast: true })
      }
      return
    }

    if (result.hasUpdate) {
      updateStatus.value = hasMatchingDownloadedPackage(result.latestVersion || '') ? 'downloaded' : 'available'
      if (manual) {
        showUpdateDialog.value = true
        if (!result.url) {
          feedback.warning('检测到新版本，但更新配置不完整，暂时无法下载')
        }
      }
      return
    }

    updateStatus.value = 'up_to_date'
    if (manual) {
      showUpdateDialog.value = true
      feedback.success('当前已是最新版本', { toast: true })
    }
  }

  const applyMockForceUpdateResult = (manual: boolean) => {
    const result = createMockUpdateResult(true)
    const snapshot = createForceUpdateSnapshotFromResult(result)
    if (snapshot) {
      forceUpdateMeta.value = snapshot
      applyForceUpdateActive(snapshot, {
        message: '当前为开发者强制更新预演模式，下载与安装均不会触发真实更新。',
      })
    }
    currentVersion.value = result.currentVersion || currentVersion.value
    if (result.downloadedFilePath) {
      setDownloadedArtifact(result.downloadedFilePath, result.latestVersion || '')
    } else {
      clearDownloadedArtifact(true)
    }
    if (manual) {
      feedback.warning('已切换到强制更新预演模式', { toast: true })
    }
  }

  const activateMockUpdatePreview = async () => {
    const hadLoadedHistory = historyLoaded.value
    mockUpdatePreviewActive.value = true
    mockForceUpdatePreviewActive.value = false
    clearForceUpdateState(false)
    historyError.value = ''
    showHistoryPanel.value = false
    updateStatusMessage.value = '当前为开发者预演模式，下载与安装均不会触发真实更新。'
    applyOrdinaryUpdateResult(createMockUpdateResult(), true)
    if (hadLoadedHistory) {
      updateHistory.value = mergeMockUpdateHistory(updateHistory.value)
      historyLoaded.value = true
    } else {
      historyLoaded.value = false
    }
    feedback.success('已切换到新版本更新预演模式', { toast: true })
  }

  const activateMockForceUpdatePreview = async () => {
    const hadLoadedHistory = historyLoaded.value
    mockUpdatePreviewActive.value = false
    mockForceUpdatePreviewActive.value = true
    historyError.value = ''
    showHistoryPanel.value = false
    applyMockForceUpdateResult(true)
    clearForceUpdateSnapshot()
    if (hadLoadedHistory) {
      updateHistory.value = mergeMockUpdateHistory(updateHistory.value)
      historyLoaded.value = true
    } else {
      historyLoaded.value = false
    }
  }

  const applySuccessfulBackendStatus = (
    status: BackendUpdateGuardStatus,
    source: 'startup' | 'silent' | 'manual'
  ) => {
    showAllNotes.value = false
    currentVersion.value = status.currentVersion || currentVersion.value

    if (status.mandatoryDetected) {
      const snapshot = createForceUpdateSnapshotFromBackendStatus(status)
      if (!snapshot) return

      if (forceUpdateActive.value) {
        applyForceUpdateActive(snapshot, {
          message: '后端已确认当前版本必须升级，请先完成更新后再继续使用软件。',
        })
        persistForceUpdateSnapshot(snapshot)
        return
      }

      applyForceUpdatePending(snapshot, {
        message:
          source === 'manual'
            ? '检测到必须更新的新版本，当前会话可继续使用；重启软件后需先完成升级。'
            : '已检测到必须更新版本，当前会话可继续使用；重启软件后将限制进入软件。',
      })
      if (source === 'manual') {
        showUpdateDialog.value = true
        feedback.warning('检测到必须更新版本，已记录为下次启动生效。', { toast: true })
      }
      return
    }

    if (forceUpdateActive.value || forceUpdatePending.value) {
      clearForceUpdateState()
    }

    latestVersion.value = status.latestVersion || ''
    clearStaleDownloadedArtifact(latestVersion.value)
    releaseDate.value = status.releaseDate || ''
    notes.value = status.notes || []
    updateDownloadUrl.value = status.downloadUrl || ''
    updateStatusMessage.value = ''

    if (!status.enabled) {
      updateStatus.value = 'idle'
      if (source === 'manual') {
        showUpdateDialog.value = true
        feedback.info('当前没有可用更新', { toast: true })
      }
      return
    }

    if (status.hasUpdate) {
      updateStatus.value = hasMatchingDownloadedPackage(status.latestVersion || '') ? 'downloaded' : 'available'
      if (updateStatus.value === 'available' && !activeDownloadVersion.value) {
        downloadProgress.value = 0
      }
      if (source === 'manual') {
        showUpdateDialog.value = true
        if (!status.downloadUrl) {
          feedback.warning('检测到新版本，但更新配置不完整，暂时无法下载')
        }
      }
      return
    }

    updateStatus.value = 'up_to_date'
    if (source === 'manual') {
      showUpdateDialog.value = true
      feedback.success('当前已是最新版本', { toast: true })
    }
  }

  const handleBackendStatusFailure = (
    status: BackendUpdateGuardStatus,
    source: 'startup' | 'silent' | 'manual'
  ) => {
    const message = status.errorMessage || '更新检查失败'
    if (source === 'manual') {
      showUpdateDialog.value = true
    }

    if (forceUpdateActive.value) {
      updateStatus.value = 'error'
      updateStatusMessage.value = message
      return
    }

    if (forceUpdatePending.value) {
      updateStatus.value = 'error'
      updateStatusMessage.value = `更新检查失败：${message}`
      return
    }

    if (source === 'manual') {
      updateStatus.value = 'error'
      updateStatusMessage.value = `更新检查失败：${message}`
      feedback.error(message)
    }
  }

  const syncBackendUpdateStatus = async (
    source: 'startup' | 'silent' | 'manual',
    forceRefresh = source !== 'startup'
  ) => {
    if (source === 'silent' && updateStatus.value === 'downloading') {
      return
    }

    if (mockForceUpdatePreviewActive.value) {
      applyMockForceUpdateResult(source === 'manual')
      return
    }

    if (mockUpdatePreviewActive.value) {
      applyOrdinaryUpdateResult(createMockUpdateResult(), source === 'manual')
      updateStatusMessage.value = '当前为开发者预演模式，下载与安装均不会触发真实更新。'
      return
    }

    const previousStatus = updateStatus.value
    updateStatus.value = 'checking'
    if (source !== 'silent') {
      updateStatusMessage.value = ''
    }

    try {
      const method = forceRefresh ? 'system.refreshUpdateGuard' : 'system.getUpdateGuardStatus'
      const status = await pythonBackend.request(method, {}) as BackendUpdateGuardStatus
      if (!status.checkSucceeded) {
        handleBackendStatusFailure(status, source)
        if (source === 'silent' && !forceUpdateActive.value && !forceUpdatePending.value) {
          updateStatus.value =
            previousStatus === 'downloaded'
              ? 'downloaded'
              : previousStatus === 'available'
                ? 'available'
                : previousStatus === 'up_to_date'
                  ? 'up_to_date'
                  : 'idle'
        }
        return
      }
      applySuccessfulBackendStatus(status, source)
    } catch (error: any) {
      const message = error instanceof Error ? error.message : String(error)
      if (forceUpdateActive.value || forceUpdatePending.value) {
        updateStatus.value = 'error'
        updateStatusMessage.value = message
      } else if (source === 'manual') {
        showUpdateDialog.value = true
        updateStatus.value = 'error'
        updateStatusMessage.value = message
        feedback.error(formatActionError('检查更新', error))
      } else {
        updateStatus.value =
          previousStatus === 'downloaded'
            ? 'downloaded'
            : previousStatus === 'available'
              ? 'available'
              : previousStatus === 'up_to_date'
                ? 'up_to_date'
                : 'idle'
      }
    }
  }

  const startSilentUpdateLoop = () => {
    if (silentCheckTimer) {
      clearInterval(silentCheckTimer)
    }
    silentCheckTimer = setInterval(() => {
      void syncBackendUpdateStatus('silent', true)
    }, SILENT_UPDATE_CHECK_INTERVAL_MS)
  }

  const stopSilentUpdateLoop = () => {
    if (!silentCheckTimer) return
    clearInterval(silentCheckTimer)
    silentCheckTimer = null
  }

  const handleManualUpdateCheck = async () => {
    if (!forceUpdateActive.value) {
      showUpdateDialog.value = true
    }
    await syncBackendUpdateStatus('manual', true)
  }

  const handleUpdateIconClick = async () => {
    if (forceUpdateActive.value) {
      return
    }
    if (
      forceUpdatePending.value ||
      updateStatus.value === 'available' ||
      updateStatus.value === 'downloading' ||
      updateStatus.value === 'downloaded' ||
      updateStatus.value === 'checking'
    ) {
      showUpdateDialog.value = true
      return
    }
    await syncBackendUpdateStatus('manual', true)
  }

  const retryForceUpdateCheck = async () => {
    await syncBackendUpdateStatus('manual', true)
  }

  const startUpdateDownload = async () => {
    return startUpdateDownloadInternal(false)
  }

  const startBackgroundUpdateDownload = async () => {
    return startUpdateDownloadInternal(true)
  }

  const pauseUpdateDownload = async () => {
    if (isMockPreviewRunning()) {
      mockDownloadPaused.value = true
      return
    }

    try {
      await window.electron?.ipcRenderer.invoke('update:pauseDownload')
    } catch {}
    updateStatus.value = 'paused'
    updateStatusMessage.value = '下载已暂停，可稍后继续'
    backgroundDownloadActive.value = false
  }

  const startUpdateDownloadInternal = async (background: boolean) => {
    if (!updateDownloadUrl.value) {
      feedback.warning('当前更新源缺少安装包地址，暂时无法下载')
      return
    }

    const targetVersion = resolveTargetVersion()

    if (updateStatus.value === 'downloading') {
      backgroundDownloadActive.value = background
      showUpdateDialog.value = !background
      if (background && !isForceUpdateMode.value) {
        updateStatusMessage.value = '更新包正在后台下载，你可以继续使用软件。'
      }
      return
    }

    if (isMockPreviewRunning()) {
      const wasPaused = updateStatus.value === 'paused'
      backgroundDownloadActive.value = background
      showUpdateDialog.value = !background
      updateStatus.value = 'downloading'
      mockDownloadPaused.value = false
      updateStatusMessage.value = mockForceUpdatePreviewActive.value
        ? background
          ? '正在后台模拟强制更新下载过程，不会请求真实安装包。'
          : '正在模拟强制更新下载过程，不会请求真实安装包。'
        : background
          ? '正在后台模拟下载过程，不会请求真实安装包。'
          : '正在模拟下载过程，不会请求真实安装包。'
      // Don't reset progress when resuming from paused
      if (!wasPaused) {
        downloadProgress.value = 0
      }
      const currentProgress = downloadProgress.value
      const progressSteps = buildMockDownloadProgressSteps(MOCK_DOWNLOAD_PROGRESS_STEP_COUNT)
      const stepDelay = Math.max(1, Math.round(MOCK_DOWNLOAD_TOTAL_DURATION_MS / progressSteps.length))
      for (const percent of progressSteps) {
        // Skip steps that are below the current progress (resume support)
        if (percent <= currentProgress) continue
        if (mockDownloadPaused.value) {
          updateStatus.value = 'paused'
          updateStatusMessage.value = '下载已暂停，可稍后继续'
          backgroundDownloadActive.value = false
          return
        }
        await wait(stepDelay)
        downloadProgress.value = percent
      }
      setDownloadedArtifact(
        mockForceUpdatePreviewActive.value
          ? MOCK_FORCE_UPDATE_PREVIEW_FILE_PATH
          : MOCK_UPDATE_PREVIEW_FILE_PATH,
        targetVersion || (mockForceUpdatePreviewActive.value
          ? MOCK_FORCE_UPDATE_PREVIEW_VERSION
          : MOCK_UPDATE_PREVIEW_VERSION)
      )
      backgroundDownloadActive.value = false
      showUpdateDialog.value = true
      updateStatus.value = 'downloaded'
      updateStatusMessage.value = mockForceUpdatePreviewActive.value
        ? background
          ? '后台模拟强制更新下载已完成，可以继续预览安装确认交互。'
          : '模拟强制更新下载已完成，可以继续预览安装确认交互。'
        : background
          ? '后台模拟下载已完成，可以继续预览安装确认交互。'
          : '模拟下载已完成，可以继续预览安装确认交互。'
      feedback.success(
        mockForceUpdatePreviewActive.value
          ? background
            ? '后台模拟强制更新下载完成，可以继续预览安装流程'
            : '模拟强制更新下载完成，可以继续预览安装流程'
          : background
            ? '后台模拟下载完成，可以继续预览安装流程'
            : '模拟下载完成，可以继续预览安装流程'
      )
      return
    }

    backgroundDownloadActive.value = background
    showUpdateDialog.value = !background
    clearStaleDownloadedArtifact(targetVersion)
    setActiveDownloadTarget(targetVersion)
    updateStatus.value = 'downloading'
    updateStatusMessage.value = background ? '更新包正在后台下载，你可以继续使用软件。' : ''
    downloadProgress.value = 0

    try {
      const result = await window.electron?.ipcRenderer.invoke('update:startDownload', {
        version: latestVersion.value || forceUpdateMeta.value?.latestVersion || '',
        releaseDate: releaseDate.value,
        notes: notes.value,
        mandatory: isForceUpdateMode.value,
        url: updateDownloadUrl.value,
      }) as UpdateCheckResult

      if (result?.downloadedFilePath) {
        clearActiveDownloadTarget()
        backgroundDownloadActive.value = false
        setDownloadedArtifact(result.downloadedFilePath, targetVersion)
        showUpdateDialog.value = true
        updateStatus.value = 'downloaded'
      }
    } catch (error: any) {
      clearActiveDownloadTarget()
      backgroundDownloadActive.value = false
      if (error instanceof Error && error.message === 'DOWNLOAD_PAUSED') {
        updateStatus.value = 'paused'
        updateStatusMessage.value = '下载已暂停，可稍后继续'
        return
      }
      showUpdateDialog.value = true
      updateStatus.value = isForceUpdateMode.value ? 'error' : 'available'
      updateStatusMessage.value = error instanceof Error ? error.message : String(error)
      feedback.error(formatActionError('下载更新包', error))
    }
  }

  const installDownloadedUpdate = async () => {
    if (!downloadedFilePath.value) {
      feedback.warning('请先下载更新包，再执行安装')
      return
    }
    const targetVersion = resolveTargetVersion(downloadedVersion.value)
    if (targetVersion && downloadedVersion.value && downloadedVersion.value !== targetVersion) {
      const staleVersion = downloadedVersion.value
      clearDownloadedArtifact(true)
      updateStatus.value = updateDownloadUrl.value ? 'available' : 'error'
      updateStatusMessage.value = `检测到更新目标已切换到 v${targetVersion}，请重新下载最新安装包。`
      feedback.warning(`当前缓存的安装包对应 v${staleVersion}，请重新下载 v${targetVersion}`)
      return
    }
    try {
      await feedback.confirmWarning({
        title: '安装新版本',
        message: '安装将关闭当前软件并启动安装程序，是否继续？',
        confirmButtonText: '立即安装',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }

    if (isMockPreviewRunning()) {
      updateStatusMessage.value = mockForceUpdatePreviewActive.value
        ? '本次为开发者强制更新预演模式，已跳过真实安装程序启动。'
        : '本次为开发者预演模式，已跳过真实安装程序启动。'
      feedback.success(
        mockForceUpdatePreviewActive.value
          ? '已完成强制更新安装交互预演，真实安装未执行'
          : '已完成安装交互预演，真实安装未执行'
      )
      return
    }

    try {
      await window.electron?.ipcRenderer.invoke('update:installDownloaded')
    } catch (error: any) {
      feedback.error(formatActionError('启动安装包', error))
    }
  }

  const loadUpdateHistory = async (force = false) => {
    if (historyLoading.value) return
    if (historyLoaded.value && !force) return

    historyLoading.value = true
    historyError.value = ''
    try {
      const result = await window.electron?.ipcRenderer.invoke('update:getHistory') as UpdateHistoryEntry[]
      updateHistory.value = mergeMockUpdateHistory(Array.isArray(result) ? result : [])
      historyLoaded.value = true
    } catch (error: any) {
      historyError.value = error instanceof Error ? error.message : String(error)
    } finally {
      historyLoading.value = false
    }
  }

  const toggleHistoryPanel = async () => {
    showHistoryPanel.value = !showHistoryPanel.value
    if (showHistoryPanel.value) {
      await loadUpdateHistory()
    }
  }

  const openReleasePage = async (url: string) => {
    try {
      await window.electron?.ipcRenderer.invoke('open_external', url)
    } catch (error: any) {
      feedback.error(formatActionError('打开发布页', error))
    }
  }

  const resetMockUpdatePreview = async (silent = false) => {
    const hadMockPreview = isMockPreviewRunning()
    mockUpdatePreviewActive.value = false
    mockForceUpdatePreviewActive.value = false
    mockDownloadPaused.value = false
    backgroundDownloadActive.value = false
    clearActiveDownloadTarget()
    downloadProgress.value = 0
    clearDownloadedArtifact()
    updateStatusMessage.value = ''

    if (!hadMockPreview) return

    clearForceUpdateState()
    historyLoaded.value = false
    updateHistory.value = []
    if (showHistoryPanel.value) {
      await loadUpdateHistory(true)
    }
    await syncBackendUpdateStatus('startup', false)
    if (!silent) {
      feedback.success('已恢复真实更新状态', { toast: true })
    }
  }

  const closeUpdateDialog = () => {
    showUpdateDialog.value = false
    // If downloading, switch to background download mode
    if (updateStatus.value === 'downloading') {
      backgroundDownloadActive.value = true
      if (!isForceUpdateMode.value) {
        updateStatusMessage.value = '更新包正在后台下载，你可以继续使用软件。'
      }
    }
    // If paused, keep the paused state but hide dialog
  }

  const toggleShowAllNotes = () => {
    showAllNotes.value = !showAllNotes.value
  }

  const resetUpdateUiState = () => {
    stopSilentUpdateLoop()
    showUpdateDialog.value = false
    showHistoryPanel.value = false
    historyLoading.value = false
    historyLoaded.value = false
    historyError.value = ''
    updateHistory.value = []
    showAllNotes.value = false
    mockUpdatePreviewActive.value = false
    mockForceUpdatePreviewActive.value = false
    mockDownloadPaused.value = false
    backgroundDownloadActive.value = false
    clearActiveDownloadTarget()
    clearForceUpdateState()
    updateStatus.value = 'idle'
    latestVersion.value = ''
    releaseDate.value = ''
    notes.value = []
    downloadProgress.value = 0
    clearDownloadedArtifact()
    updateDownloadUrl.value = ''
    updateStatusMessage.value = ''
  }

  onMounted(async () => {
    try {
      const version = await window.electron?.ipcRenderer.invoke('update:getCurrentVersion')
      if (typeof version === 'string' && version.trim()) {
        currentVersion.value = version.trim()
      }
    } catch {
      currentVersion.value = currentVersion.value || '--'
    }

    restorePersistedForceUpdate()

    removeProgressListener = window.electron?.ipcRenderer.on('update-progress', (_event: any, payload: any) => {
      const incomingVersion = normalizeVersion(payload?.version)
      const expectedVersion = normalizeVersion(activeDownloadVersion.value || latestVersion.value || incomingVersion)
      if (incomingVersion && expectedVersion && incomingVersion !== expectedVersion) {
        return
      }
      updateStatus.value = 'downloading'
      if (typeof payload?.percent === 'number' && Number.isFinite(payload.percent)) {
        if (payload.percent >= downloadProgress.value) {
          downloadProgress.value = payload.percent
        }
      }
      if (incomingVersion) {
        latestVersion.value = incomingVersion
        if (!activeDownloadVersion.value) {
          activeDownloadVersion.value = incomingVersion
        }
      }
      if (backgroundDownloadActive.value && !isForceUpdateMode.value) {
        updateStatusMessage.value = '更新包正在后台下载，你可以继续使用软件。'
      }
    })

    removeDownloadedListener = window.electron?.ipcRenderer.on('update-downloaded', (_event: any, payload: any) => {
      const incomingVersion = normalizeVersion(payload?.version)
      const expectedVersion = normalizeVersion(activeDownloadVersion.value || latestVersion.value || incomingVersion)
      if (incomingVersion && expectedVersion && incomingVersion !== expectedVersion) {
        return
      }
      const finishedInBackground = backgroundDownloadActive.value
      clearActiveDownloadTarget()
      backgroundDownloadActive.value = false
      updateStatus.value = 'downloaded'
      downloadProgress.value = 100
      setDownloadedArtifact(typeof payload?.filePath === 'string' ? payload.filePath : '', incomingVersion)
      if (incomingVersion) {
        latestVersion.value = incomingVersion
      }
      if (finishedInBackground) {
        showUpdateDialog.value = true
        updateStatusMessage.value = '后台下载已完成，可以立即安装新版本。'
        feedback.success('后台下载已完成，可以立即安装新版本')
        return
      }
      feedback.success('更新包下载完成，可以立即安装')
    })

    removeErrorListener = window.electron?.ipcRenderer.on('update-error', (_event: any, payload: any) => {
      clearActiveDownloadTarget()
      backgroundDownloadActive.value = false
      if (updateStatus.value === 'downloading' || showUpdateDialog.value || isForceUpdateMode.value) {
        updateStatus.value = 'error'
        updateStatusMessage.value = typeof payload?.message === 'string' ? payload.message : '更新流程发生异常'
        showUpdateDialog.value = true
      }
    })

    await syncBackendUpdateStatus('startup', false)
    startSilentUpdateLoop()
  })

  onBeforeUnmount(() => {
    stopSilentUpdateLoop()
    removeProgressListener?.()
    removeDownloadedListener?.()
    removeErrorListener?.()
  })

  return {
    currentVersion,
    updateStatus,
    latestVersion,
    releaseDate,
    notes,
    downloadProgress,
    downloadedFilePath,
    updateDownloadUrl,
    updateStatusMessage,
    showUpdateDialog,
    showHistoryPanel,
    historyLoading,
    historyLoaded,
    historyError,
    updateHistory,
    showAllNotes,
    mockUpdatePreviewActive,
    mockForceUpdatePreviewActive,
    backgroundDownloadActive,
    forceUpdateActive,
    forceUpdateMeta,
    showUpdateBadge,
    updateTooltip,
    updateButtonClass,
    updateStatusTitle,
    updateStatusDescription,
    updateStatusChipText,
    updateStatusChipClass,
    updateStatusPanelClass,
    updateStatusTitleClass,
    visibleNotes,
    handleManualUpdateCheck,
    handleUpdateIconClick,
    retryForceUpdateCheck,
    startUpdateDownload,
    startBackgroundUpdateDownload,
    pauseUpdateDownload,
    installDownloadedUpdate,
    toggleHistoryPanel,
    loadUpdateHistory,
    openReleasePage,
    activateMockUpdatePreview,
    activateMockForceUpdatePreview,
    resetMockUpdatePreview,
    closeUpdateDialog,
    toggleShowAllNotes,
    resetUpdateUiState,
  }
}
