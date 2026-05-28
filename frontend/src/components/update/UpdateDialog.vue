<template>
  <el-dialog
    :model-value="modelValue"
    title="软件更新"
    width="540px"
    align-center
    class="rounded-2xl"
    @update:model-value="handleModelValueChange"
  >
    <div class="max-h-[calc(80vh-160px)] overflow-y-auto pr-1 custom-scrollbar">
      <UpdateDetailsContent
        accent="primary"
        :current-version="currentVersion"
        :latest-version="latestVersion"
        :release-date="releaseDate"
        :notes="notes"
        :visible-notes="visibleNotes"
        :show-all-notes="showAllNotes"
        :show-history-panel="showHistoryPanel"
        :history-loading="historyLoading"
        :history-error="historyError"
        :update-history="updateHistory"
        :update-status="updateStatus"
        :update-status-title="updateStatusTitle"
        :update-status-description="updateStatusDescription"
        :update-status-message="updateStatusMessage"
        :update-status-title-class="updateStatusTitleClass"
        :update-status-panel-class="updateStatusPanelClass"
        :update-status-chip-text="updateStatusChipText"
        :update-status-chip-class="updateStatusChipClass"
        :download-progress="downloadProgress"
        :show-up-to-date-card="updateStatus === 'up_to_date'"
        @toggle-notes="$emit('toggle-notes')"
        @toggle-history="$emit('toggle-history')"
        @retry-history="$emit('retry-history')"
        @open-release-page="(url) => $emit('open-release-page', url)"
      />
    </div>

    <template #footer>
      <div class="flex items-center justify-end gap-2">
        <el-button
          v-if="updateStatus === 'available'"
          type="primary"
          :disabled="!canDownload"
          @click="$emit('download')"
        >
          立即下载
        </el-button>
        <el-button
          v-else-if="updateStatus === 'paused'"
          type="primary"
          @click="$emit('download')"
        >
          继续下载
        </el-button>
        <el-button
          v-else-if="updateStatus === 'downloading'"
          @click="$emit('pause')"
        >
          暂停
        </el-button>
        <el-button
          v-else-if="updateStatus === 'downloaded'"
          type="primary"
          @click="$emit('install')"
        >
          立即安装
        </el-button>
        <el-button
          v-else-if="updateStatus === 'checking'"
          type="primary"
          loading
          disabled
        >
          正在检查
        </el-button>
        <el-button
          v-else
          type="primary"
          @click="$emit('check')"
        >
          重新检查
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import UpdateDetailsContent from './UpdateDetailsContent.vue'
import { useSmoothProgress } from '@/composables/useSmoothProgress'
import type { UpdateHistoryEntry, UpdateStatus } from '@/types/appUpdate'

const props = defineProps<{
  modelValue: boolean
  currentVersion: string
  latestVersion: string
  releaseDate: string
  notes: string[]
  visibleNotes: string[]
  showAllNotes: boolean
  showHistoryPanel: boolean
  historyLoading: boolean
  historyError: string
  updateHistory: UpdateHistoryEntry[]
  updateStatus: UpdateStatus
  updateStatusTitle: string
  updateStatusDescription: string
  updateStatusMessage: string
  updateStatusTitleClass: string
  updateStatusPanelClass: string
  updateStatusChipText: string
  updateStatusChipClass: string
  downloadProgress: number
  canDownload: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
  check: []
  download: []
  pause: []
  install: []
  'toggle-notes': []
  'toggle-history': []
  'retry-history': []
  'open-release-page': [url: string]
}>()

const handleModelValueChange = (value: boolean) => {
  emit('update:modelValue', value)
  if (!value) {
    emit('close')
  }
}

const smoothProgress = useSmoothProgress(toRef(props, 'downloadProgress'))
</script>
