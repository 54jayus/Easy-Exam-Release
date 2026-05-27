import { computed, onMounted, ref } from 'vue'
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

function loadForceUpdateSnapshot(): ForceUpdateSnapshot | null {
  const raw = localStorage.getItem(FORCE_UPDATE_STORAGE_KEY)
  if (!raw) return null

  try {
    const parsed = JSON.parse(raw)
    const version = typeof parsed?.version === 'string' ? parsed.version.trim() : ''
    if (!version) return null
    return {
      version,
      releaseDate: typeof parsed?.releaseDate === 'string' ? parsed.releaseDate.trim() : '',
      notes: Array.isArray(parsed?.notes)
        ? parsed.notes.map((item: unknown) => String(item ?? '').trim()).filter(Boolean)
        : [],
      url: typeof parsed?.url === 'string' ? parsed.url.trim() : '',
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

export function useAppUpdate() {
  const feedback = createUiFeedback()

  const currentVersion = ref('--')
  const updateStatus = ref<UpdateStatus>('idle')
  const latestVersion = ref('')
  const releaseDate = ref('')
  const notes = ref<string[]>([])
  const downloadProgress = ref(0)
  const downloadedFilePath = ref('')
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
  const backendGuardForceUpdateActive = ref(false)
  const forceUpdateActive = ref(false)
  const forceUpdateMeta = ref<ForceUpdateSnapshot | null>(null)

  const isMockPreviewRunning = () => mockUpdatePreviewActive.value || mockForceUpdatePreviewActive.value

  const createForceUpdateSnapshotFromResult = (result: UpdateCheckResult): ForceUpdateSnapshot | null => {
    const version = typeof result.latestVersion === 'string' ? result.latestVersion.trim() : ''
    if (!version) return null
    return {
      version,
      releaseDate: result.releaseDate || '',
      notes: Array.isArray(result.notes) ? [...result.notes] : [],
      url: result.url || '',
    }
  }

  const clearForceUpdateState = (clearPersisted = true) => {
    backendGuardForceUpdateActive.value = false
    forceUpdateActive.value = false
    forceUpdateMeta.value = null
    if (clearPersisted) {
      clearForceUpdateSnapshot()
    }
  }

  const applyForceUpdateSnapshot = (
    snapshot: ForceUpdateSnapshot,
    options?: { fromPersistence?: boolean; keepStatus?: boolean; message?: string }
  ) => {
    forceUpdateActive.value = true
    forceUpdateMeta.value = snapshot
    showUpdateDialog.value = false
    latestVersion.value = snapshot.version
    releaseDate.value = snapshot.releaseDate
    notes.value = [...snapshot.notes]
    updateDownloadUrl.value = snapshot.url
    if (options?.fromPersistence) {
      downloadedFilePath.value = ''
      downloadProgress.value = 0
    }

    if (!options?.keepStatus) {
      updateStatus.value = snapshot.url ? 'available' : 'error'
    }

    if (typeof options?.message === 'string') {
      updateStatusMessage.value = options.message
    } else if (!options?.keepStatus) {
      updateStatusMessage.value = snapshot.url
        ? '检测到必须更新的新版本，请先完成升级后再继续使用软件。'
        : '检测到必须更新的新版本，但当前更新源未提供安装包地址，请重新检查更新。'
    }
  }

  const restorePersistedForceUpdate = () => {
    const snapshot = loadForceUpdateSnapshot()
    if (!snapshot) return false

    if (compareVersions(currentVersion.value, snapshot.version) >= 0) {
      clearForceUpdateState()
      return false
    }

    applyForceUpdateSnapshot(snapshot, {
      fromPersistence: true,
      message: snapshot.url
        ? '已恢复上次检测到的强制更新要求，请先完成升级后再继续使用软件。'
        : '已恢复上次检测到的强制更新要求，但当前没有可用安装包地址，请重新检查更新。',
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
        updateStatus.value === 'downloaded' && downloadedFilePath.value
          ? downloadedFilePath.value
          : null,
    }
  }

  const createForceUpdateSnapshotFromBackendStatus = (
    status: BackendUpdateGuardStatus
  ): ForceUpdateSnapshot | null => {
    const version = String(status.requiredVersion || status.latestVersion || '').trim()
    if (!version) return null
    return {
      version,
      releaseDate: String(status.releaseDate || '').trim(),
      notes: Array.isArray(status.notes) ? [...status.notes] : [],
      url: String(status.downloadUrl || '').trim(),
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
    forceUpdateActive.value || ['available', 'downloading', 'downloaded'].includes(updateStatus.value)
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
    switch (updateStatus.value) {
      case 'checking':
        return '正在检查更新'
      case 'available':
        return '发现新版本，点击查看详情'
      case 'downloading':
        return '正在下载更新包'
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
    if (forceUpdateActive.value) {
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
    switch (updateStatus.value) {
      case 'checking':
        return '正在检查最新版本'
      case 'available':
        return '发现新版本'
      case 'downloading':
        return '更新包下载中'
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
        case 'downloaded':
          return '安装新版本后，当前的强制更新限制会自动解除。'
        case 'error':
          return '请重新检查更新；如果问题持续存在，请确认网络或更新源配置。'
        default:
          return '当前版本需要先升级后才能继续使用。'
      }
    }
    if (mockUpdatePreviewActive.value) {
      switch (updateStatus.value) {
        case 'available':
          return '当前是开发者预演模式，可直接演示新版本提示与下载入口。'
        case 'downloading':
          return '正在本地模拟下载进度，不会访问真实更新源或安装包。'
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
        return '更新包将下载到本机更新缓存目录，下载完成后可直接启动安装。'
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
    switch (updateStatus.value) {
      case 'checking':
        return '检查中'
      case 'available':
        return '可更新'
      case 'downloading':
        return '下载中'
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
    if (forceUpdateActive.value) {
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
    if (forceUpdateActive.value) {
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
    if (forceUpdateActive.value) {
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

  const applyUpdateResult = (result: UpdateCheckResult, manual: boolean) => {
    if (backendGuardForceUpdateActive.value && !result.mandatory) {
      currentVersion.value = result.currentVersion || currentVersion.value
      if (manual) {
        feedback.warning('当前版本已被后端强制更新门禁限制，请先升级后再继续使用。', { toast: true })
      }
      return
    }

    showAllNotes.value = false
    currentVersion.value = result.currentVersion || currentVersion.value
    latestVersion.value = result.latestVersion || ''
    releaseDate.value = result.releaseDate || ''
    notes.value = result.notes || []
    updateDownloadUrl.value = result.url || ''
    downloadedFilePath.value = result.downloadedFilePath || ''
    downloadProgress.value = result.downloadedFilePath ? 100 : 0
    updateStatusMessage.value = ''

    if (!result.enabled) {
      clearForceUpdateState()
      updateStatus.value = 'idle'
      if (manual) {
        showUpdateDialog.value = true
        feedback.info('当前没有可用更新', { toast: true })
      }
      return
    }

    if (result.hasUpdate) {
      if (result.mandatory) {
        const snapshot = createForceUpdateSnapshotFromResult(result)
        if (snapshot) {
          persistForceUpdateSnapshot(snapshot)
          applyForceUpdateSnapshot(snapshot, { keepStatus: true })
        }
        updateStatus.value = result.downloadedFilePath ? 'downloaded' : result.url ? 'available' : 'error'
        updateStatusMessage.value = result.url
          ? '检测到必须更新的新版本，请先完成升级后再继续使用软件。'
          : '检测到必须更新的新版本，但当前更新源未提供安装包地址，请重新检查更新。'
        if (manual) {
          feedback.warning('检测到必须更新版本，完成升级后才可继续使用。', { toast: true })
        }
        return
      }

      clearForceUpdateState()
      updateStatus.value = result.downloadedFilePath ? 'downloaded' : 'available'
      if (manual) {
        showUpdateDialog.value = true
        if (!result.url) {
          feedback.warning('检测到新版本，但更新配置不完整，暂时无法下载')
        }
      }
      return
    }

    clearForceUpdateState()
    updateStatus.value = 'up_to_date'
    if (manual) {
      showUpdateDialog.value = true
      feedback.success('当前已是最新版本', { toast: true })
    }
  }

  const activateMockUpdatePreview = async () => {
    const hadLoadedHistory = historyLoaded.value
    mockUpdatePreviewActive.value = true
    mockForceUpdatePreviewActive.value = false
    backendGuardForceUpdateActive.value = false
    clearForceUpdateState(false)
    historyError.value = ''
    showHistoryPanel.value = false
    updateStatusMessage.value = '当前为开发者预演模式，下载与安装均不会触发真实更新。'
    applyUpdateResult(createMockUpdateResult(), true)
    if (hadLoadedHistory) {
      updateHistory.value = mergeMockUpdateHistory(updateHistory.value)
      historyLoaded.value = true
    } else {
      historyLoaded.value = false
    }
    feedback.success('已切换到新版本更新预演模式', { toast: true })
  }

  const applyBackendUpdateGuardStatus = (
    status: BackendUpdateGuardStatus,
    options?: { persist?: boolean; message?: string }
  ) => {
    if (!status?.locked) {
      if (forceUpdateActive.value && !mockForceUpdatePreviewActive.value) {
        clearForceUpdateState(options?.persist !== false)
      }
      return
    }

    backendGuardForceUpdateActive.value = true
    const snapshot = createForceUpdateSnapshotFromBackendStatus(status)
    if (!snapshot) return
    if (options?.persist !== false) {
      persistForceUpdateSnapshot(snapshot)
    }
    applyForceUpdateSnapshot(snapshot, {
      keepStatus: true,
      message:
        options?.message ||
        '后端已启用强制更新门禁，请先完成升级后再继续使用软件。',
    })
    updateStatus.value = downloadedFilePath.value ? 'downloaded' : snapshot.url ? 'available' : 'error'
  }

  const activateMockForceUpdatePreview = async () => {
    const hadLoadedHistory = historyLoaded.value
    mockUpdatePreviewActive.value = false
    mockForceUpdatePreviewActive.value = true
    backendGuardForceUpdateActive.value = false
    historyError.value = ''
    showHistoryPanel.value = false
    updateStatusMessage.value = '当前为开发者强制更新预演模式，下载与安装均不会触发真实更新。'
    applyUpdateResult(createMockUpdateResult(true), true)
    clearForceUpdateSnapshot()
    if (hadLoadedHistory) {
      updateHistory.value = mergeMockUpdateHistory(updateHistory.value)
      historyLoaded.value = true
    } else {
      historyLoaded.value = false
    }
    feedback.success('已切换到强制更新预演模式', { toast: true })
  }

  const runUpdateCheck = async (manual: boolean) => {
    if (mockForceUpdatePreviewActive.value) {
      applyUpdateResult(createMockUpdateResult(true), manual)
      clearForceUpdateSnapshot()
      updateStatusMessage.value = '当前为开发者强制更新预演模式，下载与安装均不会触发真实更新。'
      return
    }

    if (mockUpdatePreviewActive.value) {
      applyUpdateResult(createMockUpdateResult(), manual)
      updateStatusMessage.value = '当前为开发者预演模式，下载与安装均不会触发真实更新。'
      return
    }

    const previousStatus = updateStatus.value
    updateStatus.value = 'checking'
    updateStatusMessage.value = ''
    try {
      const result = await window.electron?.ipcRenderer.invoke('update:check', {
        reason: manual ? 'manual' : 'startup',
      }) as UpdateCheckResult
      if (!result) {
        throw new Error('未收到更新检查结果')
      }

      const persistedForceSnapshot = loadForceUpdateSnapshot()
      const shouldHoldForceUpdate =
        Boolean(persistedForceSnapshot) &&
        compareVersions(currentVersion.value, persistedForceSnapshot!.version) < 0

      if (result.errorMessage && shouldHoldForceUpdate && persistedForceSnapshot) {
        applyForceUpdateSnapshot(persistedForceSnapshot, {
          fromPersistence: true,
          keepStatus: true,
        })
        currentVersion.value = result.currentVersion || currentVersion.value
        updateStatus.value = 'error'
        updateStatusMessage.value = `更新检查失败：${result.errorMessage}`
        return
      }

      applyUpdateResult(result, manual)
    } catch (error: any) {
      const persistedForceSnapshot = loadForceUpdateSnapshot()
      const shouldHoldForceUpdate =
        Boolean(persistedForceSnapshot) &&
        compareVersions(currentVersion.value, persistedForceSnapshot!.version) < 0

      if (shouldHoldForceUpdate && persistedForceSnapshot) {
        applyForceUpdateSnapshot(persistedForceSnapshot, {
          fromPersistence: true,
          keepStatus: true,
        })
        updateStatus.value = 'error'
        updateStatusMessage.value = error instanceof Error ? error.message : String(error)
      } else if (forceUpdateActive.value) {
        showUpdateDialog.value = false
        updateStatus.value = 'error'
        updateStatusMessage.value = error instanceof Error ? error.message : String(error)
      } else if (manual) {
        showUpdateDialog.value = true
        updateStatus.value = 'error'
        updateStatusMessage.value = error instanceof Error ? error.message : String(error)
      } else {
        updateStatus.value =
          previousStatus === 'downloaded'
            ? 'downloaded'
            : previousStatus === 'available'
              ? 'available'
              : 'idle'
        updateStatusMessage.value = ''
      }
      if (manual) {
        feedback.error(formatActionError('检查更新', error))
      }
    }
  }

  const handleManualUpdateCheck = async () => {
    if (!forceUpdateActive.value) {
      showUpdateDialog.value = true
    }
    await runUpdateCheck(true)
  }

  const handleUpdateIconClick = async () => {
    if (forceUpdateActive.value) {
      return
    }
    if (updateStatus.value === 'available' || updateStatus.value === 'downloading' || updateStatus.value === 'downloaded') {
      showUpdateDialog.value = true
      return
    }
    if (updateStatus.value === 'checking') {
      showUpdateDialog.value = true
      return
    }
    await runUpdateCheck(true)
  }

  const retryForceUpdateCheck = async () => {
    await runUpdateCheck(true)
  }

  const startUpdateDownload = async () => {
    if (!updateDownloadUrl.value) {
      feedback.warning('当前更新源缺少安装包地址，暂时无法下载')
      return
    }

    if (isMockPreviewRunning()) {
      showUpdateDialog.value = true
      updateStatus.value = 'downloading'
      updateStatusMessage.value = mockForceUpdatePreviewActive.value
        ? '正在模拟强制更新下载过程，不会请求真实安装包。'
        : '正在模拟下载过程，不会请求真实安装包。'
      downloadProgress.value = 0
      for (const percent of [9, 23, 41, 58, 76, 92, 100]) {
        await wait(180)
        downloadProgress.value = percent
      }
      downloadedFilePath.value = mockForceUpdatePreviewActive.value
        ? MOCK_FORCE_UPDATE_PREVIEW_FILE_PATH
        : MOCK_UPDATE_PREVIEW_FILE_PATH
      updateStatus.value = 'downloaded'
      updateStatusMessage.value = mockForceUpdatePreviewActive.value
        ? '模拟强制更新下载已完成，可以继续预览安装确认交互。'
        : '模拟下载已完成，可以继续预览安装确认交互。'
      feedback.success(mockForceUpdatePreviewActive.value ? '模拟强制更新下载完成，可以继续预览安装流程' : '模拟下载完成，可以继续预览安装流程')
      return
    }

    showUpdateDialog.value = true
    updateStatus.value = 'downloading'
    updateStatusMessage.value = ''
    downloadProgress.value = 0
    try {
      const result = await window.electron?.ipcRenderer.invoke('update:startDownload') as UpdateCheckResult
      if (result?.downloadedFilePath) {
        downloadedFilePath.value = result.downloadedFilePath
        updateStatus.value = 'downloaded'
        downloadProgress.value = 100
      }
    } catch (error: any) {
      updateStatus.value = forceUpdateActive.value ? 'error' : 'available'
      updateStatusMessage.value = error instanceof Error ? error.message : String(error)
      feedback.error(formatActionError('下载更新包', error))
    }
  }

  const installDownloadedUpdate = async () => {
    if (!downloadedFilePath.value) {
      feedback.warning('请先下载更新包，再执行安装')
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
      feedback.success(mockForceUpdatePreviewActive.value ? '已完成强制更新安装交互预演，真实安装未执行' : '已完成安装交互预演，真实安装未执行')
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
    downloadProgress.value = 0
    downloadedFilePath.value = ''
    updateStatusMessage.value = ''

    if (!hadMockPreview) return

    clearForceUpdateState()
    historyLoaded.value = false
    updateHistory.value = []
    if (showHistoryPanel.value) {
      await loadUpdateHistory(true)
    }
    await runUpdateCheck(false)
    if (!silent) {
      feedback.success('已恢复真实更新状态', { toast: true })
    }
  }

  const closeUpdateDialog = () => {
    showUpdateDialog.value = false
  }

  const toggleShowAllNotes = () => {
    showAllNotes.value = !showAllNotes.value
  }

  const resetUpdateUiState = () => {
    showUpdateDialog.value = false
    showHistoryPanel.value = false
    historyLoading.value = false
    historyLoaded.value = false
    historyError.value = ''
    updateHistory.value = []
    showAllNotes.value = false
    mockUpdatePreviewActive.value = false
    mockForceUpdatePreviewActive.value = false
    clearForceUpdateState()
    updateStatus.value = 'idle'
    latestVersion.value = ''
    releaseDate.value = ''
    notes.value = []
    downloadProgress.value = 0
    downloadedFilePath.value = ''
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

    const removeProgressListener = window.electron?.ipcRenderer.on('update-progress', (_event: any, payload: any) => {
      updateStatus.value = 'downloading'
      if (typeof payload?.percent === 'number' && Number.isFinite(payload.percent)) {
        downloadProgress.value = payload.percent
      }
      if (typeof payload?.version === 'string' && payload.version.trim()) {
        latestVersion.value = payload.version.trim()
      }
    })

    const removeDownloadedListener = window.electron?.ipcRenderer.on('update-downloaded', (_event: any, payload: any) => {
      updateStatus.value = 'downloaded'
      downloadProgress.value = 100
      downloadedFilePath.value = typeof payload?.filePath === 'string' ? payload.filePath : ''
      if (typeof payload?.version === 'string' && payload.version.trim()) {
        latestVersion.value = payload.version.trim()
      }
      feedback.success('更新包下载完成，可以立即安装')
    })

    const removeErrorListener = window.electron?.ipcRenderer.on('update-error', (_event: any, payload: any) => {
      if (updateStatus.value === 'downloading' || showUpdateDialog.value || forceUpdateActive.value) {
        updateStatus.value = 'error'
        updateStatusMessage.value = typeof payload?.message === 'string' ? payload.message : '更新流程发生异常'
      }
    })

    void Promise.resolve().then(() => runUpdateCheck(false))

    void removeProgressListener
    void removeDownloadedListener
    void removeErrorListener
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
    installDownloadedUpdate,
    toggleHistoryPanel,
    loadUpdateHistory,
    openReleasePage,
    applyBackendUpdateGuardStatus,
    activateMockUpdatePreview,
    activateMockForceUpdatePreview,
    resetMockUpdatePreview,
    closeUpdateDialog,
    toggleShowAllNotes,
    resetUpdateUiState,
  }
}
