import type { Ref } from 'vue'
import { ref } from 'vue'
import { buildMockDownloadProgressSteps } from '@/lib/versionUtils'
import type { ForceUpdateSnapshot, UpdateCheckResult, UpdateHistoryEntry, UpdateStatus } from '@/types/appUpdate'

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

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export function useUpdateMockPreview(params: {
  currentVersion: Ref<string>
  updateStatus: Ref<UpdateStatus>
  downloadProgress: Ref<number>
  downloadedFilePath: Ref<string>
  downloadedVersion: Ref<string>
  backgroundDownloadActive: Ref<boolean>
  showUpdateDialog: Ref<boolean>
  updateStatusMessage: Ref<string>
  historyLoaded: Ref<boolean>
  historyError: Ref<string>
  updateHistory: Ref<UpdateHistoryEntry[]>
  showHistoryPanel: Ref<boolean>
  hasMatchingDownloadedPackage: (version: string) => boolean
  setDownloadedArtifact: (filePath: string, version: string) => void
  clearDownloadedArtifact: (resetProgress?: boolean) => void
  clearActiveDownloadTarget: () => void
  resolveTargetVersion: (fallback?: string) => string
  applyOrdinaryUpdateResult: (result: UpdateCheckResult, manual: boolean) => void
  applyForceUpdateActive: (snapshot: ForceUpdateSnapshot, options?: { fromPersistence?: boolean; message?: string }) => void
  createForceUpdateSnapshotFromResult: (result: UpdateCheckResult) => ForceUpdateSnapshot | null
  clearForceUpdateState: (clearPersisted?: boolean) => void
  clearForceUpdateSnapshot: () => void
  syncBackendUpdateStatus: (source: 'startup' | 'silent' | 'manual', forceRefresh?: boolean) => Promise<void>
  feedback: {
    success: (message: string, options?: { toast?: boolean }) => void
    warning: (message: string, options?: { toast?: boolean }) => void
  }
}) {
  const mockUpdatePreviewActive = ref(false)
  const mockForceUpdatePreviewActive = ref(false)
  const mockDownloadPaused = ref(false)

  const isMockPreviewRunning = () => mockUpdatePreviewActive.value || mockForceUpdatePreviewActive.value

  const createMockUpdateResult = (mandatory = false): UpdateCheckResult => {
    const version = mandatory ? MOCK_FORCE_UPDATE_PREVIEW_VERSION : MOCK_UPDATE_PREVIEW_VERSION
    return {
      currentVersion: params.currentVersion.value,
      latestVersion: version,
      hasUpdate: true,
      enabled: true,
      releaseDate: mandatory ? MOCK_FORCE_UPDATE_PREVIEW_DATE : MOCK_UPDATE_PREVIEW_DATE,
      notes: mandatory ? [...MOCK_FORCE_UPDATE_PREVIEW_NOTES] : [...MOCK_UPDATE_PREVIEW_NOTES],
      mandatory,
      url: mandatory ? MOCK_FORCE_UPDATE_PREVIEW_URL : MOCK_UPDATE_PREVIEW_URL,
      downloadedFilePath:
        params.hasMatchingDownloadedPackage(version) && params.downloadedFilePath.value
          ? params.downloadedFilePath.value
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

  const applyMockForceUpdateResult = (manual: boolean) => {
    const result = createMockUpdateResult(true)
    const snapshot = params.createForceUpdateSnapshotFromResult(result)
    if (snapshot) {
      params.applyForceUpdateActive(snapshot, {
        message: '当前为开发者强制更新预演模式，下载与安装均不会触发真实更新。',
      })
    }
    params.currentVersion.value = result.currentVersion || params.currentVersion.value
    if (result.downloadedFilePath) {
      params.setDownloadedArtifact(result.downloadedFilePath, result.latestVersion || '')
    } else {
      params.clearDownloadedArtifact(true)
    }
    if (manual) {
      params.feedback.warning('已切换到强制更新预演模式', { toast: true })
    }
  }

  const activateMockUpdatePreview = async () => {
    const hadLoadedHistory = params.historyLoaded.value
    mockUpdatePreviewActive.value = true
    mockForceUpdatePreviewActive.value = false
    params.clearForceUpdateState(false)
    params.historyError.value = ''
    params.showHistoryPanel.value = false
    params.updateStatusMessage.value = '当前为开发者预演模式，下载与安装均不会触发真实更新。'
    params.applyOrdinaryUpdateResult(createMockUpdateResult(), true)
    if (hadLoadedHistory) {
      params.updateHistory.value = mergeMockUpdateHistory(params.updateHistory.value)
      params.historyLoaded.value = true
    } else {
      params.historyLoaded.value = false
    }
    params.feedback.success('已切换到新版本更新预演模式', { toast: true })
  }

  const activateMockForceUpdatePreview = async () => {
    const hadLoadedHistory = params.historyLoaded.value
    mockUpdatePreviewActive.value = false
    mockForceUpdatePreviewActive.value = true
    params.historyError.value = ''
    params.showHistoryPanel.value = false
    applyMockForceUpdateResult(true)
    params.clearForceUpdateSnapshot()
    if (hadLoadedHistory) {
      params.updateHistory.value = mergeMockUpdateHistory(params.updateHistory.value)
      params.historyLoaded.value = true
    } else {
      params.historyLoaded.value = false
    }
  }

  const executeMockDownload = async (background: boolean) => {
    const wasPaused = params.updateStatus.value === 'paused'
    params.backgroundDownloadActive.value = background
    params.showUpdateDialog.value = !background
    params.updateStatus.value = 'downloading'
    mockDownloadPaused.value = false
    params.updateStatusMessage.value = mockForceUpdatePreviewActive.value
      ? background
        ? '正在后台模拟强制更新下载过程，不会请求真实安装包。'
        : '正在模拟强制更新下载过程，不会请求真实安装包。'
      : background
        ? '正在后台模拟下载过程，不会请求真实安装包。'
        : '正在模拟下载过程，不会请求真实安装包。'
    if (!wasPaused) {
      params.downloadProgress.value = 0
    }
    const currentProgress = params.downloadProgress.value
    const progressSteps = buildMockDownloadProgressSteps(MOCK_DOWNLOAD_PROGRESS_STEP_COUNT)
    const stepDelay = Math.max(1, Math.round(MOCK_DOWNLOAD_TOTAL_DURATION_MS / progressSteps.length))
    for (const percent of progressSteps) {
      if (percent <= currentProgress) continue
      if (mockDownloadPaused.value) {
        params.updateStatus.value = 'paused'
        params.updateStatusMessage.value = '下载已暂停，可稍后继续'
        params.backgroundDownloadActive.value = false
        return
      }
      await wait(stepDelay)
      params.downloadProgress.value = percent
    }
    const targetVersion = params.resolveTargetVersion()
    params.setDownloadedArtifact(
      mockForceUpdatePreviewActive.value
        ? MOCK_FORCE_UPDATE_PREVIEW_FILE_PATH
        : MOCK_UPDATE_PREVIEW_FILE_PATH,
      targetVersion || (mockForceUpdatePreviewActive.value
        ? MOCK_FORCE_UPDATE_PREVIEW_VERSION
        : MOCK_UPDATE_PREVIEW_VERSION)
    )
    params.backgroundDownloadActive.value = false
    params.showUpdateDialog.value = true
    params.updateStatus.value = 'downloaded'
    params.updateStatusMessage.value = mockForceUpdatePreviewActive.value
      ? background
        ? '后台模拟强制更新下载已完成，可以继续预览安装确认交互。'
        : '模拟强制更新下载已完成，可以继续预览安装确认交互。'
      : background
        ? '后台模拟下载已完成，可以继续预览安装确认交互。'
        : '模拟下载已完成，可以继续预览安装确认交互。'
    params.feedback.success(
      mockForceUpdatePreviewActive.value
        ? background
          ? '后台模拟强制更新下载完成，可以继续预览安装流程'
          : '模拟强制更新下载完成，可以继续预览安装流程'
        : background
          ? '后台模拟下载完成，可以继续预览安装流程'
          : '模拟下载完成，可以继续预览安装流程'
    )
  }

  const executeMockInstall = () => {
    params.updateStatusMessage.value = mockForceUpdatePreviewActive.value
      ? '本次为开发者强制更新预演模式，已跳过真实安装程序启动。'
      : '本次为开发者预演模式，已跳过真实安装程序启动。'
    params.feedback.success(
      mockForceUpdatePreviewActive.value
        ? '已完成强制更新安装交互预演，真实安装未执行'
        : '已完成安装交互预演，真实安装未执行'
    )
  }

  const resetMockUpdatePreview = async (silent = false) => {
    const hadMockPreview = isMockPreviewRunning()
    mockUpdatePreviewActive.value = false
    mockForceUpdatePreviewActive.value = false
    mockDownloadPaused.value = false
    params.backgroundDownloadActive.value = false
    params.clearActiveDownloadTarget()
    params.downloadProgress.value = 0
    params.clearDownloadedArtifact()
    params.updateStatusMessage.value = ''

    if (!hadMockPreview) return

    params.clearForceUpdateState()
    params.historyLoaded.value = false
    params.updateHistory.value = []
    if (params.showHistoryPanel.value) {
      // reload history will be handled by the caller
    }
    await params.syncBackendUpdateStatus('startup', false)
    if (!silent) {
      params.feedback.success('已恢复真实更新状态', { toast: true })
    }
  }

  const getMockForceUpdatePreviewVersion = () => MOCK_FORCE_UPDATE_PREVIEW_VERSION

  return {
    mockUpdatePreviewActive,
    mockForceUpdatePreviewActive,
    mockDownloadPaused,
    isMockPreviewRunning,
    createMockUpdateResult,
    createMockUpdateHistoryEntry,
    mergeMockUpdateHistory,
    applyMockForceUpdateResult,
    activateMockUpdatePreview,
    activateMockForceUpdatePreview,
    executeMockDownload,
    executeMockInstall,
    resetMockUpdatePreview,
    getMockForceUpdatePreviewVersion,
  }
}
