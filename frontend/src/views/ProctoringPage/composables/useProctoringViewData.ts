import { computed, type Ref } from 'vue'

type ProctoringConfig = {
  roomCount: number
  mode: string
  balanceMode: string
  genderMix: boolean
  internalMix: boolean
  roomRepeatPreference?: string
  avoidConsecutiveSessions?: boolean
}

type Subject = {
  id: string
  name: string
  examDate?: string
  time: string
  durationMinutes: number
  roomCount: number
  remark?: string
}

type TeacherViewGenderFilter = 'all' | 'M' | 'F' | 'unknown'
type TeacherViewSourceFilter = 'all' | 'internal' | 'external' | 'unknown'
type TeacherViewPresetFilter = 'all' | 'preset' | 'none'

export type TeacherViewRow = {
  name: string
  gender: string
  genderLabel: string
  isInternal: boolean | null | undefined
  sourceLabel: string
  maxSessions: number
  unavailableSubjects: Array<string | number>
  unavailableSubjectsLabel: string
  previousSupervisionDuration: number
  presetRoom: number | null
  sessions: number
  supervisionDuration: number
  totalDuration: number
}

const normalizeCount = (value: unknown) => {
  const numeric = Number(value ?? 0)
  return Number.isFinite(numeric) ? numeric : 0
}

const normalizeGenderLabel = (gender: string) => {
  if (gender === 'M') return '男'
  if (gender === 'F') return '女'
  return '未填写'
}

const normalizeSourceLabel = (isInternal: boolean | null | undefined) => {
  if (isInternal === true) return '本校'
  if (isInternal === false) return '外校'
  return '未填写'
}

