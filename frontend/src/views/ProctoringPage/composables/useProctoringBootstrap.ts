import type { Ref } from 'vue'
import { formatActionError } from '@/lib/uiFeedback'
import { pythonBackend } from '@/lib/pythonBackend'

type Subject = {
  id: string
  name: string
  examDate?: string
  time: string
  durationMinutes: number
  roomCount: number
  remark?: string
}
type ProctoringConfig = {
  roomCount: number
  mode: string
  balanceMode: string
  genderMix: boolean
  internalMix: boolean
  roomRepeatPreference?: string
  avoidConsecutiveSessions?: boolean
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
        config.balanceMode = config.balanceMode || 'duration'
        const normalizedRoomRepeatPreference = String(config.roomRepeatPreference || '').trim().toLowerCase()
        if (['high', 'same', 'prefer_same', 'fixed'].includes(normalizedRoomRepeatPreference)) {
          config.roomRepeatPreference = 'fixed'
        } else if (['low', 'different', 'prefer_different'].includes(normalizedRoomRepeatPreference)) {
          config.roomRepeatPreference = 'different'
        } else {
          config.roomRepeatPreference = ''
        }
        config.avoidConsecutiveSessions = Boolean(config.avoidConsecutiveSessions)

        if (res.schedule && Array.isArray(res.schedule)) {
          hasPreset.value = res.schedule.some((subj: any) =>
            subj.rooms?.some((room: any) =>
              room.teachers?.some((t: any) => t?.isLocked || t?.isExempt)
            )
          )
        }
      }
    } catch (e) {
      logError(formatActionError('读取监考编排状态', e))
    }
  }

  const initializePage = async () => {
    try {
      const res = await pythonBackend.request<any>('subjects.list')
      if (res && res.subjects) {
        subjects.value = res.subjects.map((s: any) => ({
          id: s.id,
          name: s.name,
          examDate: s.exam_date || '',
          time: s.exam_time || s.time || '',
          durationMinutes: Number(s.duration_minutes ?? s.durationMinutes ?? s.duration ?? 0) || 0,
          roomCount: Number(s.room_count ?? s.roomCount ?? 0) || 0,
          remark: s.remark || '',
        }))
        if (subjects.value.length > 0) selectedSubjectId.value = subjects.value[0].id
      }

      await loadState()
    } catch (e) {
      logError(formatActionError('初始化页面', e))
    }
  }

  return {
    loadState,
    initializePage,
  }
}
