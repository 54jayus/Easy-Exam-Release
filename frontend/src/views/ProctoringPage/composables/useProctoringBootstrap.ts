import type { Ref } from 'vue'
import { pythonBackend } from '@/lib/pythonBackend'

type Subject = { id: string; name: string; time: string; durationMinutes: number }
type ProctoringConfig = {
  roomCount: number
  mode: string
  balanceMode: string
  genderMix: boolean
  internalMix: boolean
}

export function useProctoringBootstrap(options: {
  config: ProctoringConfig
  subjects: Ref<Subject[]>
  teachers: Ref<any[]>
  schedule: Ref<any[]>
  selectedSubjectId: Ref<string>
  hasPreset: Ref<boolean>
  logError: (msg: string) => void
}) {
  const {
    config,
    subjects,
    teachers,
    schedule,
    selectedSubjectId,
    hasPreset,
    logError,
  } = options

  const loadState = async () => {
    try {
      const res = await pythonBackend.request<any>('proctoring.getState')
      if (res) {
        if (res.teachers) teachers.value = res.teachers
        if (res.schedule) schedule.value = res.schedule
        if (res.config) {
          Object.assign(config, res.config)
        }

        if (res.schedule && Array.isArray(res.schedule)) {
          hasPreset.value = res.schedule.some((subj: any) =>
            subj.rooms?.some((room: any) =>
              room.teachers?.some((t: any) => t?.isLocked)
            )
          )
        }
      }
    } catch (e) {
      logError('读取监考编排状态失败：' + (e instanceof Error ? e.message : String(e)))
    }
  }

  const initializePage = async () => {
    try {
      const res = await pythonBackend.request<any>('subjects.list')
      if (res && res.subjects) {
        subjects.value = res.subjects.map((s: any) => ({
          id: s.id,
          name: s.name,
          time: s.exam_time || s.time || '',
          durationMinutes: Number(s.duration_minutes ?? s.durationMinutes ?? s.duration ?? 0) || 0
        }))
        if (subjects.value.length > 0) selectedSubjectId.value = subjects.value[0].id
      }

      await loadState()
    } catch (e) {
      logError('初始化失败：' + (e instanceof Error ? e.message : String(e)))
    }
  }

  return {
    loadState,
    initializePage,
  }
}
