export const GAOKAO_SUBJECT_ORDER = [
  '语文', '数学', '物理历史', '英语', '化学', '地理', '政治', '生物'
] as const

export const GAOKAO_ELECTIVE_SUBJECTS = ['化学', '地理', '政治', '生物'] as const

export type GaokaoSubjectKey = typeof GAOKAO_SUBJECT_ORDER[number]
export type GaokaoElectiveSubjectKey = typeof GAOKAO_ELECTIVE_SUBJECTS[number]

export interface SubjectTimeConfig {
  subjectName?: string
  date: string      // ISO格式: "2024-06-07"
  startTime: string // 24小时制: "09:00"
  endTime: string   // 24小时制: "11:30"
}

export interface GaokaoTimeSettings {
  examTimes: Record<GaokaoSubjectKey, SubjectTimeConfig>
  selfStudyTimes: Record<GaokaoElectiveSubjectKey, SubjectTimeConfig>
}

const GAOKAO_TIME_RANGES: Record<GaokaoSubjectKey, { startTime: string; endTime: string }> = {
  语文: { startTime: '09:00', endTime: '11:30' },
  数学: { startTime: '15:00', endTime: '17:00' },
  物理历史: { startTime: '09:00', endTime: '10:15' },
  英语: { startTime: '15:00', endTime: '17:00' },
  化学: { startTime: '08:30', endTime: '09:45' },
  地理: { startTime: '11:00', endTime: '12:15' },
  政治: { startTime: '14:30', endTime: '15:45' },
  生物: { startTime: '17:00', endTime: '18:15' },
}

function formatDate(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function buildGaokaoTimeDefaults(today = new Date()): GaokaoTimeSettings {
  const date = formatDate(today)
  const examTimes = Object.fromEntries(
    GAOKAO_SUBJECT_ORDER.map((subject) => [
      subject,
      {
        subjectName: subject,
        date,
        startTime: GAOKAO_TIME_RANGES[subject].startTime,
        endTime: GAOKAO_TIME_RANGES[subject].endTime,
      }
    ])
  ) as Record<GaokaoSubjectKey, SubjectTimeConfig>

  const selfStudyTimes = Object.fromEntries(
    GAOKAO_ELECTIVE_SUBJECTS.map((subject) => [
      subject,
      {
        date,
        startTime: GAOKAO_TIME_RANGES[subject].startTime,
        endTime: GAOKAO_TIME_RANGES[subject].endTime,
      }
    ])
  ) as Record<GaokaoElectiveSubjectKey, SubjectTimeConfig>

  return { examTimes, selfStudyTimes }
}

export function normalizeGaokaoTimeSettings(settings: unknown): GaokaoTimeSettings {
  const defaults = buildGaokaoTimeDefaults()
  const raw = (settings && typeof settings === 'object') ? settings as Partial<GaokaoTimeSettings> : {}
  const rawExamTimes = (raw.examTimes && typeof raw.examTimes === 'object'
    ? raw.examTimes
    : {}) as Partial<Record<GaokaoSubjectKey, Partial<SubjectTimeConfig>>>
  const rawSelfStudyTimes = (raw.selfStudyTimes && typeof raw.selfStudyTimes === 'object'
    ? raw.selfStudyTimes
    : {}) as Partial<Record<GaokaoElectiveSubjectKey, Partial<SubjectTimeConfig>>>

  const examTimes = Object.fromEntries(
    GAOKAO_SUBJECT_ORDER.map((subject) => {
      const defaultItem = defaults.examTimes[subject]
      const rawItem = rawExamTimes[subject] && typeof rawExamTimes[subject] === 'object' ? rawExamTimes[subject] : {}
      return [
        subject,
        {
          subjectName: String(
            Object.prototype.hasOwnProperty.call(rawItem, 'subjectName')
              ? rawItem.subjectName
              : defaultItem.subjectName ?? subject
          ).trim() || subject,
          date: String(
            Object.prototype.hasOwnProperty.call(rawItem, 'date')
              ? rawItem.date
              : defaultItem.date ?? ''
          ).trim(),
          startTime: String(
            Object.prototype.hasOwnProperty.call(rawItem, 'startTime')
              ? rawItem.startTime
              : defaultItem.startTime ?? ''
          ).trim(),
          endTime: String(
            Object.prototype.hasOwnProperty.call(rawItem, 'endTime')
              ? rawItem.endTime
              : defaultItem.endTime ?? ''
          ).trim(),
        }
      ]
    })
  ) as Record<GaokaoSubjectKey, SubjectTimeConfig>

  const selfStudyTimes = Object.fromEntries(
    GAOKAO_ELECTIVE_SUBJECTS.map((subject) => {
      const defaultItem = defaults.selfStudyTimes[subject]
      const rawItem = rawSelfStudyTimes[subject] && typeof rawSelfStudyTimes[subject] === 'object' ? rawSelfStudyTimes[subject] : {}
      return [
        subject,
        {
          date: String(
            Object.prototype.hasOwnProperty.call(rawItem, 'date')
              ? rawItem.date
              : defaultItem.date ?? ''
          ).trim(),
          startTime: String(
            Object.prototype.hasOwnProperty.call(rawItem, 'startTime')
              ? rawItem.startTime
              : defaultItem.startTime ?? ''
          ).trim(),
          endTime: String(
            Object.prototype.hasOwnProperty.call(rawItem, 'endTime')
              ? rawItem.endTime
              : defaultItem.endTime ?? ''
          ).trim(),
        }
      ]
    })
  ) as Record<GaokaoElectiveSubjectKey, SubjectTimeConfig>

  return { examTimes, selfStudyTimes }
}

export const GAOKAO_TIME_DEFAULTS: GaokaoTimeSettings = buildGaokaoTimeDefaults()
