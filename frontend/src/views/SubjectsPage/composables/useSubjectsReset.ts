import { applyPageReset } from '@/composables/useAppCacheControl'
import type { UiLogEntry } from '@/composables/useUiLogs'
import {
  createUiFeedback,
  formatActionSuccess,
  formatActionWarning,
} from '@/lib/uiFeedback'
import { pythonBackend } from '@/lib/pythonBackend'

interface LoggerLike {
  error: (msg: string, err?: unknown) => void
}

interface UseSubjectsResetOptions {
  subjects: { value: unknown[] }
  importedFromFile: { value: boolean }
  validationErrors: { value: string[] }
  showErrors: { value: boolean }
  showLogs: { value: boolean }
  logs: { value: UiLogEntry[] }
  loading: { value: boolean }
  viewMode: { value: string }
  sidebarCollapsed: { value: boolean }
  logger: LoggerLike
  logInfo: (msg: string) => void
  logWarning: (msg: string) => void
  logSuccess: (msg: string) => void
  resetFormState: () => void
}

export function useSubjectsReset({
  subjects,
  importedFromFile,
  validationErrors,
  showErrors,
  showLogs,
  logs,
  loading,
  viewMode,
  sidebarCollapsed,
  logger,
  logInfo,
  logWarning,
  logSuccess,
  resetFormState,
}: UseSubjectsResetOptions) {
  const feedback = createUiFeedback({ logInfo, logWarning, logSuccess })

  const handleClearImport = async () => {
    try {
      await feedback.confirmWarning({
        message: '确定要清除所有科目数据吗？',
        title: '清除科目数据',
        confirmButtonText: '清除',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }

    subjects.value = []
    importedFromFile.value = false
    validationErrors.value = []
    await pythonBackend.request('subjects.update', { subjects: [] })
    logSuccess(formatActionSuccess('清除科目数据'))
  }

  const handleResetPage = async () => {
    try {
      await feedback.confirmWarning({
        message: '确定要初始化当前页面吗？这将清除所有数据与设置（科目数据、校验状态、日志、视图偏好等）。',
        title: '初始化页面',
        confirmButtonText: '初始化',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }

    subjects.value = []
    importedFromFile.value = false
    validationErrors.value = []
    showErrors.value = false
    showLogs.value = false
    logs.value = []
    loading.value = false

    resetFormState()

    viewMode.value = 'grid'
    sidebarCollapsed.value = false

    try {
      await pythonBackend.request('subjects.update', { subjects: [] })
    } catch (e) {
      logger.error('初始化时同步科目数据失败', e)
      logWarning(formatActionWarning('初始化页面', '同步科目数据失败，重新进入页面时可能恢复旧状态'))
    }

    try {
      await pythonBackend.request('proctoring.clearState')
    } catch (e) {
      logger.error('初始化时重置监考编排失败', e)
      logWarning(formatActionWarning('初始化页面', '重置监考编排失败，重新进入页面时可能恢复旧状态'))
    }

    applyPageReset('subjects')
    feedback.success('页面已初始化，相关监考与打印依赖已同步失效', {
      logMessage: formatActionSuccess('初始化页面', '相关监考与打印依赖已同步失效'),
    })
  }

  return {
    handleClearImport,
    handleResetPage,
  }
}
