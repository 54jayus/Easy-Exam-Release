import { open, saveAndRun } from '@/lib/dialog'
import {
  createUiFeedback,
  formatActionError,
  formatActionSuccess,
} from '@/lib/uiFeedback'
import { pythonBackend } from '@/lib/pythonBackend'
import { ref } from 'vue'
import type { Ref } from 'vue'
import type { RoomsConfig } from './useRoomsState'

export function useRoomsIO(deps: {
  roomSettings: Ref<any[]>
  students: Ref<any[]>
  results: Ref<any[]>
  studentPath: Ref<string>
  cachedResultsPath: Ref<string>
  config: RoomsConfig
  activeTab: Ref<string>
  logInfo: (msg: string) => void
  logSuccess: (msg: string) => void
  logError: (msg: string) => void
  logFromText: (msg: string) => void
}) {
  const feedback = createUiFeedback({
    logInfo: deps.logInfo,
    logSuccess: deps.logSuccess,
    logError: deps.logError,
  })

  // Loading state for export
  const isExporting = ref(false)
  // Template Generation
  const handleGenerateTemplate = async (type: string) => {
    await saveAndRun({
      dialog: {
        filters: [{ name: 'Excel', extensions: ['xlsx'] }],
        defaultPath: type === 'settings' ? '考场设置模板.xlsx' : '考生名册模板.xlsx'
      },
      run: async (path) => {
        return await pythonBackend.request<any>('rooms.generateTemplate', { type, path })
      },
      successText: '模板生成成功',
      errorText: '生成模板失败',
      onLog: deps.logFromText
    })
  }

  // Import Settings
  const handleImportSettings = async () => {
    const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx', 'xls'] }] })
    if (path) {
      const res = await pythonBackend.request<any>('rooms.importSettings', { path })
      if (res?.error) {
        feedback.error(res.error, {
          logMessage: formatActionError('导入考场设置', res.error),
        })
      } else if (res?.settings) {
        deps.roomSettings.value = res.settings
        deps.config.totalRooms = res.settings.length

        // 检测考场人数是否一致
        if (res.settings.length > 0) {
          const capacities = res.settings
            .map((r: any) => r.capacity)
            .filter((c: any) => typeof c === 'number' && c > 0)

          if (capacities.length > 0) {
            const min = Math.min(...capacities)
            const max = Math.max(...capacities)

            // 只有当所有考场人数一致时，才更新 seatsPerRoom
            if (min === max) {
              deps.config.seatsPerRoom = min
            }
            // 如果不一致，保持原有值不变，由 seatsPerRoomInfo 计算属性处理显示
          }
        }

        feedback.success(`成功导入 ${res.settings.length} 个考场设置`, {
          logMessage: formatActionSuccess('导入考场设置', `${res.settings.length} 个考场`),
        })
        deps.activeTab.value = 'settings'
      }
    }
  }

  // Import Students
  const handleImportStudents = async () => {
    const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx', 'xls'] }] })
    if (path) {
      deps.studentPath.value = path as string // Save path
      const res = await pythonBackend.request<any>('rooms.importStudents', { path })
      if (res?.error) {
        feedback.error(res.error, {
          logMessage: formatActionError('导入考生名册', res.error),
        })
      } else if (res?.students) {
        deps.students.value = res.students
        feedback.success(`成功导入 ${res.total} 名考生`, {
          logMessage: formatActionSuccess('导入考生名册', `${res.total} 人`),
        })
        deps.activeTab.value = 'students'
      }
    }
  }

  // Import Results
  const handleImportResults = async () => {
    const path = await open({ filters: [{ name: 'Excel', extensions: ['xlsx', 'xls'] }] })
    if (path) {
      const res = await pythonBackend.request<any>('rooms.importResults', { path })
      if (res?.error) {
        feedback.error(res.error, {
          logMessage: formatActionError('导入编排结果', res.error),
        })
      } else if (res?.results) {
        deps.results.value = res.results
        deps.cachedResultsPath.value = String(path)
        feedback.success('导入成功', {
          logMessage: formatActionSuccess('导入编排结果', `共 ${res.results.length} 人`),
        })
        deps.activeTab.value = 'results'
      }
    }
  }

  // Export Results
  const handleExport = async () => {
    await saveAndRun({
      dialog: {
        filters: [{ name: 'Excel', extensions: ['xlsx'] }],
        defaultPath: '考场编排结果.xlsx'
      },
      run: async (path) => {
        isExporting.value = true
        try {
          return await pythonBackend.request<any>('rooms.export', { path })
        } finally {
          isExporting.value = false
        }
      },
      successText: '导出成功',
      errorText: '导出失败',
      onLog: deps.logFromText
    })
  }

  return {
    handleGenerateTemplate,
    handleImportSettings,
    handleImportStudents,
    handleImportResults,
    handleExport,
    isExporting
  }
}
