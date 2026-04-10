import { computed, reactive, ref } from 'vue'
import { formatActionSuccess } from '@/lib/uiFeedback'
import type { Subject } from '../types'

interface UseSubjectsFormOptions {
  subjects: { value: Subject[] }
  syncToBackend: () => Promise<void>
  validateData: () => Promise<void>
  logInfo: (msg: string) => void
}

const createEmptySubject = (): Subject => ({
  name: '',
  exam_date: '',
  exam_time: '',
  duration_minutes: 0,
  room_count: 0,
  remark: '',
})

export function useSubjectsForm({
  subjects,
  syncToBackend,
  validateData,
  logInfo,
}: UseSubjectsFormOptions) {
  const dialogVisible = ref(false)
  const isEdit = ref(false)
  const editingIndex = ref(-1)
  const formRef = ref()
  const form = reactive<Subject>(createEmptySubject())

  const rules = {
    name: [{ required: true, message: '请输入科目名称', trigger: 'blur' }],
    exam_date: [{ required: true, message: '请选择考试日期', trigger: 'change' }],
    exam_time: [
      { required: true, message: '请选择考试时间段', trigger: 'change' },
      { pattern: /^\d{1,2}:\d{2}-\d{1,2}:\d{2}$/, message: '格式应为 HH:mm-HH:mm', trigger: 'change' },
    ],
  }

  const resetFormState = () => {
    dialogVisible.value = false
    isEdit.value = false
    editingIndex.value = -1
    Object.assign(form, createEmptySubject())
  }

  const handleAdd = () => {
    isEdit.value = false
    editingIndex.value = -1
    Object.assign(form, createEmptySubject())
    dialogVisible.value = true
  }

  const handleEdit = (row: Subject, index: number) => {
    isEdit.value = true
    editingIndex.value = index
    Object.assign(form, { ...row })
    dialogVisible.value = true
  }

  const handleDelete = async (index: number) => {
    const deletedName = subjects.value[index].name
    subjects.value.splice(index, 1)
    await syncToBackend()
    logInfo(formatActionSuccess('删除科目', deletedName))
    await validateData()
  }

  const handleClearAll = async () => {
    subjects.value = []
    await syncToBackend()
    logInfo(formatActionSuccess('清空科目数据'))
  }

  const submitForm = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid: boolean) => {
      if (valid) {
        const newSubject = { ...form }
        if (isEdit.value && editingIndex.value > -1) {
          subjects.value[editingIndex.value] = newSubject
          logInfo(formatActionSuccess('更新科目', newSubject.name))
        } else {
          subjects.value.push(newSubject)
          logInfo(formatActionSuccess('新增科目', newSubject.name))
        }
        await syncToBackend()
        dialogVisible.value = false
        await validateData()
      }
    })
  }

  function calculateDuration() {
    if (!form.exam_time) return
    const match = form.exam_time.match(/^(\d{1,2}):(\d{2})\s*[-~]\s*(\d{1,2}):(\d{2})$/)
    if (!match) return

    const start = Number(match[1]) * 60 + Number(match[2])
    const end = Number(match[3]) * 60 + Number(match[4])
    if (Number.isNaN(start) || Number.isNaN(end)) return

    let diff = end - start
    if (diff < 0) diff += 24 * 60
    form.duration_minutes = diff
  }

  const examTimeRange = computed<[string, string] | undefined>({
    get() {
      const match = form.exam_time.match(/^(\d{1,2}:\d{2})\s*[-~]\s*(\d{1,2}:\d{2})$/)
      if (!match) return undefined
      return [match[1], match[2]]
    },
    set(val) {
      if (Array.isArray(val) && val.length === 2 && val[0] && val[1]) {
        form.exam_time = `${val[0]}-${val[1]}`
        calculateDuration()
        return
      }
      form.exam_time = ''
      form.duration_minutes = 0
    },
  })

  return {
    dialogVisible,
    isEdit,
    formRef,
    form,
    rules,
    handleAdd,
    handleEdit,
    handleDelete,
    handleClearAll,
    submitForm,
    examTimeRange,
    resetFormState,
  }
}
