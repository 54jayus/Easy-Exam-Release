<template>
  <div
    class="flex flex-col border-r border-slate-200/80 bg-white/80 backdrop-blur-xl transition-all duration-300 relative z-20 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.1)]"
    :class="collapsed ? 'w-0 opacity-0 overflow-hidden' : 'w-[280px] opacity-100'"
  >
    <div class="h-14 px-4 border-b border-slate-100/80 flex items-center justify-between shrink-0 bg-gradient-to-b from-white to-slate-50/50">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-200">
          <el-icon :size="16"><Setting /></el-icon>
        </div>
        <span class="font-bold text-slate-800 text-base tracking-tight">考场配置</span>
      </div>
      <div class="flex items-center gap-1">
        <el-tooltip content="初始化当前页面（清除所有考场数据与设置）" placement="bottom">
          <el-button link class="!text-slate-400 hover:!text-rose-600 transition-colors" @click="$emit('reset')">
            <el-icon><Delete /></el-icon>
            <span class="text-xs">初始化</span>
          </el-button>
        </el-tooltip>
        <el-button link class="!text-slate-400 hover:!text-slate-600 transition-colors" @click="$emit('update:collapsed', true)">
          <el-icon><Fold /></el-icon>
          <span class="text-xs">收起</span>
        </el-button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-8">

      <!-- 1. Templates -->
      <section class="space-y-3">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-1 h-3 bg-blue-500 rounded-full"></div>
          <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">模板下载</span>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <SidebarActionButton
            label="考场模板"
            :icon="Download"
            tone="blue"
            tooltip="下载考场设置 Excel 模板，填写考场编号和人数"
            @click="$emit('generate-template', 'settings')"
          />

          <el-dropdown trigger="click" @command="(cmd: string) => $emit('generate-template', cmd)" class="w-full">
            <SidebarActionButton
              label="考生模板"
              :icon="Download"
              tone="blue"
            >
              <template #suffix>
                <el-icon class="text-[10px] text-slate-400 transition-colors group-hover:text-blue-500"><ArrowDown /></el-icon>
              </template>
            </SidebarActionButton>
            <template #dropdown>
              <el-dropdown-menu class="w-[240px]">
                <el-dropdown-item command="student_normal">
                  <div class="flex flex-col py-1">
                    <span class="font-bold">通用版 (普通)</span>
                    <span class="text-xs text-slate-400">适用于常规考试</span>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item command="student_subject">
                  <div class="flex flex-col py-1">
                    <span class="font-bold">新高考版 (3+1+2)</span>
                    <span class="text-xs text-slate-400">包含选科组合信息</span>
                  </div>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </section>

      <!-- 2. Data Import -->
      <section class="space-y-3">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <div class="w-1 h-3 bg-emerald-500 rounded-full"></div>
            <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">数据导入</span>
          </div>
          <div class="px-2 py-0.5 rounded text-[10px] font-bold transition-colors"
               :class="hasStudents ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-400'">
            {{ hasStudents ? `${studentsCount} 人` : '未导入' }}
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <SidebarActionButton
            label="考场导入"
            :icon="Upload"
            tone="emerald"
            tooltip="从已填写的 Excel 文件导入考场设置"
            :active="hasSettings"
            clearable
            @click="$emit('import-settings')"
            @clear="$emit('clear-settings')"
          />
          <SidebarActionButton
            label="考生导入"
            :icon="Upload"
            tone="emerald"
            tooltip="从已填写的 Excel 文件导入考生名册"
            :active="hasStudents"
            clearable
            @click="$emit('import-students')"
            @clear="$emit('clear-students')"
          />
        </div>
      </section>

      <!-- 3. Parameters -->
      <section class="space-y-4">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-1 h-3 bg-indigo-500 rounded-full"></div>
          <span class="text-xs font-bold text-slate-800 uppercase tracking-wider">编排参数</span>
        </div>

        <div class="bg-slate-50/50 rounded-xl p-3 border border-slate-100 space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1.5">
              <div class="text-[10px] font-bold text-slate-400 uppercase">考场数量</div>
              <el-input-number
                :model-value="config.totalRooms"
                @update:model-value="$emit('update:totalRooms', $event)"
                :min="1" :max="200"
                size="small"
                class="!w-full shadow-sm input-number-fixed-height"
                controls-position="right"
              />
            </div>
            <div class="space-y-1.5">
              <div class="text-[10px] font-bold text-slate-400 uppercase">每场人数</div>
              <el-tooltip
                v-if="!seatsPerRoomInfo.isUniform"
                :content="`考场人数不一致，范围：${seatsPerRoomInfo.min}-${seatsPerRoomInfo.max}人`"
                placement="top"
              >
                <div class="h-[32px] px-3 bg-slate-100 border border-slate-200 rounded-lg flex items-center justify-center text-sm text-slate-500 cursor-not-allowed shadow-sm">
                  {{ seatsPerRoomInfo.displayText }}人
                </div>
              </el-tooltip>
              <el-input-number
                v-else
                :model-value="config.seatsPerRoom"
                @update:model-value="$emit('update:seatsPerRoom', $event)"
                :min="1" :max="100"
                size="small"
                class="!w-full shadow-sm input-number-fixed-height"
                controls-position="right"
              />
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-[10px] font-bold text-slate-400 uppercase">编排模式</label>
            <el-select
              :model-value="config.mode"
              @update:model-value="$emit('update:mode', $event)"
              size="default"
              class="w-full shadow-sm"
            >
              <el-option label="3+1+2选科编排" value="3+1+2">
                <div class="flex items-center w-full">
                  <span class="truncate">3+1+2选科编排</span>
                  <el-button class="ml-auto -mr-5" link type="primary" size="small" @click.stop="$emit('open-priority-dialog')">高级设置</el-button>
                </div>
              </el-option>
              <el-option label="高考模式" value="gaokao">
                <div class="flex items-center w-full">
                  <span class="truncate">高考模式</span>
                  <el-button
                    class="ml-auto -mr-5"
                    link
                    type="primary"
                    size="small"
                    @click.stop="$emit('open-gaokao-time-dialog')"
                  >
                    高级设置
                  </el-button>
                </div>
              </el-option>
              <el-option label="顺序编排" value="normal" />
              <el-option label="随机编排" value="random" />
            </el-select>
          </div>
          <button class="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 text-left transition hover:border-blue-300 hover:bg-blue-50/40" @click="$emit('open-seat-layout-dialog')">
            <div>
              <div class="text-xs font-bold text-slate-700">座位布局</div>
              <div class="mt-0.5 text-[10px] text-slate-400">{{ config.seatLayout.defaultLayout.layoutName }} · {{ config.seatLayout.defaultLayout.layoutPattern }}</div>
            </div>
            <span class="text-xs font-bold text-blue-600">设置</span>
          </button>
        </div>
      </section>

      <!-- 4. Actions -->
      <section class="pt-4 mt-auto space-y-2">
        <el-button
          type="primary"
          size="default"
          class="!w-full !h-10 !text-sm !font-bold !rounded-lg shadow-lg shadow-blue-200 hover:shadow-blue-300 transition-all hover:-translate-y-0.5"
          :disabled="!canArrange"
          @click="$emit('arrange')"
        >
          智能编排
        </el-button>
        <div class="grid grid-cols-2 gap-2">
          <el-button
            plain
            size="default"
            class="!w-full !h-10 !rounded-lg border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-200"
            @click="$emit('import-results')"
          >
            <el-icon class="mr-1.5"><Upload /></el-icon> 导入结果
          </el-button>
          <el-button
            plain
            size="default"
            class="!w-full !h-10 !rounded-lg border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-200"
            :disabled="!hasResults"
            :loading="isExporting"
            @click="$emit('export')"
          >
            <el-icon v-if="!isExporting" class="mr-1.5"><Download /></el-icon> 导出结果
          </el-button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Setting, ArrowDown, Upload, Download, Fold, Delete } from '@element-plus/icons-vue'
