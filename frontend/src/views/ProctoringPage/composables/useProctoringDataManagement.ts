import type { Ref } from 'vue'
import { applyPageReset } from '@/composables/useAppCacheControl'
import type { UiLogEntry } from '@/composables/useUiLogs'
import { open, saveAndRun } from '@/lib/dialog'
import {
  createUiFeedback,
  formatActionError,
  formatActionSuccess,
  formatActionWarning,
} from '@/lib/uiFeedback'
import { pythonBackend } from '@/lib/pythonBackend'

type Teacher = any
type Subject = any
type ScheduleSession = any
type ProctoringConfig = {
  roomCount: number
  mode: string
  balanceMode: string
  genderMix: boolean
  internalMix: boolean
  roomRepeatPreference?: string
  avoidConsecutiveSessions?: boolean
}

type UseProctoringDataManagementOptions = {
  config: ProctoringConfig
  subjects: Ref<Subject[]>
  teachers: Ref<Teacher[]>
  schedule: Ref<ScheduleSession[]>
  logs: Ref<UiLogEntry[]>
  showLogs: Ref<boolean>
  presetVisible: Ref<boolean>
  hasPreset: Ref<boolean>
  adjustMode: Ref<boolean>
  selectedCells: Ref<{ roomId: number; c: string }[]>
  selectedSubjectId: Ref<string>
  optDetailVisible: Ref<boolean>
  optDetail: Ref<any>
  sidebarCollapsed: Ref<boolean>
  advancedSettingsVisible: Ref<boolean>
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
  advancedSettingsVisible,
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
  const feedback = createUiFeedback({ logInfo, logSuccess, logWarning, logError })

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
        await feedback.alertError('导入教师失败', res.errors.join('\n'), {
          logMessage: formatActionError('导入教师', res.errors.join('；')),
        })
        return
      }
      if (res?.warnings?.length) {
        feedback.warning(res.warnings[0], {
          logMessage: formatActionWarning('导入教师', res.warnings.join('；')),
        })
      }
      if (res?.teachers?.length) {
        teachers.value = res.teachers
        feedback.success(`导入成功，共 ${res.teachers.length} 人`, {
          logMessage: formatActionSuccess('导入教师', `${res.teachers.length} 人`),
        })
      } else {
        feedback.error('导入教师失败：未返回教师数据')
      }
    } catch (e) {
      feedback.error(formatActionError('导入教师', e))
    }
  }

  const handlePresetDialog = () => {
    presetVisible.value = true
  }

  const handleClearTeachers = async () => {
    try {
      await feedback.confirmWarning({
        message: '确定要清除已导入的教师数据吗？这将同时清空当前监考安排与预设状态。',
        title: '清除教师数据',
        confirmButtonText: '清除',
        cancelButtonText: '取消',
      })
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
      logWarning(formatActionWarning('清除教师数据', `后端状态同步失败：${e instanceof Error ? e.message : String(e)}`))
    }
    teachers.value = []
    schedule.value = []
    hasPreset.value = false
    resetScheduleState()
    logSuccess(formatActionSuccess('清除教师数据'))
  }

  const handleClearPreset = async () => {
    try {
      await feedback.confirmWarning({
        message: '确定要清除已导入的预设监考安排吗？这将清空当前监考安排。',
        title: '清除预设监考',
        confirmButtonText: '清除',
        cancelButtonText: '取消',
      })
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
      logWarning(formatActionWarning('清除预设监考', `后端状态同步失败：${e instanceof Error ? e.message : String(e)}`))
    }
    hasPreset.value = false
    resetScheduleState()
    logSuccess(formatActionSuccess('清除预设监考安排'))
  }

  const handleClearSchedule = async () => {
    try {
      await feedback.confirmWarning({
        message: '确定要清除当前监考编排结果吗？（不会清除教师与科目信息）',
        title: '清除当前编排',
        confirmButtonText: '清除',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }
    resetScheduleState()
    logSuccess(formatActionSuccess('清除当前监考编排'))
  }

  const handleResetPage = async () => {
    try {
      await feedback.confirmWarning({
        message: '确定要初始化当前页面吗？这将清除所有数据与设置（教师、科目、编排、预设、日志、参数等）。',
        title: '初始化页面',
        confirmButtonText: '初始化',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }

    try {
      await pythonBackend.request('proctoring.clearState')
    } catch (e) {
      logWarning(formatActionWarning('初始化页面', `后端状态同步失败：${e instanceof Error ? e.message : String(e)}`))
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
    config.roomRepeatPreference = ''
    config.avoidConsecutiveSessions = false

    sidebarCollapsed.value = false
    advancedSettingsVisible.value = false
    activeTab.value = 'overview'

    schedulingProgress.value = 0
    schedulingStatus.value = ''
    schedulingStepText.value = ''
    isScheduling.value = false

    applyPageReset('proctoring')
    feedback.success('页面已初始化', {
      logMessage: formatActionSuccess('初始化页面'),
    })
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

    try {
      const res = await pythonBackend.request<any>('proctoring.import_preset', {
        path,
        teachers: teachers.value,
        subjects: subjects.value,
        config: { ...config }
      })

      if (res?.error) {
        await feedback.alertError('导入预设安排失败', res.error, {
          logMessage: formatActionError('导入预设安排', res.error),
        })
        return
      }
      if (res?.schedule) {
        schedule.value = res.schedule
        if (res.teachers) teachers.value = res.teachers
        if (res.detectedMode) config.mode = String(res.detectedMode)
        if (res.detectedRoomCount) config.roomCount = res.detectedRoomCount
        hasPreset.value = true
        logSuccess(formatActionSuccess('导入预设安排'))
        presetVisible.value = false
      }
    } catch (e) {
      feedback.error(formatActionError('导入预设安排', e))
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
        logSuccess(formatActionSuccess('导入监考安排'))
      }
    } catch (e) {
      feedback.error(formatActionError('导入监考安排', e))
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
