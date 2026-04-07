import type { Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { pythonBackend } from '@/lib/pythonBackend'

type ProctoringConfig = {
  roomCount: number
  mode: string
  balanceMode: string
  genderMix: boolean
  internalMix: boolean
}

type UiLogFn = (msg: string) => void

export function useProctoringScheduling(options: {
  config: ProctoringConfig
  teachers: Ref<any[]>
  subjects: Ref<any[]>
  schedule: Ref<any[]>
  hasPreset: Ref<boolean>
  showLogs: Ref<boolean>
  optDetailVisible: Ref<boolean>
  optDetail: Ref<any>
  schedulingProgress: Ref<number>
  schedulingStatus: Ref<string>
  schedulingStepText: Ref<string>
  isScheduling: Ref<boolean>
  logInfo: UiLogFn
  logSuccess: UiLogFn
  logWarning: UiLogFn
  logError: UiLogFn
}) {
  const {
    config,
    teachers,
    subjects,
    schedule,
    hasPreset,
    showLogs,
    optDetailVisible,
    optDetail,
    schedulingProgress,
    schedulingStatus,
    schedulingStepText,
    isScheduling,
    logInfo,
    logSuccess,
    logWarning,
    logError,
  } = options

  const setOptimizationDetail = (optimization: any, details: any) => {
    optDetail.value = {
      swaps: Array.isArray(details?.swaps) ? details.swaps : [],
      presetDetails: Array.isArray(details?.presetDetails) ? details.presetDetails : [],
      before: optimization?.before,
      after: optimization?.after,
      earlyStopReason: optimization?.earlyStopReason
    }
  }

  const shouldShowOptimizationDetails = () => {
    const isDev = localStorage.getItem('developer_mode') === 'true'
    const showDetails = localStorage.getItem('show_optimization_details') === 'true'
    return isDev && showDetails
  }

  const handleSmartSchedule = async () => {
    isScheduling.value = true
    schedulingProgress.value = 0
    schedulingStatus.value = ''
    schedulingStepText.value = '准备开始...'

    try {
      const method = hasPreset.value ? 'proctoring.continue' : 'proctoring.generateSchedule'
      const actionName = hasPreset.value ? '补全安排' : '智能编排'

      schedulingStepText.value = `正在进行${actionName}...`
      schedulingProgress.value = 10
      logInfo(`开始${actionName}`)

      await new Promise((r) => setTimeout(r, 500))

      const res = await pythonBackend.request<any>(method, {
        teachers: teachers.value,
        subjects: subjects.value,
        schedule: hasPreset.value ? schedule.value : undefined,
        config
      })

      if (!res.schedule) throw new Error('未返回排班结果')

      schedule.value = res.schedule
      teachers.value = res.teachers
      schedulingProgress.value = 60
      logSuccess(`${actionName}完成`)

      schedulingStepText.value = '正在进行优化...'
      logInfo('开始深度优化')

      const optStart = Date.now()
      const optPhaseMin = 60
      const optPhaseMax = 96
      const optExpectedMs = 60_000
      const progressTimer = setInterval(() => {
        const elapsed = Date.now() - optStart
        const ratio = Math.min(1, elapsed / optExpectedMs)
        const eased = 0.15 + 0.85 * ratio
        const target = Math.floor(optPhaseMin + (optPhaseMax - optPhaseMin) * eased)
        if (schedulingProgress.value < target && schedulingProgress.value < optPhaseMax) {
          schedulingProgress.value += 1
        }
      }, 600)

      const optRes = await pythonBackend.request<any>('proctoring.optimize', {
        teachers: teachers.value,
        subjects: subjects.value,
        schedule: schedule.value,
        config
      }, 180_000)

      clearInterval(progressTimer)

      if (optRes?.error) {
        logWarning(`二次均衡优化失败：${optRes.error}`)
        ElMessage.warning('基础编排完成，但深度优化失败')
      } else if (optRes.schedule) {
        schedule.value = optRes.schedule
        teachers.value = optRes.teachers
        setOptimizationDetail(optRes.optimization, optRes.optimizationDetails)
        logSuccess('二次均衡优化完成')
      }

      schedulingProgress.value = 100
      schedulingStatus.value = 'success'
      schedulingStepText.value = '全部完成！'

      await new Promise((r) => setTimeout(r, 800))
      isScheduling.value = false

      if (optDetail.value && shouldShowOptimizationDetails()) optDetailVisible.value = true
      else ElMessage.success('编排完成')
    } catch (e: any) {
      const msg = e?.message || String(e)
      logError(`编排失败：${msg}`)
      schedulingStatus.value = 'exception'
      schedulingStepText.value = '发生错误'
      ElMessage.error(`编排失败: ${msg}`)
      await new Promise((r) => setTimeout(r, 2000))
      isScheduling.value = false
    }
  }

  const handleOptimize = async () => {
    logInfo('开始优化')
    try {
      const res = await pythonBackend.request<any>('proctoring.optimize', {
        teachers: teachers.value,
        subjects: subjects.value,
        schedule: schedule.value,
        config
      }, 180_000)
      if (res?.error) {
        logError(`二次均衡优化失败：${res.error}`)
        if (res.trace) logInfo(String(res.trace))
        showLogs.value = true
        await ElMessageBox.alert(res.error, '二次均衡优化失败', { type: 'error' })
        return
      }
      if (res.schedule) {
        schedule.value = res.schedule
        teachers.value = res.teachers
        const info = res.optimization
        if (info) {
          const parts = []
          if (typeof info.swapCount === 'number') parts.push(`交换 ${info.swapCount} 次`)
          if (typeof info.presetMoves === 'number' && info.presetMoves > 0) parts.push(`预设修复 ${info.presetMoves} 次`)
          if (info.earlyStopReason) parts.push(`提前结束：${info.earlyStopReason}`)
          logSuccess(`二次均衡优化完成${parts.length ? `（${parts.join('；')}）` : ''}`)
        } else {
          logSuccess('二次均衡优化完成')
        }

        setOptimizationDetail(info, res.optimizationDetails)

        if (shouldShowOptimizationDetails()) {
          optDetailVisible.value = true
        }
      }
    } catch (e: any) {
      const msg = e?.message ? String(e.message) : String(e)
      logError(`二次均衡优化异常：${msg}`)
      showLogs.value = true
      ElMessage.error('优化失败')
    }
  }

  return {
    handleSmartSchedule,
    handleOptimize,
  }
}