import SidebarActionButton from '@/components/SidebarActionButton.vue'
import type { RoomsConfig } from './composables/useRoomsState'

interface Props {
  collapsed: boolean
  config: RoomsConfig
  hasSettings: boolean
  hasStudents: boolean
  hasResults: boolean
  canArrange: boolean
  studentsCount: number
  isExporting?: boolean
  seatsPerRoomInfo: {
    isUniform: boolean
    value: number
    min: number
    max: number
    displayText: string
  }
}

defineProps<Props>()

defineEmits<{
  'update:collapsed': [value: boolean]
  'update:config': [value: RoomsConfig]
  'update:mode': [value: string]
  'update:totalRooms': [value: number]
  'update:seatsPerRoom': [value: number]
  'generate-template': [type: string]
  'import-settings': []
  'import-students': []
  'import-results': []
  'clear-settings': []
  'clear-students': []
  'arrange': []
  'export': []
  'reset': []
  'open-priority-dialog': []
  'open-gaokao-time-dialog': []
  'open-seat-layout-dialog': []
}>()
</script>

<style scoped>
/* 确保两个输入框高度一致 */
.input-number-fixed-height :deep(.el-input-number) {
  height: 32px;
}

.input-number-fixed-height :deep(.el-input__wrapper) {
  height: 32px;
  box-sizing: border-box;
}

.input-number-fixed-height :deep(.el-input__inner) {
  height: 30px;
  line-height: 30px;
}

/* 去掉上下箭头中间的空隙 */
.input-number-fixed-height :deep(.el-input-number__increase),
.input-number-fixed-height :deep(.el-input-number__decrease) {
  height: 16px;
  line-height: 16px;
}

.input-number-fixed-height :deep(.el-input-number__increase) {
  border-bottom: none;
}

.input-number-fixed-height :deep(.el-input-number__decrease) {
  border-top: 1px solid var(--el-input-border-color);
}
</style>
