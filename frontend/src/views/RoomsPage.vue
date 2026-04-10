<template>
  <div class="h-full flex bg-slate-50/50 animate-fade-in relative overflow-hidden font-sans text-slate-600">
    <!-- Background Pattern -->
    <div class="absolute inset-0 z-0 pointer-events-none opacity-[0.03]"
         style="background-image: radial-gradient(#64748b 1px, transparent 1px); background-size: 24px 24px;">
    </div>

    <!-- Left Sidebar -->
    <RoomsSidebar
      v-model:collapsed="sidebarCollapsed"
      v-model:config="config"
      :has-settings="hasSettings"
      :has-students="hasStudents"
      :has-results="hasResults"
      :can-arrange="canArrange"
      :students-count="students.length"
      :seats-per-room-info="seatsPerRoomInfo"
      :is-exporting="isExporting"
      @generate-template="handleGenerateTemplate"
      @import-settings="handleImportSettings"
      @import-students="handleImportStudents"
      @import-results="handleImportResults"
      @clear-settings="handleClearSettings"
      @clear-students="handleClearStudents"
      @arrange="handleArrange"
      @export="handleExport"
      @reset="handleResetPage"
      @open-priority-dialog="showSubjectPriorityDialog = true"
      @open-gaokao-time-dialog="showGaokaoTimeDialog = true"
      @update:mode="(mode: string) => config.mode = mode"
      @update:totalRooms="(val: number) => config.totalRooms = val"
      @update:seatsPerRoom="(val: number) => config.seatsPerRoom = val"
    />

    <!-- Toggle Button (Visible when collapsed) -->
    <div
      v-if="sidebarCollapsed"
      class="absolute left-0 top-6 z-30 bg-white border border-l-0 border-slate-200 p-2 rounded-r-xl shadow-lg cursor-pointer hover:bg-blue-50 hover:text-blue-600 transition-all hover:pl-3"
      @click="sidebarCollapsed = false"
    >
      <el-icon><Expand /></el-icon>
    </div>

    <!-- Right Main Content -->
    <RoomsDataTabs
      v-model:active-tab="activeTab"
      :settings="roomSettings"
      :students="students"
      :results="results"
      :filtered-results="filteredResults"
      v-model:students-page="studentCurrentPage"
      v-model:students-page-size="studentPageSize"
      v-model:results-page="currentPage"
      v-model:results-page-size="pageSize"
      v-model:search-query="searchQuery"
      :mode="config.mode"
      :logs-count="logs.length"
      @reimport-settings="handleImportSettings"
      @reimport-students="handleImportStudents"
      @open-logs="showLogs = true"
    />

    <!-- Subject Priority Dialog -->
    <SubjectPriorityDialog
      v-model:visible="showSubjectPriorityDialog"
      v-model:priority-order="config.subjectPriorityOrder"
      @log-success="logSuccess"
      @log-error="logError"
    />

    <!-- Gaokao Time Settings Dialog -->
    <GaokaoTimeSettingsDialog
      v-model:visible="showGaokaoTimeDialog"
      v-model:settings="gaokaoTimeSettings"
      @log-success="logSuccess"
      @log-error="logError"
    />

    <!-- Logs Drawer -->
    <OperationLogsDrawer
      v-model:visible="showLogs"
      :logs="logs"
      :modal="false"
      size="380px"
      @clear-logs="clearLogs"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Expand } from '@element-plus/icons-vue'
import { pythonBackend } from '@/lib/pythonBackend'
import { applyPageReset } from '@/composables/useAppCacheControl'
import { useUiLogs } from '@/composables/useUiLogs'
import OperationLogsDrawer from '@/components/OperationLogsDrawer.vue'
import {
  createUiFeedback,
  formatActionError,
  formatActionSuccess,
  formatActionWarning,
} from '@/lib/uiFeedback'
import RoomsSidebar from './RoomsPage/RoomsSidebar.vue'
import RoomsDataTabs from './RoomsPage/RoomsDataTabs.vue'
import SubjectPriorityDialog from './RoomsPage/SubjectPriorityDialog.vue'
import GaokaoTimeSettingsDialog from './RoomsPage/GaokaoTimeSettingsDialog.vue'
import { GAOKAO_TIME_DEFAULTS } from '@/types/gaokao'
import type { GaokaoTimeSettings } from '@/types/gaokao'
import {
  useRoomsState,
  useRoomsPersistence,
  useRoomsArrangement,
  useRoomsIO,
  SUBJECT_PRIORITY_DEFAULT
} from './RoomsPage/composables'

// Initialize composables
const {
  sidebarCollapsed,
  activeTab,
  showLogs,
  students,
  results,
  roomSettings,
  studentPath,
  cachedResultsPath,
  config,
  searchQuery,
  currentPage,
  pageSize,
  studentCurrentPage,
  studentPageSize,
  showSubjectPriorityDialog,
  canArrange,
  hasResults,
  hasSettings,
  hasStudents,
  filteredResults,
  seatsPerRoomInfo,
  resetState
} = useRoomsState()

