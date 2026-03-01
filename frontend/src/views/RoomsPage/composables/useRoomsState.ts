import { ref, reactive, computed } from 'vue'

export type UiLogLevel = 'info' | 'success' | 'warning' | 'error'

export interface RoomsConfig {
  totalRooms: number
  seatsPerRoom: number
  mode: string
  subjectPriorityOrder: string[]
}

export interface LoadingStates {
  arranging: boolean
  importing: boolean
  exporting: boolean
}

export const SUBJECT_PRIORITY_DEFAULT = ['化学', '生物', '政治', '地理']

export function useRoomsState() {
  // UI State
  const sidebarCollapsed = ref(false)
  const activeTab = ref('settings') // 'settings' | 'students' | 'results'
  const showLogs = ref(false)

  // Data State
  const students = ref<any[]>([])
  const results = ref<any[]>([])
  const roomSettings = ref<any[]>([])
  const studentPath = ref('')
  const cachedResultsPath = ref('')

  // Configuration
  const config = reactive<RoomsConfig>({
    totalRooms: 30,
    seatsPerRoom: 30,
    mode: 'normal',
    subjectPriorityOrder: [...SUBJECT_PRIORITY_DEFAULT]
  })

  // Pagination State - Results
  const searchQuery = ref('')
  const currentPage = ref(1)
  const pageSize = ref(50)

  // Pagination State - Students
  const studentCurrentPage = ref(1)
  const studentPageSize = ref(50)

  // Loading States
  const loading = reactive<LoadingStates>({
    arranging: false,
    importing: false,
    exporting: false
  })

  // Subject Priority Dialog State
  const showSubjectPriorityDialog = ref(false)
  const savingSubjectPriority = ref(false)
  const subjectPriorityDraft = ref<string[]>([...SUBJECT_PRIORITY_DEFAULT])
  const draggingSubjectIndex = ref<number | null>(null)
  const dragOverSubjectIndex = ref<number | null>(null)

  // Computed
  const canArrange = computed(() => students.value.length > 0)
  const hasResults = computed(() => results.value.length > 0)
  const hasSettings = computed(() => roomSettings.value.length > 0)
  const hasStudents = computed(() => students.value.length > 0)

  const filteredResults = computed(() => {
    if (!searchQuery.value) return results.value
    const q = searchQuery.value.toLowerCase()
    return results.value.filter(r =>
      String(r['姓名']).toLowerCase().includes(q) ||
      String(r['考号']).toLowerCase().includes(q)
    )
  })

  const pagedResults = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    return filteredResults.value.slice(start, start + pageSize.value)
  })

  const pagedStudents = computed(() => {
    const start = (studentCurrentPage.value - 1) * studentPageSize.value
    return students.value.slice(start, start + studentPageSize.value)
  })

  // Helper Methods
  const indexMethod = (index: number) => {
    return (currentPage.value - 1) * pageSize.value + index + 1
  }

  const studentIndexMethod = (index: number) => {
    return (studentCurrentPage.value - 1) * studentPageSize.value + index + 1
  }

  // Reset Method
  const resetState = () => {
    roomSettings.value = []
    students.value = []
    results.value = []
    studentPath.value = ''
    cachedResultsPath.value = ''

    searchQuery.value = ''
    currentPage.value = 1
    pageSize.value = 50
    studentCurrentPage.value = 1
    studentPageSize.value = 50

    config.totalRooms = 30
    config.seatsPerRoom = 30
    config.mode = 'normal'
    config.subjectPriorityOrder = [...SUBJECT_PRIORITY_DEFAULT]

    sidebarCollapsed.value = false
    activeTab.value = 'settings'
    showLogs.value = false
  }

  return {
    // UI State
    sidebarCollapsed,
    activeTab,
    showLogs,

    // Data State
    students,
    results,
    roomSettings,
    studentPath,
    cachedResultsPath,

    // Configuration
    config,

    // Pagination
    searchQuery,
    currentPage,
    pageSize,
    studentCurrentPage,
    studentPageSize,

    // Loading
    loading,

    // Subject Priority Dialog
    showSubjectPriorityDialog,
    savingSubjectPriority,
    subjectPriorityDraft,
    draggingSubjectIndex,
    dragOverSubjectIndex,

    // Computed
    canArrange,
    hasResults,
    hasSettings,
    hasStudents,
    filteredResults,
    pagedResults,
    pagedStudents,

    // Methods
    indexMethod,
    studentIndexMethod,
    resetState,

    // Constants
    SUBJECT_PRIORITY_DEFAULT
  }
}
