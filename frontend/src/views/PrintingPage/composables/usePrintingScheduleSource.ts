import { ElMessage } from 'element-plus'
import { pythonBackend } from '@/lib/pythonBackend'
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
        ElMessage.success(`\u6210\u529f\u52a0\u8f7d ${response.total} \u6761\u8003\u573a\u7f16\u6392\u6570\u636e`)
      } else if (response?.error) {
        const message = String(response.error || '')
        if (message.includes('\u6682\u65e0\u8003\u573a\u7f16\u6392\u6570\u636e')) {
          ElMessage.warning(message)
        } else {
          ElMessage.error(message)
        }
      }
    } catch (error) {
      clearSchedulePreview()
      ElMessage.error(`\u52a0\u8f7d\u8003\u573a\u6570\u636e\u5931\u8d25: ${error}`)
    } finally {
      loadingSchedule.value = false
    }
  }

  return {
    refreshSchedulePreviewSilently,
    handleLoadFromSchedule
  }
}
