import type { Ref } from 'vue'
import {
  createUiFeedback,
  formatActionError,
  formatActionStart,
  formatActionSuccess,
} from '@/lib/uiFeedback'
import { pythonBackend } from '@/lib/pythonBackend'

type ProctoringConfig = {
  roomCount: number
  mode: string
  balanceMode: string
  genderMix: boolean
  internalMix: boolean
  roomRepeatPreference?: string
  avoidConsecutiveSessions?: boolean
  consecutiveGapMinutes?: number
  cpSatNoImprovementSeconds?: number
  cpSatProgressIntervalSeconds?: number
}

type UiLogFn = (msg: string) => void

const POLL_INTERVAL_MS = 3000
const DEFAULT_NO_IMPROVEMENT_SECONDS = 3
const DEFAULT_PROGRESS_INTERVAL_SECONDS = 3

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const countMissingAssignments = (scheduleData: any[] | undefined | null) => {
  let missing = 0
  for (const subject of scheduleData || []) {
    for (const room of subject?.rooms || []) {
      for (const teacher of room?.teachers || []) {
        if (!teacher) missing += 1
      }
    }
  }
  return missing
}

const humanizeStageName = (stageName: string) => {
  switch (stageName) {
    case 'minimize_max_overall_duration':
    case 'maximize_min_overall_duration':
    case 'minimize_overall_duration_deviation':
      return '正在平衡老师监考时长'
    case 'minimize_count_range':
    case 'minimize_max_count':
    case 'minimize_count_deviation':
      return '正在平衡老师监考场次'
    case 'minimize_distinct_rooms':
    case 'maximize_distinct_rooms':
      return '正在调整老师的考场安排'
    case 'minimize_consecutive_sessions':
      return '正在尽量减少连续监考'
    default:
      return '正在整理监考编排数据'
  }
}

const humanizeBackendMessage = (rawMessage: any, actionName: string) => {
  const message = String(rawMessage || '').trim()
  if (!message) return `${actionName}失败，请稍后重试。`
  if (/[\u4e00-\u9fff]/.test(message)) return message

  if (message.includes('No feasible schedule satisfies the current constraints')) {
    return '未找到满足当前条件的监考安排，请检查老师人数、禁监考科目、最大监考场次和预设条件。'
  }
  if (message.includes('The CP-SAT solver did not find a feasible solution')) {
    return '未找到可用的监考安排，请检查当前条件是否过于严格。'
  }
  if (message.includes('The CP-SAT model is invalid')) {
    return '当前监考编排设置无效，请检查参数后重试。'
  }
  if (message.includes('Locked assignment is incompatible with the active constraints')) {
    return '导入或锁定的监考安排与当前条件冲突，请检查锁定位置、预设考场和搭配条件。'
  }
  if (message.includes('No eligible teacher is available for subject')) {
    return '部分考场暂时找不到符合条件的监考老师，请检查老师数量、禁监考科目和最大监考场次。'
  }
  if (message.includes('Job not found')) {
    return '当前编排任务不存在，请重新开始。'
  }
  return message
}

