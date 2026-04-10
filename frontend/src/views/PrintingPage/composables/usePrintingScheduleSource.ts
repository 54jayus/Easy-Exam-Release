import { pythonBackend } from '@/lib/pythonBackend'
import { createUiFeedback, formatActionError, formatActionSuccess, formatActionWarning } from '@/lib/uiFeedback'
import type { Ref } from 'vue'

type UsePrintingScheduleSourceOptions = {
  activeTab: Ref<string>
  loadingSchedule: Ref<boolean>
  scheduleArrangementMode: Ref<string>
  previewData: Ref<any[]>
  previewTotal: Ref<number>
  syncSubjectRowsForCurrentSource: () => Promise<void>
}

export function usePrintingScheduleSource({
  activeTab,
  loadingSchedule,
  scheduleArrangementMode,
  previewData,
  previewTotal,
  syncSubjectRowsForCurrentSource
}: UsePrintingScheduleSourceOptions) {
  const feedback = createUiFeedback()

  const applyScheduleModeFromRoomsState = async () => {
    const roomsState = await pythonBackend.request<any>('rooms.getState', {})
    if (roomsState && roomsState.config) {
      const mode = roomsState.config.mode || ''
      scheduleArrangementMode.value = mode === 'gaokao' ? 'gaokao_mode' : ''
    }
  }

  const clearSchedulePreview = () => {
    previewData.value = []
    previewTotal.value = 0
  }

  const loadSchedulePreview = async () => {
    const response = await pythonBackend.request<any>('printing.loadFromSchedule', { type: activeTab.value })
    if (response.data) {
      previewData.value = response.data
      previewTotal.value = response.total
      return response
    }

    clearSchedulePreview()
    return response
  }

  const refreshSchedulePreviewSilently = async () => {
    await applyScheduleModeFromRoomsState()
    await syncSubjectRowsForCurrentSource()
    await loadSchedulePreview()
  }

  const handleLoadFromSchedule = async ({ silent = false }: { silent?: boolean } = {}) => {
    loadingSchedule.value = true

    if (silent) {
      try {
        await refreshSchedulePreviewSilently()
      } catch {
        clearSchedulePreview()
      } finally {
        loadingSchedule.value = false
      }
      return
    }

    try {
      await applyScheduleModeFromRoomsState()
      await syncSubjectRowsForCurrentSource()

      const response = await loadSchedulePreview()
      if (response?.data) {
        feedback.success(formatActionSuccess('加载考场编排数据', `${response.total} 条`))
      } else if (response?.error) {
        const message = String(response.error || '')
        if (message.includes('\u6682\u65e0\u8003\u573a\u7f16\u6392\u6570\u636e')) {
          feedback.warning(formatActionWarning('加载考场编排数据', message))
        } else {
          feedback.error(formatActionError('加载考场编排数据', message))
        }
      }
    } catch (error) {
      clearSchedulePreview()
      feedback.error(formatActionError('加载考场编排数据', error))
    } finally {
      loadingSchedule.value = false
    }
  }

  return {
    refreshSchedulePreviewSilently,
    handleLoadFromSchedule
  }
}
