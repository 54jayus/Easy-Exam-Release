import { ElMessage, ElMessageBox } from 'element-plus'
import { applyPageReset } from '@/composables/useAppCacheControl'
import { pythonBackend } from '@/lib/pythonBackend'
import type { UiLogEntry } from '../types'

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
  const handleClearImport = async () => {
    try {
      await ElMessageBox.confirm('确定要清除所有科目数据吗？', '清除科目数据', {
        type: 'warning',
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
    logInfo('已清除科目数据')
  }

  const handleResetPage = async () => {
    try {
      await ElMessageBox.confirm(
        '确定要初始化当前页面吗？这将清除所有数据与设置（科目数据、校验状态、日志、视图偏好等）。',
        '初始化页面',
        { type: 'warning', confirmButtonText: '初始化', cancelButtonText: '取消' },
      )
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
      logWarning('初始化时同步科目数据失败，重新进入页面时可能恢复旧状态')
    }

    try {
      await pythonBackend.request('proctoring.clearState')
    } catch (e) {
      logger.error('初始化时重置监考编排失败', e)
      logWarning('初始化时重置监考编排失败，重新进入页面时可能恢复旧状态')
    }

    applyPageReset('subjects')
    logSuccess('页面已初始化，相关监考与打印依赖已同步失效')
    ElMessage.success('页面已初始化，相关监考与打印依赖已同步失效')
  }

  return {
    handleClearImport,
    handleResetPage,
  }
}
