import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { pythonBackend } from '@/lib/pythonBackend'
import { createUiFeedback, formatActionError } from '@/lib/uiFeedback'
import {
  type BackendUpdateGuardStatus,
  type UpdateCheckResult,
  type UpdateHistoryEntry,
  type UpdateStatus,
} from '@/types/appUpdate'
import { createStatusDisplayComputed } from '@/composables/updateStatusDisplayMap'
import { useUpdateMockPreview } from '@/composables/useUpdateMockPreview'
import { useForceUpdate } from '@/composables/useForceUpdate'

const SILENT_UPDATE_CHECK_INTERVAL_MS = 10 * 60 * 1000
const SKIPPED_VERSION_KEY = 'easy_exam_skipped_version'
const REMIND_LATER_KEY = 'easy_exam_remind_later'

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
  const backgroundDownloadActive = ref(false)
  const skippedVersion = ref(localStorage.getItem(SKIPPED_VERSION_KEY) || '')
  const remindLaterUntil = ref(Number(localStorage.getItem(REMIND_LATER_KEY)) || 0)

  let silentCheckTimer: ReturnType<typeof setInterval> | null = null
  let removeProgressListener: (() => void) | undefined
  let removeDownloadedListener: (() => void) | undefined
  let removeErrorListener: (() => void) | undefined

  const normalizeVersion = (value: unknown) =>
    typeof value === 'string' ? value.trim() : ''

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

  const skipCurrentVersion = () => {
    const version = latestVersion.value
    if (!version) return
    skippedVersion.value = version
    localStorage.setItem(SKIPPED_VERSION_KEY, version)
    updateStatus.value = 'idle'
    updateStatusMessage.value = ''
    showUpdateDialog.value = false
    feedback.info(`已忽略版本 v${version}，后续版本仍会提醒`, { toast: true })
  }

  const remindLater = (hours = 4) => {
    const until = Date.now() + hours * 60 * 60 * 1000
    remindLaterUntil.value = until
    localStorage.setItem(REMIND_LATER_KEY, String(until))
    showUpdateDialog.value = false
    feedback.info(`${hours} 小时后将再次提醒更新`, { toast: true })
  }

  const isVersionSkipped = (version: string) => {
    return Boolean(version && skippedVersion.value && version === skippedVersion.value)
  }

  const isInRemindCooldown = () => {
    return remindLaterUntil.value > 0 && Date.now() < remindLaterUntil.value
  }

  // Force update composable
  const forceUpdate = useForceUpdate({
    currentVersion,
    latestVersion,
    releaseDate,
    notes,
    updateDownloadUrl,
    updateStatus,
    updateStatusMessage,
    showUpdateDialog,
    downloadedFilePath,
    downloadedVersion,
    downloadProgress,
    hasMatchingDownloadedPackage,
    clearDownloadedArtifact,
  })

  const {
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
    clearForceUpdateSnapshot,
  } = forceUpdate

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
      const version = result.latestVersion || ''
      if (!manual && isVersionSkipped(version)) {
        updateStatus.value = 'idle'
        return
      }
      updateStatus.value = hasMatchingDownloadedPackage(version) ? 'downloaded' : 'available'
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

  // Mock preview composable
  const mock = useUpdateMockPreview({
    currentVersion,
    updateStatus,
    downloadProgress,
    downloadedFilePath,
    downloadedVersion,
    backgroundDownloadActive,
    showUpdateDialog,
    updateStatusMessage,
    historyLoaded,
    historyError,
    updateHistory,
    showHistoryPanel,
    hasMatchingDownloadedPackage,
    setDownloadedArtifact,
    clearDownloadedArtifact,
    clearActiveDownloadTarget,
    resolveTargetVersion,
    applyOrdinaryUpdateResult,
    applyForceUpdateActive,
    createForceUpdateSnapshotFromResult,
    clearForceUpdateState,
    clearForceUpdateSnapshot,
    syncBackendUpdateStatus: async (source, forceRefresh) => {
      await syncBackendUpdateStatus(source, forceRefresh)
    },
    feedback,
  })

  const {
    mockUpdatePreviewActive,
    mockForceUpdatePreviewActive,
    isMockPreviewRunning,
  } = mock

  const {
    updateTooltip,
    updateStatusTitle,
    updateStatusDescription,
    updateStatusChipText,
    updateStatusChipClass,
    updateStatusPanelClass,
    updateStatusTitleClass,
  } = createStatusDisplayComputed({
    updateStatus,
    isForceUpdateMode,
    forceUpdateActive,
    forceUpdatePending,
    backgroundDownloadActive,
    updateDownloadUrl,
    mockUpdatePreviewActive,
  })

  const showUpdateBadge = computed(() =>
    isForceUpdateMode.value || ['available', 'downloading', 'paused', 'downloaded'].includes(updateStatus.value)
  )

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

  const maxVisibleNotes = computed(() => 4)

  const visibleNotes = computed(() =>
    showAllNotes.value || notes.value.length <= maxVisibleNotes.value ? notes.value : notes.value.slice(0, maxVisibleNotes.value)
  )

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
      const version = status.latestVersion || ''
      if (source !== 'manual' && isVersionSkipped(version)) {
        updateStatus.value = 'idle'
        return
      }
      updateStatus.value = hasMatchingDownloadedPackage(version) ? 'downloaded' : 'available'
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

    if (source === 'silent' && isInRemindCooldown()) {
      return
    }

    if (mock.mockForceUpdatePreviewActive.value) {
      mock.applyMockForceUpdateResult(source === 'manual')
      return
    }

    if (mock.mockUpdatePreviewActive.value) {
      applyOrdinaryUpdateResult(mock.createMockUpdateResult(), source === 'manual')
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
      mock.mockDownloadPaused.value = true
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
      return mock.executeMockDownload(background)
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
      mock.executeMockInstall()
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
      updateHistory.value = mock.mergeMockUpdateHistory(Array.isArray(result) ? result : [])
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
    await mock.resetMockUpdatePreview(silent)
    if (showHistoryPanel.value) {
      await loadUpdateHistory(true)
    }
  }

  const closeUpdateDialog = () => {
    showUpdateDialog.value = false
    if (updateStatus.value === 'downloading') {
      backgroundDownloadActive.value = true
      if (!isForceUpdateMode.value) {
        updateStatusMessage.value = '更新包正在后台下载，你可以继续使用软件。'
      }
    }
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
    mock.mockUpdatePreviewActive.value = false
    mock.mockForceUpdatePreviewActive.value = false
    mock.mockDownloadPaused.value = false
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
    maxVisibleNotes,
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
    activateMockUpdatePreview: mock.activateMockUpdatePreview,
    activateMockForceUpdatePreview: mock.activateMockForceUpdatePreview,
    resetMockUpdatePreview,
    closeUpdateDialog,
    toggleShowAllNotes,
    resetUpdateUiState,
    skipCurrentVersion,
    remindLater,
  }
}
