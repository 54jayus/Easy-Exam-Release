import type { Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { applyPageReset } from '@/composables/useAppCacheControl'
import { open, saveAndRun } from '@/lib/dialog'
import { pythonBackend } from '@/lib/pythonBackend'

type UiLogLevel = 'info' | 'success' | 'warning' | 'error'

type Teacher = any
type Subject = any
type ScheduleSession = any
type ProctoringConfig = {
  roomCount: number
  mode: string
  balanceMode: string
  genderMix: boolean
  internalMix: boolean
}

type UseProctoringDataManagementOptions = {
  config: ProctoringConfig
  subjects: Ref<Subject[]>
  teachers: Ref<Teacher[]>
  schedule: Ref<ScheduleSession[]>
  logs: Ref<{ time: string; level: UiLogLevel; msg: string }[]>
  showLogs: Ref<boolean>
  presetVisible: Ref<boolean>
  hasPreset: Ref<boolean>
  adjustMode: Ref<boolean>
  selectedCells: Ref<{ roomId: number; c: string }[]>
  selectedSubjectId: Ref<string>
  optDetailVisible: Ref<boolean>
  optDetail: Ref<any>
  sidebarCollapsed: Ref<boolean>
  activeTab: Ref<string>
  schedulingProgress: Ref<number>
  schedulingStatus: Ref<string>
  schedulingStepText: Ref<string>
  isScheduling: Ref<boolean>
  logInfo: (msg: string) => void
  logSuccess: (msg: string) => void
  logWarning: (msg: string) => void
  logError: (msg: string) => void
  logFromText: (msg: string) => void
}

export function useProctoringDataManagement({
  config,
  subjects,
  teachers,
  schedule,
  logs,
  showLogs,
  presetVisible,
  hasPreset,
  adjustMode,
  selectedCells,
  selectedSubjectId,
  optDetailVisible,
  optDetail,
  sidebarCollapsed,
  activeTab,
  schedulingProgress,
  schedulingStatus,
  schedulingStepText,
  isScheduling,
  logInfo,
  logSuccess,
  logWarning,
  logError,
  logFromText
}: UseProctoringDataManagementOptions) {
  const resetScheduleState = () => {
    schedule.value = []
    hasPreset.value = false
    presetVisible.value = false
    adjustMode.value = false
    selectedCells.value = []
    selectedSubjectId.value = ''
    optDetailVisible.value = false
    optDetail.value = null
  }

  const handleTemplate = async () => {
    await saveAndRun({
      dialog: { filters: [{ name: 'Excel', extensions: ['xlsx'] }], defaultPath: '监考教师导入模板.xlsx' },
      run: async (path) => {
        return await pythonBackend.request('proctoring.template', { path })
      },
      successText: '教师模板下载成功',
      errorText: '教师模板下载失败',
      openFolderTitle: '教师模板下载成功',
      onLog: logFromText,
    })
  }

  const handleAddTeacher = async () => {
    const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx'] }] })
    if (!path) return

    try {
      const res = await pythonBackend.request<any>('proctoring.importTeachers', {
        path,
        config: { ...config },
        subjects: subjects.value
      })
      if (res?.errors?.length) {
        logError('导入教师失败：' + res.errors.join('；'))
        await ElMessageBox.alert(res.errors.join('\n'), '导入教师失败', { type: 'error' })
        return
      }
      if (res?.warnings?.length) {
        logWarning('导入教师警告：' + res.warnings.join('；'))
        ElMessage.warning(res.warnings[0])
      }
      if (res?.teachers?.length) {
        teachers.value = res.teachers
        logSuccess(`已导入教师：${res.teachers.length} 人`)
        ElMessage.success(`导入成功，共 ${res.teachers.length} 人`)
      } else {
        logError('导入教师失败：未返回教师数据')
        ElMessage.error('导入教师失败：未返回教师数据')
      }
    } catch (e) {
      ElMessage.error('导入失败: ' + e)
    }
  }

  const handlePresetDialog = () => {
    presetVisible.value = true
  }

  const handleClearTeachers = async () => {
    try {
      await ElMessageBox.confirm(
        '确定要清除已导入的教师数据吗？这将同时清空当前监考安排与预设状态。',
        '清除教师数据',
        { type: 'warning', confirmButtonText: '清除', cancelButtonText: '取消' }
      )
    } catch {
      return
    }
    try {
      await pythonBackend.request('proctoring.clearState', {
        clearTeachers: true,
        clearSchedule: true,
        clearConfig: false
      })
    } catch (e) {
      logWarning('清除后端状态失败：' + (e instanceof Error ? e.message : String(e)))
    }
    teachers.value = []
    schedule.value = []
    hasPreset.value = false
    resetScheduleState()
    logInfo('已清除教师数据')
  }

  const handleClearPreset = async () => {
    try {
      await ElMessageBox.confirm(
        '确定要清除已导入的预设监考安排吗？这将清空当前监考安排。',
        '清除预设监考',
        { type: 'warning', confirmButtonText: '清除', cancelButtonText: '取消' }
      )
    } catch {
      return
    }
    try {
      await pythonBackend.request('proctoring.clearState', {
        clearTeachers: false,
        clearSchedule: true,
        clearConfig: false
      })
    } catch (e) {
      logWarning('清除后端状态失败：' + (e instanceof Error ? e.message : String(e)))
    }
    hasPreset.value = false
    resetScheduleState()
    logInfo('已清除预设监考安排')
  }

  const handleClearSchedule = async () => {
    try {
      await ElMessageBox.confirm(
        '确定要清除当前监考编排结果吗？（不会清除教师与科目信息）',
        '清除当前编排',
        { type: 'warning', confirmButtonText: '清除', cancelButtonText: '取消' }
      )
    } catch {
      return
    }
    resetScheduleState()
    logInfo('已清除当前监考编排')
  }

  const handleResetPage = async () => {
    try {
      await ElMessageBox.confirm(
        '确定要初始化当前页面吗？这将清除所有数据与设置（教师、科目、编排、预设、日志、参数等）。',
        '初始化页面',
        { type: 'warning', confirmButtonText: '初始化', cancelButtonText: '取消' }
      )
    } catch {
      return
    }

    try {
      await pythonBackend.request('proctoring.clearState')
    } catch (e) {
      logWarning('初始化后端状态失败：' + (e instanceof Error ? e.message : String(e)))
    }

    subjects.value = []
    teachers.value = []
    logs.value = []
    showLogs.value = false

    resetScheduleState()

    config.roomCount = 0
    config.mode = 'single'
    config.balanceMode = 'duration'
    config.genderMix = false
    config.internalMix = false

    sidebarCollapsed.value = false
    activeTab.value = 'overview'

    schedulingProgress.value = 0
    schedulingStatus.value = ''
    schedulingStepText.value = ''
    isScheduling.value = false

    applyPageReset('proctoring')
    ElMessage.success('页面已初始化')
  }

  const handleGenerateEmptyTemplate = async () => {
    await saveAndRun({
      dialog: { filters: [{ name: 'Excel', extensions: ['xlsx'] }], defaultPath: '预设监考模板.xlsx' },
      run: async (path) => {
        return await pythonBackend.request('proctoring.export_empty_preset', {
          path,
          subjects: subjects.value,
          roomCount: config.roomCount,
          mode: config.mode
        })
      },
      successText: '预设模板下载成功',
      errorText: '预设模板下载失败',
      openFolderTitle: '预设模板下载成功',
      onLog: logFromText,
    })
  }

  const handleImportPreset = async () => {
    const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx'] }] })
    if (!path) return

    const importPreset = async () => {
      return await pythonBackend.request<any>('proctoring.import_preset', {
        path,
        teachers: teachers.value,
        subjects: subjects.value,
        config: { ...config }
      })
    }

    try {
      const res = await importPreset()

      const mismatch = res?.modeMismatch
      if (res?.error && mismatch?.detected && mismatch?.current && mismatch?.detected !== mismatch?.current) {
        const detectedMode = String(mismatch.detected)
        const modeText = detectedMode === 'double' ? '双人监考' : '单人监考'
        try {
          await ElMessageBox.confirm(
            `检测到导入的表格为${modeText}模式，是否切换到${modeText}并继续导入？`,
            '导入预设安排',
            { type: 'warning', confirmButtonText: '切换并导入', cancelButtonText: '取消' }
          )
        } catch {
          logInfo('已取消导入预设安排：未切换模式')
          await ElMessageBox.alert(res.error, '导入预设安排失败', { type: 'error' })
          return
        }

        config.mode = detectedMode
        const retryRes = await importPreset()
        if (retryRes?.error) {
          logError('导入预设安排失败：' + retryRes.error)
          await ElMessageBox.alert(retryRes.error, '导入预设安排失败', { type: 'error' })
          return
        }
        if (retryRes?.schedule) {
          schedule.value = retryRes.schedule
          if (retryRes.teachers) teachers.value = retryRes.teachers
          if (retryRes.detectedRoomCount) config.roomCount = retryRes.detectedRoomCount
          hasPreset.value = true
          logSuccess('导入预设安排成功')
          presetVisible.value = false
          return
        }
      }

      if (res?.error) {
        logError('导入预设安排失败：' + res.error)
        await ElMessageBox.alert(res.error, '导入预设安排失败', { type: 'error' })
        return
      }
      if (res?.schedule) {
        schedule.value = res.schedule
        if (res.teachers) teachers.value = res.teachers
        if (res.detectedRoomCount) config.roomCount = res.detectedRoomCount
        hasPreset.value = true
        logSuccess('导入预设安排成功')
        presetVisible.value = false
      }
    } catch (e) {
      ElMessage.error('导入失败: ' + e)
    }
  }

  const handleImportSchedule = async () => {
    const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx'] }] })
    if (!path) return

    try {
      const res = await pythonBackend.request<any>('proctoring.importSchedule', {
        path,
        teachers: teachers.value,
        subjects: subjects.value,
        config
      })
      if (res.schedule) {
        schedule.value = res.schedule
        teachers.value = res.teachers
        logSuccess('导入安排成功')
      }
    } catch (e) {
      ElMessage.error('导入失败: ' + e)
    }
  }

  const handleExport = async () => {
    await saveAndRun({
      dialog: { filters: [{ name: 'Excel', extensions: ['xlsx'] }], defaultPath: '监考安排.xlsx' },
      run: async (path) => {
        return await pythonBackend.request('proctoring.export', {
          path,
          teachers: teachers.value,
          subjects: subjects.value,
          schedule: schedule.value,
          config
        })
      },
      successText: '导出成功',
      errorText: '导出失败',
      openFolderTitle: '导出成功',
      onLog: logFromText,
    })
  }

  return {
    handleTemplate,
    handleAddTeacher,
    handlePresetDialog,
    handleClearTeachers,
    handleClearPreset,
    handleClearSchedule,
    handleResetPage,
    handleGenerateEmptyTemplate,
    handleImportPreset,
    handleImportSchedule,
    handleExport,
  }
}
