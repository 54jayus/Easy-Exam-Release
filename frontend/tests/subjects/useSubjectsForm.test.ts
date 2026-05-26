import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { useSubjectsForm } from '@/views/SubjectsPage/composables/useSubjectsForm'
import type { Subject } from '@/views/SubjectsPage/types'

describe('useSubjectsForm', () => {
  it('submits a new subject without changing business flow', async () => {
    const subjects = ref<Subject[]>([])
    const syncToBackend = vi.fn().mockResolvedValue(undefined)
    const validateData = vi.fn().mockResolvedValue(undefined)
    const logInfo = vi.fn()

    const formApi = useSubjectsForm({
      subjects,
      syncToBackend,
      validateData,
      logInfo,
    })

    formApi.handleAdd()
    formApi.form.name = '语文'
    formApi.form.exam_date = '2026-06-07'
    formApi.form.exam_time = '09:00-11:00'
    formApi.form.duration_minutes = 120
    formApi.form.remark = '上午场'

    formApi.formRef.value = {
      validate: async (callback: (valid: boolean) => void) => callback(true),
    }

    await formApi.submitForm()

    expect(subjects.value).toHaveLength(1)
    expect(subjects.value[0].name).toBe('语文')
    expect(syncToBackend).toHaveBeenCalledTimes(1)
    expect(validateData).toHaveBeenCalledTimes(1)
    expect(logInfo).toHaveBeenCalledWith('已新增科目：语文')
    expect(formApi.dialogVisible.value).toBe(false)
  })
})