// Gaokao Time Settings State
const showGaokaoTimeDialog = ref(false)
const gaokaoTimeSettings = ref<GaokaoTimeSettings>(JSON.parse(JSON.stringify(GAOKAO_TIME_DEFAULTS)))

const {
  initializeFromStorage,
  setupWatchers
} = useRoomsPersistence()

const {
  logs,
  logInfo,
  logSuccess,
  logWarning,
  logError,
  logFromText,
  clearLogs
} = useUiLogs()

const feedback = createUiFeedback({ logInfo, logSuccess, logWarning, logError })

const { handleArrange } = useRoomsArrangement({
  studentPath,
  roomSettings,
  config,
  students,
  results,
  activeTab,
  logInfo,
  logSuccess,
  logError
})

const {
  handleGenerateTemplate,
  handleImportSettings,
  handleImportStudents,
  handleImportResults,
  handleExport,
  isExporting
} = useRoomsIO({
  roomSettings,
  students,
  results,
  studentPath,
  cachedResultsPath,
  config,
  activeTab,
  logInfo,
  logSuccess,
  logError,
  logFromText
})

// Initialize from storage
const stored = initializeFromStorage()
sidebarCollapsed.value = stored.sidebarCollapsed
activeTab.value = stored.activeTab
cachedResultsPath.value = stored.cachedResultsPath

// Setup persistence watchers
setupWatchers({
  sidebarCollapsed,
  activeTab,
  cachedResultsPath
})

// Normalize subject priority order
const normalizeSubjectPriorityOrder = (order: unknown): string[] => {
  const allowed = SUBJECT_PRIORITY_DEFAULT
  if (!Array.isArray(order)) return [...allowed]
  const cleaned = order.map((v) => String(v || '').trim()).filter((v) => allowed.includes(v))
  const dedup: string[] = []
  for (const s of cleaned) {
    if (!dedup.includes(s)) dedup.push(s)
  }
  for (const s of allowed) {
    if (!dedup.includes(s)) dedup.push(s)
  }
  return dedup.slice(0, allowed.length)
}

// Reset page handler
const handleResetPage = async () => {
  try {
    await feedback.confirmWarning({
      message: '确定要初始化当前页面吗？这将清除所有考场数据与设置。',
      title: '初始化页面',
      confirmButtonText: '初始化',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  const res = await pythonBackend.request<any>('rooms.resetState', {})
  if (res?.error) {
    feedback.error(res.error, {
      logMessage: formatActionError('初始化页面', res.error),
    })
    return
  }

  resetState()
  clearLogs()
  showLogs.value = false
  applyPageReset('rooms')

  feedback.success('页面已初始化', {
    logMessage: formatActionSuccess('初始化考场编排页面'),
  })
}

// Clear settings handler
const handleClearSettings = async () => {
  try {
    await feedback.confirmWarning({
      message: '确定要清除考场设置数据吗？',
      title: '清除考场设置',
      confirmButtonText: '清除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  roomSettings.value = []
  config.totalRooms = 30
  feedback.success('已清除考场设置', {
    logMessage: formatActionSuccess('清除考场设置数据'),
  })
}

// Clear students handler
const handleClearStudents = async () => {
  try {
    await feedback.confirmWarning({
      message: '确定要清除考生名册数据吗？',
      title: '清除考生名册',
      confirmButtonText: '清除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  students.value = []
  studentPath.value = ''
  feedback.success('已清除考生名册', {
    logMessage: formatActionSuccess('清除考生名册数据'),
  })
}

// Lifecycle
onMounted(async () => {
  let res: any = null
  try {
    res = await pythonBackend.request<any>('rooms.getState')
  } catch (e) {
    logError(formatActionError('加载考场编排状态', e))
  }

  if (res) {
    if (res.settings) roomSettings.value = res.settings
    if (res.students) students.value = res.students
    if (res.results) results.value = res.results
    if (res.config) Object.assign(config, res.config)
    if (res.studentPath) studentPath.value = res.studentPath
  }

  config.subjectPriorityOrder = normalizeSubjectPriorityOrder((res?.config || {}).subjectPriorityOrder ?? config.subjectPriorityOrder)

  // 加载高考时间设置
  try {
    const timeRes = await pythonBackend.request('rooms.getGaokaoTimeSettings', {})
    if (timeRes?.settings) {
      gaokaoTimeSettings.value = timeRes.settings
    }
  } catch (e) {
    console.error('Failed to load gaokao time settings:', e)
  }

  if ((!results.value || results.value.length === 0) && cachedResultsPath.value) {
    try {
      const r = await pythonBackend.request<any>('rooms.importResults', { path: cachedResultsPath.value })
      if (r?.results) {
        results.value = r.results
        logInfo(formatActionSuccess('恢复编排结果', `共 ${r.results.length} 人`))
      }
    } catch (e) {
      logWarning(formatActionWarning('恢复编排结果', e instanceof Error ? e.message : String(e)))
    }
  }
})
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Optimize Tabs for compact layout */
:deep(.el-tabs__item) {
  padding: 0 10px !important;
  font-size: 13px;
}
:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #e2e8f0;
}
:deep(.el-tabs__active-bar) {
  height: 2px;
  background-color: #3b82f6;
}
</style>