export function useProctoringViewData(options: {
  config: ProctoringConfig
  subjects: Ref<Subject[]>
  teachers: Ref<any[]>
  schedule: Ref<any[]>
  selectedSubjectId: Ref<string>
  teacherViewKeyword: Ref<string>
  teacherViewGenderFilter: Ref<TeacherViewGenderFilter>
  teacherViewSourceFilter: Ref<TeacherViewSourceFilter>
  teacherViewPresetFilter: Ref<TeacherViewPresetFilter>
}) {
  const {
    config,
    subjects,
    teachers,
    schedule,
    selectedSubjectId,
    teacherViewKeyword,
    teacherViewGenderFilter,
    teacherViewSourceFilter,
    teacherViewPresetFilter,
  } = options

  const subjectCount = computed(() => subjects.value.length)
  const hasSchedule = computed(() => schedule.value.length > 0)
  const getExpectedRoomNumbers = (subjectId: string) => {
    const session = schedule.value.find((s: any) => s.subjectId === subjectId)
    const scheduledRooms = Array.isArray(session?.rooms)
      ? session.rooms
          .map((room: any) => Number(room?.roomNum ?? room?.id ?? 0))
          .filter((roomNum: number) => Number.isFinite(roomNum) && roomNum > 0)
      : []
    if (scheduledRooms.length > 0) {
      return Array.from(new Set<number>(scheduledRooms)).sort((left, right) => left - right)
    }

    const subject = subjects.value.find((item) => item.id === subjectId)
    const roomCount = Number(subject?.roomCount ?? 0) > 0
      ? Number(subject?.roomCount ?? 0)
      : Number(config.roomCount ?? 0)
    return Array.from({ length: Math.max(0, roomCount) }, (_, index) => index + 1)
  }
  const maxVisibleRoomCount = computed(() => {
    const counts = subjects.value.map((subject) => getExpectedRoomNumbers(subject.id).length)
    return Math.max(0, ...counts)
  })
  const canSchedule = computed(() => {
    if (teachers.value.length <= 0 || subjectCount.value <= 0) return false
    return subjects.value.every((subject) => getExpectedRoomNumbers(subject.id).length > 0)
  })
  const missingSlots = computed(() => {
    if (!hasSchedule.value) return 0
    const requiredSlots = config.mode === 'double' ? 2 : 1
    let missing = 0
    for (const sub of subjects.value) {
      const session = schedule.value.find((s) => s.subjectId === sub.id)
      for (const roomId of getExpectedRoomNumbers(sub.id)) {
        const room = session?.rooms?.find((r: any) => Number(r.roomNum ?? r.id) === roomId)
        const ts: any[] = room?.teachers || []
        const filled = ts.filter((t) => t && !t.isExempt).length
        const exempt = ts.filter((t) => t?.isExempt).length
        if (filled + exempt < requiredSlots) missing += (requiredSlots - filled - exempt)
      }
    }
    return missing
  })
  const canContinue = computed(() => hasSchedule.value && missingSlots.value > 0)

  const getRoomRecord = (subjectId: string, roomNum: number) => {
    const session = schedule.value.find((s: any) => s.subjectId === subjectId)
    const rooms: any[] = session?.rooms || []
    return rooms.find((r: any) => Number(r.roomNum ?? r.id) === roomNum) || null
  }

  const getTeacherObj = (subjectId: string, roomNum: number, idx: number) => {
    const room = getRoomRecord(subjectId, roomNum)
    const ts: any[] = room?.teachers || []
    if (config.mode === 'double') return ts[idx] || null
    return ts.find((t) => t) || null
  }

  const getTeacherText = (subjectId: string, roomNum: number, idx: number) => {
    const t = getTeacherObj(subjectId, roomNum, idx)
    if (!t) return ''
    if (t.isExempt) return '无需编排'
    if (t.isLocked) return `${t.name}[锁]`
    if (t.presetRoom && Number(t.presetRoom) === roomNum) return `${t.name}[预]`
    return t.name
  }

  const getTeacherTextClass = (subjectId: string, roomNum: number, idx: number) => {
    const t = getTeacherObj(subjectId, roomNum, idx)
    if (!t) return 'text-slate-300'

    if (t.isExempt) return 'text-amber-600 font-semibold'
    if (t.isLocked) return 'text-rose-600 font-semibold'
    if (t.presetRoom && Number(t.presetRoom) === roomNum) return 'text-emerald-600 font-semibold'
    if (t.gender === 'M') return 'text-blue-600'
    if (t.gender === 'F') return 'text-fuchsia-600'
    return 'text-slate-700'
  }

  const getUnavailableNames = (unavailable: any[]) => {
    if (!unavailable || !Array.isArray(unavailable) || unavailable.length === 0) return ''
    return unavailable.map((u) => {
      const text = String(u ?? '').trim()
      const sub = subjects.value.find((s) => s.id === text || s.name === text || String(s.id) === text)
      return sub ? sub.name : text
    }).filter(Boolean).join('、')
  }

  const matrixData = computed(() => {
    if (!schedule.value.length) return []
    const rows = []
    for (let i = 1; i <= maxVisibleRoomCount.value; i += 1) {
      const row: any = { roomId: i }
      subjects.value.forEach((sub) => {
        if (config.mode === 'double') {
          row[`sub_${sub.id}_1`] = ''
          row[`sub_${sub.id}_2`] = ''
        } else {
          row[`sub_${sub.id}`] = ''
        }
      })
      rows.push(row)
    }
    return rows
  })

  const teacherStats = computed(() => {
    return teachers.value.map((t) => {
      const status: Record<string, boolean> = {}
      subjects.value.forEach((sub) => {
        const assigned = schedule.value.some((s) =>
          s.subjectId === sub.id &&
          s.rooms.some((r: any) => r.teachers.some((tr: any) => tr && tr.id === t.id)),
        )
        status[sub.id] = assigned
      })

      return {
        ...t,
        subjectStatus: status,
      }
    })
  })

  const teacherViewRows = computed<TeacherViewRow[]>(() => {
    return teachers.value.map((teacher) => {
      const gender = String(teacher?.gender || '').trim().toUpperCase()
      const unavailableSubjects = Array.isArray(teacher?.unavailableSubjects)
        ? teacher.unavailableSubjects
        : []
      const previousSupervisionDuration = normalizeCount(teacher?.previousSupervisionDuration)
      const supervisionDuration = normalizeCount(teacher?.supervisionDuration)
      const presetRoomValue = Number(teacher?.presetRoom ?? 0)
      const presetRoom = Number.isFinite(presetRoomValue) && presetRoomValue > 0 ? presetRoomValue : null

      return {
        name: String(teacher?.name || ''),
        gender,
        genderLabel: normalizeGenderLabel(gender),
        isInternal: teacher?.isInternal,
        sourceLabel: normalizeSourceLabel(teacher?.isInternal),
        maxSessions: normalizeCount(teacher?.maxSessions),
        unavailableSubjects,
        unavailableSubjectsLabel: getUnavailableNames(unavailableSubjects),
        previousSupervisionDuration,
        presetRoom,
        sessions: normalizeCount(teacher?.sessions),
        supervisionDuration,
        totalDuration: previousSupervisionDuration + supervisionDuration,
      }
    })
  })

  const teacherViewTableData = computed(() => {
    const keyword = teacherViewKeyword.value.trim().toLowerCase()

    return teacherViewRows.value.filter((row) => {
      if (keyword && !row.name.toLowerCase().includes(keyword)) return false

      if (teacherViewGenderFilter.value === 'M' && row.gender !== 'M') return false
      if (teacherViewGenderFilter.value === 'F' && row.gender !== 'F') return false
      if (teacherViewGenderFilter.value === 'unknown' && row.gender) return false

      if (teacherViewSourceFilter.value === 'internal' && row.isInternal !== true) return false
      if (teacherViewSourceFilter.value === 'external' && row.isInternal !== false) return false
      if (teacherViewSourceFilter.value === 'unknown' && row.isInternal !== null && row.isInternal !== undefined) {
        return false
      }

      if (teacherViewPresetFilter.value === 'preset' && !row.presetRoom) return false
      if (teacherViewPresetFilter.value === 'none' && row.presetRoom) return false

      return true
    })
  })

  const getTeacherRowDisplay = (teacher: any, roomNum: number) => {
    if (!teacher) {
      return {
        name: '',
        gender: '',
        source: '',
        className: 'text-slate-300',
      }
    }

    return {
      name: teacher.isExempt
        ? '无需编排'
        : teacher.isLocked
          ? `${teacher.name}[锁]`
          : teacher.presetRoom && Number(teacher.presetRoom) === roomNum
            ? `${teacher.name}[预]`
            : teacher.name,
      gender: teacher.isExempt
        ? ''
        : teacher.gender === 'M'
          ? '男'
          : teacher.gender === 'F'
            ? '女'
            : '',
      source: teacher.isExempt
        ? ''
        : teacher.isInternal === true
          ? '本校'
          : teacher.isInternal === false
            ? '外校'
            : '',
      className: teacher.isExempt
        ? 'text-amber-600 font-semibold'
        : teacher.isLocked
          ? 'text-rose-600 font-semibold'
          : teacher.presetRoom && Number(teacher.presetRoom) === roomNum
            ? 'text-emerald-600 font-semibold'
            : teacher.gender === 'M'
              ? 'text-blue-600'
              : teacher.gender === 'F'
                ? 'text-fuchsia-600'
                : 'text-slate-700',
    }
  }

  const subjectTableData = computed(() => {
    if (!selectedSubjectId.value) return []
    const session = schedule.value.find((s) => s.subjectId === selectedSubjectId.value)
    if (!session) return []

    return session.rooms.map((r: any) => {
      const roomNum = Number(r.roomNum ?? r.id)
      const row: any = { roomLabel: `考场${roomNum}` }
      const ts = r.teachers || []

      const teacher1 = getTeacherRowDisplay(ts[0], roomNum)
      row.t1_name = teacher1.name
      row.t1_gender = teacher1.gender
      row.t1_source = teacher1.source
      row.t1_class = teacher1.className

      if (config.mode === 'double') {
        const teacher2 = getTeacherRowDisplay(ts[1], roomNum)
        row.t2_name = teacher2.name
        row.t2_gender = teacher2.gender
        row.t2_source = teacher2.source
        row.t2_class = teacher2.className
      }

      return row
    })
  })

  return {
    subjectCount,
    canSchedule,
    hasSchedule,
    missingSlots,
    canContinue,
    getTeacherText,
    getTeacherTextClass,
    getUnavailableNames,
    matrixData,
    teacherStats,
    teacherViewRows,
    teacherViewTableData,
    subjectTableData,
  }
}
