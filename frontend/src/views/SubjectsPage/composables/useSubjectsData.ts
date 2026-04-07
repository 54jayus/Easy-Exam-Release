import type { Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { open, saveAndRun } from '@/lib/dialog'
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
  const syncToBackend = async () => {
    try {
      const res = await pythonBackend.request<any>('subjects.update', { subjects: subjects.value })
      if (res?.proctoringReset) {
        ElMessage.warning('科目已更新，原监考编排结果已自动清除')
        logInfo('科目变更，监考编排结果已自动重置')
      }
    } catch (e) {
      logger.error('同步科目数据失败', e)
    }
  }

  const loadFromBackend = async () => {
    try {
      const res = await pythonBackend.request<any>('subjects.list')
      if (res && res.subjects) {
        subjects.value = res.subjects as Subject[]
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
        ElMessage.warning(`发现 ${res.errors.length} 个潜在问题`)
        logWarning(`数据校验发现 ${res.errors.length} 个问题`)
      } else {
        logSuccess('数据校验通过')
      }
    } catch (err) {
      logger.error('数据校验失败', err)
    }
  }

  const handleImport = async () => {
    try {
      logInfo('正在打开文件选择器')
      const selected = await open({
        multiple: false,
        filters: [{ name: 'Excel Files', extensions: ['xlsx', 'xls'] }],
      })

      if (!selected) return

      logInfo(`已选择文件：${selected}`)
      loading.value = true
      logInfo('正在导入科目数据')
      const res = await pythonBackend.request<any>('subjects.import', {
        path: selected,
      })

      if (res.subjects && res.subjects.length > 0) {
        subjects.value = res.subjects
        importedFromFile.value = true
        ElMessage.success(`成功导入 ${res.subjects.length} 个科目`)
        logSuccess(`成功导入 ${res.subjects.length} 个科目`)
        if (res.proctoringReset) {
          ElMessage.warning('科目已更新，原监考编排结果已自动清除')
          logInfo('科目变更，监考编排结果已自动重置')
        }
      }

      validationErrors.value = res.errors
      if (res.errors.length > 0) {
        showErrors.value = true
        logError(`导入发现 ${res.errors.length} 个错误`)
      }
    } catch (err) {
      ElMessage.error(`导入失败：${String(err)}`)
      logError(`导入失败：${String(err)}`)
    } finally {
      loading.value = false
    }
  }

  const handleExport = async () => {
    if (subjects.value.length === 0) {
      ElMessage.warning('没有数据可导出')
      return
    }

    logInfo('正在打开文件保存对话框')
    await saveAndRun({
      dialog: {
        filters: [{ name: 'Excel Files', extensions: ['xlsx'] }],
        defaultPath: '科目信息.xlsx',
      },
      run: async (path) => {
        logInfo('正在导出科目数据')
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
    logInfo('正在打开文件保存对话框')
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
