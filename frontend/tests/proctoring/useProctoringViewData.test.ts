import { reactive, ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { useProctoringViewData } from '@/views/ProctoringPage/composables/useProctoringViewData'

describe('useProctoringViewData', () => {
  it('builds teacher view rows from imported teacher fields and defaults schedule metrics to zero', () => {
    const teacherViewKeyword = ref('')
    const teacherViewGenderFilter = ref<'all' | 'M' | 'F' | 'unknown'>('all')
    const teacherViewSourceFilter = ref<'all' | 'internal' | 'external' | 'unknown'>('all')
    const teacherViewPresetFilter = ref<'all' | 'preset' | 'none'>('all')

    const view = useProctoringViewData({
      config: reactive({
        roomCount: 2,
        mode: 'single',
        balanceMode: 'duration',
        genderMix: false,
        internalMix: false,
        roomRepeatPreference: '',
        avoidConsecutiveSessions: false,
      }),
      subjects: ref([
        { id: '1', name: '语文', time: '09:00-11:00', durationMinutes: 120, roomCount: 1 },
        { id: '2', name: '数学', time: '15:00-17:00', durationMinutes: 120, roomCount: 1 },
      ]),
      teachers: ref([
        {
          id: 't1',
          name: '张老师',
          gender: 'M',
          isInternal: true,
          maxSessions: 3,
          unavailableSubjects: ['1', '数学'],
          previousSupervisionDuration: 90,
          presetRoom: 2,
        },
        {
          id: 't2',
          name: '李老师',
          maxSessions: 2,
          unavailableSubjects: [],
        },
      ]),
      schedule: ref([]),
      selectedSubjectId: ref('1'),
      teacherViewKeyword,
      teacherViewGenderFilter,
      teacherViewSourceFilter,
      teacherViewPresetFilter,
    })

    expect(view.teacherViewRows.value).toEqual([
      {
        name: '张老师',
        gender: 'M',
        genderLabel: '男',
        isInternal: true,
        sourceLabel: '本校',
        maxSessions: 3,
        unavailableSubjects: ['1', '数学'],
        unavailableSubjectsLabel: '语文、数学',
        previousSupervisionDuration: 90,
        presetRoom: 2,
        sessions: 0,
        supervisionDuration: 0,
        totalDuration: 90,
      },
      {
        name: '李老师',
        gender: '',
        genderLabel: '未填写',
        isInternal: undefined,
        sourceLabel: '未填写',
        maxSessions: 2,
        unavailableSubjects: [],
        unavailableSubjectsLabel: '',
        previousSupervisionDuration: 0,
        presetRoom: null,
        sessions: 0,
        supervisionDuration: 0,
        totalDuration: 0,
      },
    ])
  })

  it('filters teacher view rows by name, gender, source, and preset room', () => {
    const teacherViewKeyword = ref('')
    const teacherViewGenderFilter = ref<'all' | 'M' | 'F' | 'unknown'>('all')
    const teacherViewSourceFilter = ref<'all' | 'internal' | 'external' | 'unknown'>('all')
    const teacherViewPresetFilter = ref<'all' | 'preset' | 'none'>('all')

    const view = useProctoringViewData({
      config: reactive({
        roomCount: 1,
        mode: 'single',
        balanceMode: 'duration',
        genderMix: false,
        internalMix: false,
        roomRepeatPreference: '',
        avoidConsecutiveSessions: false,
      }),
      subjects: ref([
        { id: '1', name: '语文', time: '09:00-11:00', durationMinutes: 120, roomCount: 1 },
      ]),
      teachers: ref([
        {
          id: 't1',
          name: '张老师',
          gender: 'M',
          isInternal: true,
          maxSessions: 2,
          presetRoom: 1,
          sessions: 1,
          supervisionDuration: 120,
        },
        {
          id: 't2',
          name: '李老师',
          gender: 'F',
          isInternal: false,
          maxSessions: 2,
          sessions: 0,
          supervisionDuration: 0,
        },
        {
          id: 't3',
          name: '王老师',
          maxSessions: 2,
        },
      ]),
      schedule: ref([]),
      selectedSubjectId: ref('1'),
      teacherViewKeyword,
      teacherViewGenderFilter,
      teacherViewSourceFilter,
      teacherViewPresetFilter,
    })

    expect(view.teacherViewTableData.value.map((row) => row.name)).toEqual(['张老师', '李老师', '王老师'])

    teacherViewKeyword.value = '李'
    expect(view.teacherViewTableData.value.map((row) => row.name)).toEqual(['李老师'])

    teacherViewKeyword.value = ''
    teacherViewGenderFilter.value = 'unknown'
    expect(view.teacherViewTableData.value.map((row) => row.name)).toEqual(['王老师'])

    teacherViewGenderFilter.value = 'all'
    teacherViewSourceFilter.value = 'external'
    expect(view.teacherViewTableData.value.map((row) => row.name)).toEqual(['李老师'])

    teacherViewSourceFilter.value = 'all'
    teacherViewPresetFilter.value = 'preset'
    expect(view.teacherViewTableData.value.map((row) => row.name)).toEqual(['张老师'])

    teacherViewPresetFilter.value = 'none'
    expect(view.teacherViewTableData.value.map((row) => row.name)).toEqual(['李老师', '王老师'])
  })
})