export function useProctoringScheduling(options: {
  config: ProctoringConfig
  teachers: Ref<any[]>
  subjects: Ref<any[]>
  schedule: Ref<any[]>
  hasPreset: Ref<boolean>
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
  const feedback = createUiFeedback({ logInfo, logSuccess, logWarning, logError })

  const setOptimizationDetail = (optimization: any, details: any) => {
    optDetail.value = {
      swaps: Array.isArray(details?.swaps) ? details.swaps : [],
      presetDetails: Array.isArray(details?.presetDetails) ? details.presetDetails : [],
      stages: Array.isArray(details?.stages) ? details.stages : [],
      progressSamples: Array.isArray(details?.progressSamples) ? details.progressSamples : [],
      before: optimization?.before,
      after: optimization?.after,
      earlyStopReason: optimization?.earlyStopReason,
    }
  }

  const shouldShowOptimizationDetails = () => {
    const isDev = localStorage.getItem('developer_mode') === 'true'
    const showDetails = localStorage.getItem('show_optimization_details') === 'true'
    return isDev && showDetails
  }

  const buildSolverConfig = () => ({
    ...config,
    roomRepeatPreference: config.roomRepeatPreference ?? '',
    avoidConsecutiveSessions: Boolean(config.avoidConsecutiveSessions),
    consecutiveGapMinutes: config.avoidConsecutiveSessions
      ? Number(config.consecutiveGapMinutes ?? 0)
      : 0,
    cpSatNoImprovementSeconds: config.cpSatNoImprovementSeconds ?? DEFAULT_NO_IMPROVEMENT_SECONDS,
    cpSatProgressIntervalSeconds: config.cpSatProgressIntervalSeconds ?? DEFAULT_PROGRESS_INTERVAL_SECONDS,
  })

  const buildProgressText = (job: any, actionName: string) => {
    const progress = job?.progress || {}
    const stageText = humanizeStageName(String(progress?.currentStageName || ''))
    const previewStageIndex = Number(progress?.previewStageIndex ?? 0)

    if (job?.status === 'queued') return `${actionName}：正在排队，准备开始`
    if (job?.status === 'completed') return `${actionName}：已完成`
    if (job?.status === 'failed') return `${actionName}：未完成`
    if (job?.status === 'running' && progress?.previewResult?.schedule) {
      const previewLabel = previewStageIndex > 0
        ? `已显示第 ${previewStageIndex} 阶段结果`
        : '已显示阶段结果'
      return `${actionName}：${previewLabel}，${stageText}`
    }

    return `${actionName}：${stageText}`
  }

  const buildProgressLogKey = (job: any) => {
    const progress = job?.progress || {}
    return [
      job?.status || '',
      humanizeStageName(String(progress?.currentStageName || '')),
    ].join('|')
  }

  const applyCompletedResult = (res: any, actionName: string) => {
    if (!res?.schedule) throw new Error('后端未返回监考编排结果')

    schedule.value = res.schedule
    teachers.value = res.teachers
    setOptimizationDetail(res.optimization, res.optimizationDetails)
    schedulingProgress.value = 100

    const missingCount = countMissingAssignments(res.schedule)
    if (missingCount > 0) {
      schedulingStatus.value = 'warning'
      schedulingStepText.value = `${actionName}已结束，仍有 ${missingCount} 个监考空缺`
      logWarning(`${actionName}提示：仍有 ${missingCount} 个监考空缺`)
      return
    }

    schedulingStatus.value = 'success'
    schedulingStepText.value = `${actionName}已完成`
    logSuccess(formatActionSuccess(actionName))
  }

  const applyPreviewResult = (res: any) => {
    if (!res?.schedule) return
    schedule.value = res.schedule
    teachers.value = res.teachers
  }

  const runSolverJob = async (args: {
    operation: 'generate' | 'continue'
    actionName: string
    payload: Record<string, any>
    completionToast: string
  }) => {
    const { operation, actionName, payload, completionToast } = args
    const started = await pythonBackend.request<any>('proctoring.startSolverJob', {
      operation,
      ...payload,
      config: buildSolverConfig(),
    })
    if (started?.error) throw new Error(humanizeBackendMessage(started.error, actionName))

    const jobId = String(started?.jobId || '')
    if (!jobId) throw new Error('后端未返回任务编号')

    let lastLogKey = ''
    let lastPreviewStageIndex = 0
    schedulingProgress.value = 1
    schedulingStatus.value = ''
    schedulingStepText.value = `${actionName}：正在准备`

    while (true) {
      const job = await pythonBackend.request<any>('proctoring.getJobStatus', { jobId }, 15_000)
      if (job?.status === 'missing') {
        throw new Error(humanizeBackendMessage(job?.error || 'Job not found', actionName))
      }

      schedulingProgress.value = Number(job?.progressPercent ?? schedulingProgress.value ?? 0)
      schedulingStepText.value = buildProgressText(job, actionName)

      const progressLogKey = buildProgressLogKey(job)
      if (progressLogKey !== lastLogKey && job?.status === 'running') {
        lastLogKey = progressLogKey
        logInfo(schedulingStepText.value)
      }

      const previewStageIndex = Number(job?.progress?.previewStageIndex ?? 0)
      if (
        job?.status === 'running'
        && previewStageIndex > lastPreviewStageIndex
        && job?.progress?.previewResult?.schedule
      ) {
        lastPreviewStageIndex = previewStageIndex
        applyPreviewResult(job.progress.previewResult)
        logInfo(`已显示第 ${previewStageIndex} 阶段结果，系统仍在继续优化`)
      }

      if (job?.status === 'completed') {
        applyCompletedResult(job.result, actionName)
        await sleep(500)
        isScheduling.value = false
        if (optDetail.value && shouldShowOptimizationDetails()) {
          optDetailVisible.value = true
        } else {
          feedback.success(completionToast, { log: false })
        }
        return
      }

      if (job?.status === 'failed') {
        const message = humanizeBackendMessage(
          job?.error || job?.message || `${actionName}失败`,
          actionName,
        )
        throw new Error(message)
      }

      if (job?.status !== 'queued' && job?.status !== 'running') {
        throw new Error(
          humanizeBackendMessage(
            job?.message || `${actionName}状态异常：${String(job?.status)}`,
            actionName,
          ),
        )
      }

      await sleep(POLL_INTERVAL_MS)
    }
  }

  const handleSmartSchedule = async () => {
    isScheduling.value = true
    schedulingProgress.value = 0
    schedulingStatus.value = ''
    schedulingStepText.value = '正在准备...'

    const actionName = hasPreset.value ? '补全编排' : '智能编排'
    logInfo(formatActionStart(actionName))

    try {
      await runSolverJob({
        operation: hasPreset.value ? 'continue' : 'generate',
        actionName,
        payload: {
          teachers: teachers.value,
          subjects: subjects.value,
          schedule: hasPreset.value ? schedule.value : undefined,
        },
        completionToast: '编排完成',
      })
    } catch (e: any) {
      const msg = e?.message || String(e)
      logError(formatActionError(actionName, msg))
      schedulingStatus.value = 'exception'
      schedulingStepText.value = '监考编排未完成'
      feedback.error(formatActionError(actionName, msg), { log: false })
      await sleep(1500)
      isScheduling.value = false
    }
  }

  return {
    handleSmartSchedule,
  }
}
