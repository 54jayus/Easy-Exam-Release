import { pythonBackend } from '@/lib/pythonBackend'
import {
  createUiFeedback,
  formatActionError,
  formatActionStart,
  formatActionSuccess,
  formatActionWarning,
} from '@/lib/uiFeedback'
import type { Ref } from 'vue'
import type { RoomsConfig } from './useRoomsState'

export function useRoomsArrangement(deps: {
  studentPath: Ref<string>
  roomSettings: Ref<any[]>
  config: RoomsConfig
  students: Ref<any[]>
  results: Ref<any[]>
  activeTab: Ref<string>
  logInfo: (msg: string) => void
  logSuccess: (msg: string) => void
  logError: (msg: string) => void
}) {
  const feedback = createUiFeedback({
    logInfo: deps.logInfo,
    logSuccess: deps.logSuccess,
    logError: deps.logError,
  })

  const handleArrange = async () => {
    if (!deps.studentPath.value) {
      feedback.warning('请先导入考生名册', {
        logMessage: formatActionWarning('考场编排', '请先导入考生名册'),
      })
      return
    }

    deps.logInfo(formatActionStart('考场编排'))
    try {
      const res = await pythonBackend.request<any>('rooms.arrange', {
        studentPath: deps.studentPath.value,
        settings: deps.roomSettings.value,
        config: deps.config
      })

      if (res?.error) {
        feedback.error(res.error, {
          logMessage: formatActionError('考场编排', res.error),
        })
      } else if (res?.results) {
        deps.results.value = res.results
        feedback.success('编排完成', {
          logMessage: formatActionSuccess('完成考场编排', `共 ${res.results.length} 人`),
        })
        deps.activeTab.value = 'results'
      }
    } catch (e) {
      feedback.error(formatActionError('考场编排', e))
    }
  }

  return {
    handleArrange
  }
}
