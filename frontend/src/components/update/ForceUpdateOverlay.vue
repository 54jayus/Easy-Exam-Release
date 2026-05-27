<template>
  <transition name="fade">
    <div
      v-if="active"
      class="fixed inset-0 z-[220] overflow-y-auto bg-slate-950/60 px-6 py-8 backdrop-blur-sm"
    >
      <div class="mx-auto flex min-h-full w-full max-w-4xl items-center justify-center">
        <section class="w-full overflow-hidden rounded-[28px] border border-rose-100 bg-white shadow-2xl shadow-slate-950/20">
          <div class="bg-[linear-gradient(135deg,#dc2626_0%,#f97316_100%)] px-6 py-6 text-white md:px-8">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div class="max-w-2xl">
                <div class="text-xs font-semibold uppercase tracking-[0.28em] text-white/75">Mandatory Update</div>
                <h2 class="mt-3 text-2xl font-bold tracking-tight md:text-[28px]">更新后才能继续使用软件</h2>
                <p class="mt-2 text-sm leading-6 text-white/85">
                  当前版本 v{{ currentVersion }} 低于要求版本 v{{ targetVersion || '--' }}，
                  请先完成升级，再继续使用智能考务系统。
                </p>
              </div>
              <div class="rounded-full border border-white/25 bg-white/12 px-4 py-1.5 text-sm font-semibold text-white shadow-sm">
                强制更新
              </div>
            </div>
          </div>

          <div class="space-y-5 px-6 py-6 md:px-8">
            <UpdateDetailsContent
              accent="rose"
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
              @toggle-notes="$emit('toggle-notes')"
              @toggle-history="$emit('toggle-history')"
              @retry-history="$emit('retry-history')"
              @open-release-page="(url) => $emit('open-release-page', url)"
            />

            <div class="flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-5">
              <el-button
                v-if="updateStatus === 'available'"
                type="primary"
                :disabled="!canDownload"
                @click="$emit('download')"
              >
                下载并更新
              </el-button>
              <el-button
                v-else-if="updateStatus === 'downloaded'"
                type="primary"
                @click="$emit('install')"
              >
                立即安装新版本
              </el-button>
              <el-button
                v-else-if="updateStatus === 'checking' || updateStatus === 'downloading'"
                type="primary"
                loading
                disabled
              >
                {{ updateStatus === 'checking' ? '正在检查' : '正在下载' }}
              </el-button>
              <el-button
                v-else
                type="primary"
                @click="$emit('check')"
              >
                重新检查更新
              </el-button>
            </div>
          </div>
        </section>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import UpdateDetailsContent from './UpdateDetailsContent.vue'
import type { ForceUpdateSnapshot, UpdateHistoryEntry, UpdateStatus } from '@/types/appUpdate'

const props = defineProps<{
  active: boolean
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
  forceUpdateMeta: ForceUpdateSnapshot | null
}>()

defineEmits<{
  check: []
  download: []
  install: []
  'toggle-notes': []
  'toggle-history': []
  'retry-history': []
  'open-release-page': [url: string]
}>()

const targetVersion = computed(() => props.latestVersion || props.forceUpdateMeta?.version || '')
</script>
