<template>
  <div class="space-y-5 py-1">
    <template v-if="showUpToDateCard">
      <div class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 flex items-center gap-3">
        <div class="w-9 h-9 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
          <el-icon class="text-white text-base"><Check /></el-icon>
        </div>
        <div>
          <div class="text-sm font-semibold text-emerald-800">当前已是最新版本</div>
          <div class="mt-0.5 text-xs text-emerald-600">
            v{{ currentVersion }}{{ releaseDate ? ` · 发布于 ${releaseDate}` : '' }}
          </div>
        </div>
      </div>
    </template>
    <template v-else>
      <div class="grid grid-cols-2 gap-3">
        <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
          <div class="text-xs font-medium text-slate-500">当前版本</div>
          <div class="mt-1 text-lg font-bold text-slate-900">v{{ currentVersion }}</div>
        </div>
        <div :class="latestVersionCardClass" class="rounded-2xl border px-4 py-3">
          <div :class="latestVersionLabelClass" class="text-xs font-medium">最新版本</div>
          <div :class="latestVersionValueClass" class="mt-1 text-lg font-bold">
            {{ latestVersion ? `v${latestVersion}` : '暂无可用更新' }}
          </div>
          <div v-if="releaseDate" :class="latestVersionDateClass" class="mt-1 text-xs">发布时间：{{ releaseDate }}</div>
        </div>
      </div>
    </template>

    <div class="rounded-2xl border px-4 py-3" :class="updateStatusPanelClass">
      <div class="flex items-center justify-between gap-3">
        <div>
          <div class="text-sm font-semibold" :class="updateStatusTitleClass">{{ updateStatusTitle }}</div>
          <div class="mt-1 text-xs text-slate-500">{{ updateStatusDescription }}</div>
        </div>
        <div class="rounded-full px-3 py-1 text-xs font-semibold" :class="updateStatusChipClass">
          {{ updateStatusChipText }}
        </div>
      </div>
      <div v-if="updateStatus === 'downloading' || updateStatus === 'paused'" class="mt-4 space-y-2">
        <el-progress :percentage="smoothProgress" :stroke-width="10" :show-text="false" />
        <div class="text-right text-xs text-slate-500">已下载 {{ smoothProgress.toFixed(1) }}%</div>
      </div>
      <div v-if="updateStatusMessage" class="mt-3 text-xs leading-5 text-slate-500">
        {{ updateStatusMessage }}
      </div>
    </div>

    <div class="rounded-2xl border border-slate-200 bg-white px-4 py-4">
      <div class="text-sm font-semibold text-slate-800 mb-3">更新内容</div>
      <ul v-if="notes.length" class="space-y-2 text-sm text-slate-600">
        <li v-for="item in visibleNotes" :key="item" class="flex items-start gap-2">
          <span :class="noteDotClass" class="mt-1 h-1.5 w-1.5 rounded-full flex-shrink-0" />
          <span>{{ item }}</span>
        </li>
      </ul>
      <div v-else class="text-sm text-slate-500">当前版本暂未提供额外更新说明。</div>
      <div class="mt-3 flex items-center justify-between">
        <el-button
          v-if="notes.length > 4"
          link
          :class="notesActionClass"
          @click="$emit('toggle-notes')"
        >
          {{ showAllNotes ? '▴ 收起' : `▾ 展开全部 ${notes.length} 条` }}
        </el-button>
        <span v-else />
        <el-button link :class="notesActionClass" @click="$emit('toggle-history')">
          {{ showHistoryPanel ? '收起历史记录' : '查看历史更新' }}
        </el-button>
      </div>
    </div>

    <transition name="fade-slide">
      <div
        v-if="showHistoryPanel"
        class="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-4"
      >
        <div class="flex items-center justify-between gap-3">
          <div>
            <div class="text-sm font-semibold text-slate-800">历史更新记录</div>
            <div class="mt-1 text-xs text-slate-500">可在软件内快速查看以往版本的发布时间与更新说明。</div>
          </div>
          <el-button
            v-if="historyError"
            link
            :class="notesActionClass"
            @click="$emit('retry-history')"
          >
            重试
          </el-button>
        </div>

        <div v-if="historyLoading" class="mt-4 flex items-center gap-2 text-sm text-slate-500">
          <el-icon class="animate-spin"><RefreshRight /></el-icon>
          正在加载历史更新记录...
        </div>

        <div v-else-if="historyError" class="mt-4 rounded-xl border border-rose-100 bg-rose-50 px-3 py-3 text-sm text-rose-600">
          {{ historyError }}
        </div>

        <div v-else-if="updateHistory.length" class="mt-4 max-h-60 overflow-y-auto pr-1 custom-scrollbar">
          <div
            v-for="(entry, index) in updateHistory"
            :key="entry.version"
            class="flex gap-3"
          >
            <div class="flex flex-col items-center flex-shrink-0">
              <div
                class="w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0"
                :class="entry.version === currentVersion ? activeHistoryDotClass : 'bg-slate-300'"
              />
              <div
                v-if="index < updateHistory.length - 1"
                class="w-px flex-1 min-h-4 bg-slate-200 my-1"
              />
            </div>
            <div class="flex-1 pb-4">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-sm font-semibold text-slate-800">v{{ entry.version }}</span>
                <span v-if="entry.title && entry.title !== `Easy Exam.v${entry.version}`" class="text-xs text-slate-500">{{ entry.title }}</span>
                <span
                  v-if="entry.version === currentVersion"
                  :class="currentVersionBadgeClass"
                  class="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                >
                  当前版本
                </span>
                <span class="text-xs text-slate-400 ml-auto">{{ entry.releaseDate || '未提供' }}</span>
                <el-button
                  v-if="entry.releasePageUrl"
                  link
                  :class="notesActionClass"
                  @click="$emit('open-release-page', entry.releasePageUrl!)"
                >
                  查看发布页
                </el-button>
              </div>
              <ul v-if="entry.notes.length" class="mt-2 space-y-1 text-xs text-slate-600">
                <li
                  v-for="item in entry.notes"
                  :key="`${entry.version}-${item}`"
                  class="flex items-start gap-1.5"
                >
                  <span :class="historyNoteDotClass" class="mt-1 h-1 w-1 rounded-full flex-shrink-0" />
                  <span>{{ item }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div v-else class="mt-4 text-sm text-slate-500">
          暂时还没有可展示的历史更新记录。
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import { Check, RefreshRight } from '@element-plus/icons-vue'
import { useSmoothProgress } from '@/composables/useSmoothProgress'
import type { UpdateHistoryEntry, UpdateStatus } from '@/types/appUpdate'

const props = withDefaults(defineProps<{
  accent?: 'primary' | 'rose'
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
  showUpToDateCard?: boolean
}>(), {
  accent: 'primary',
  showUpToDateCard: false,
})

defineEmits<{
  'toggle-notes': []
  'toggle-history': []
  'retry-history': []
  'open-release-page': [url: string]
}>()

const smoothProgress = useSmoothProgress(toRef(props, 'downloadProgress'))

const latestVersionCardClass = computed(() =>
  props.accent === 'rose' ? 'border-rose-100 bg-rose-50' : 'border-primary-100 bg-primary-50'
)
const latestVersionLabelClass = computed(() =>
  props.accent === 'rose' ? 'text-rose-500' : 'text-primary-500'
)
const latestVersionValueClass = computed(() =>
  props.accent === 'rose' ? 'text-rose-700' : 'text-primary-700'
)
const latestVersionDateClass = computed(() =>
  props.accent === 'rose' ? 'text-rose-500' : 'text-primary-500'
)
const noteDotClass = computed(() =>
  props.accent === 'rose' ? 'bg-rose-400' : 'bg-primary-400'
)
const notesActionClass = computed(() =>
  props.accent === 'rose'
    ? '!px-0 !text-rose-600 !text-xs'
    : '!px-0 !text-primary-600 !text-xs'
)
const activeHistoryDotClass = computed(() =>
  props.accent === 'rose' ? 'bg-rose-500' : 'bg-primary-500'
)
const currentVersionBadgeClass = computed(() =>
  props.accent === 'rose'
    ? 'bg-rose-50 text-rose-600'
    : 'bg-primary-50 text-primary-600'
)
const historyNoteDotClass = computed(() =>
  props.accent === 'rose' ? 'bg-rose-300' : 'bg-primary-300'
)
</script>
