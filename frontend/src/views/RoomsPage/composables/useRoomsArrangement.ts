import { ElMessage } from 'element-plus'
import { pythonBackend } from '@/lib/pythonBackend'
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
  const handleArrange = async () => {
    if (!deps.studentPath.value) {
      ElMessage.warning('请先导入考生名册')
      return
    }

    deps.logInfo('开始考场编排')
    try {
      const res = await pythonBackend.request<any>('rooms.arrange', {
        studentPath: deps.studentPath.value,
        settings: deps.roomSettings.value,
        config: deps.config
      })

      if (res?.error) {
        ElMessage.error(res.error)
        deps.logError(`编排失败：${res.error}`)
      } else if (res?.results) {
        deps.results.value = res.results
        ElMessage.success('编排完成')
        deps.logSuccess(`编排完成：共 ${res.results.length} 人`)
        deps.activeTab.value = 'results'
      }
    } catch (e) {
      ElMessage.error('编排失败: ' + e)
      deps.logError(`编排异常：${e instanceof Error ? e.message : String(e)}`)
    }
  }

  return {
    handleArrange
  }
}
