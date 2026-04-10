import type { Ref } from 'vue'
import { open, saveAndRun } from '@/lib/dialog'
import {
  createUiFeedback,
  formatActionError,
  formatActionProgress,
  formatActionSuccess,
  formatActionWarning,
} from '@/lib/uiFeedback'
import { pythonBackend } from '@/lib/pythonBackend'
import type { Subject } from '../types'

type LogFn = (msg: string) => void

interface UseSubjectsDataOptions {
  subjects: Ref<Subject[]>
  importedFromFile: Ref<boolean>
  validationErrors: Ref<string[]>
  showErrors: Ref<boolean>
  loading: Ref<boolean>
  logInfo: LogFn
  logSuccess: LogFn
  logWarning: LogFn
  logError: LogFn
  logFromText: LogFn
  logger: {
    error: (msg: string, err?: unknown) => void
  }
}

export function useSubjectsData({
  subjects,
  importedFromFile,
  validationErrors,
  showErrors,
  loading,
  logInfo,
  logSuccess,
  logWarning,
  logError,
  logFromText,
  logger,
}: UseSubjectsDataOptions) {
  const feedback = createUiFeedback({ logInfo, logSuccess, logWarning, logError })

  const normalizeSubjects = (items: any[]): Subject[] =>
    (items || []).map((subject: any) => ({
      ...subject,
      room_count: Number(subject?.room_count ?? subject?.roomCount ?? 0) || 0,
    }))

  const syncToBackend = async () => {
    try {
      const res = await pythonBackend.request<any>('subjects.update', { subjects: subjects.value })
      if (res?.proctoringReset) {
        feedback.warning('科目已更新，原监考编排结果已自动清除', {
          logMessage: formatActionWarning('科目同步', '监考编排结果已自动清除'),
        })
      }
    } catch (e) {
      logger.error('同步科目数据失败', e)
    }
  }

  const loadFromBackend = async () => {
    try {
      const res = await pythonBackend.request<any>('subjects.list')
      if (res && res.subjects) {
        subjects.value = normalizeSubjects(res.subjects)
        if (res.subjects.length > 0) importedFromFile.value = true
      }
    } catch (e) {
      logger.error('读取科目数据失败', e)
    }
  }

  const validateData = async () => {
    if (subjects.value.length === 0) {
      validationErrors.value = []
      return
    }

    try {
      const res = await pythonBackend.request<any>('subjects.validate', {
        subjects: subjects.value,
      })
      validationErrors.value = res.errors
      if (res.errors.length > 0) {
        feedback.warning(`发现 ${res.errors.length} 个潜在问题`, {
          logMessage: formatActionWarning('数据校验', `发现 ${res.errors.length} 个潜在问题`),
        })
      } else {
        logSuccess(formatActionSuccess('完成数据校验'))
      }
    } catch (err) {
      logger.error('数据校验失败', err)
    }
  }

  const handleImport = async () => {
    try {
      logInfo(formatActionProgress('打开文件选择器'))
      const selected = await open({
        multiple: false,
        filters: [{ name: 'Excel Files', extensions: ['xlsx', 'xls'] }],
      })

      if (!selected) return

      logInfo(`已选择文件：${selected}`)
      loading.value = true
      logInfo(formatActionProgress('导入科目数据'))
      const res = await pythonBackend.request<any>('subjects.import', {
        path: selected,
      })

      if (res.subjects && res.subjects.length > 0) {
        subjects.value = normalizeSubjects(res.subjects)
        importedFromFile.value = true
        feedback.success(`成功导入 ${res.subjects.length} 个科目`, {
          logMessage: formatActionSuccess('导入科目', `${res.subjects.length} 个`),
        })
        if (res.proctoringReset) {
          feedback.warning('科目已更新，原监考编排结果已自动清除', {
            logMessage: formatActionWarning('导入科目', '监考编排结果已自动清除'),
          })
        }
      }

      validationErrors.value = res.errors
      if (res.errors.length > 0) {
        showErrors.value = true
        logWarning(formatActionWarning('导入科目', `发现 ${res.errors.length} 个问题`))
      }
    } catch (err) {
      feedback.error(formatActionError('导入科目', err))
    } finally {
      loading.value = false
    }
  }

  const handleExport = async () => {
    if (subjects.value.length === 0) {
      feedback.warning('暂无可导出的科目数据', {
        log: false,
      })
      return
    }

    logInfo(formatActionProgress('打开文件保存对话框'))
    await saveAndRun({
      dialog: {
        filters: [{ name: 'Excel Files', extensions: ['xlsx'] }],
        defaultPath: '科目信息.xlsx',
      },
      run: async (path) => {
        logInfo(formatActionProgress('导出科目数据'))
        return await pythonBackend.request('subjects.export', {
          path,
          subjects: subjects.value,
        })
      },
      successText: '导出成功',
      errorText: '导出失败',
      openFolderTitle: '导出成功',
      onLog: logFromText,
    })
  }

  const handleTemplate = async () => {
    logInfo(formatActionProgress('打开文件保存对话框'))
    await saveAndRun({
      dialog: {
        filters: [{ name: 'Excel Files', extensions: ['xlsx'] }],
        defaultPath: '科目导入模板.xlsx',
      },
      run: async (path) => {
        return await pythonBackend.request('subjects.template', { path })
      },
      successText: '模板下载成功',
      errorText: '模板下载失败',
      openFolderTitle: '模板下载成功',
      onLog: logFromText,
    })
  }

  return {
    syncToBackend,
    loadFromBackend,
    validateData,
    handleImport,
    handleExport,
    handleTemplate,
  }
}
