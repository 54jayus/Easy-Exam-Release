<template>
  <el-dialog
    :model-value="modelValue"
    title="科目与时间设置"
    width="720px"
    class="!rounded-2xl"
    align-center
    append-to-body
    @update:model-value="handleVisibleChange"
  >
    <div class="flex flex-col h-[520px]">
      <div class="flex items-center justify-between p-1 mb-4 bg-slate-50 border border-slate-100 rounded-xl">
        <div class="flex items-center gap-4 px-3">
          <span class="text-sm font-bold text-slate-600">科目数量</span>
          <el-input-number
            :model-value="subjectDraftCount"
            :min="1"
            :max="20"
            size="small"
            class="!w-32"
            controls-position="right"
            @update:model-value="handleDraftCountChange"
          />
        </div>
        <el-button
          type="primary"
          link
          :loading="syncingSubjects"
          class="!px-4 !py-2 !h-9 hover:!bg-white hover:shadow-sm rounded-lg transition-all"
          @click="$emit('sync-subjects')"
        >
          <el-icon class="mr-1.5"><Notebook /></el-icon>
          从科目设置同步
        </el-button>
      </div>

      <div class="flex-1 rounded-xl border border-slate-200 overflow-hidden bg-white flex flex-col shadow-sm">
        <div class="grid grid-cols-[56px_1fr_0.9fr_1fr_72px] gap-0 bg-slate-50/80 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider backdrop-blur-sm z-10">
          <div class="py-2.5 text-center border-r border-slate-100">序号</div>
          <div class="py-2.5 px-4 border-r border-slate-100">科目名称</div>
          <div class="py-2.5 px-4 border-r border-slate-100">日期</div>
          <div class="py-2.5 px-4 border-r border-slate-100">时间段</div>
          <div class="py-2.5 text-center">操作</div>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar p-0 bg-slate-50/30">
          <transition-group name="list" tag="div" class="space-y-px">
            <div
              v-for="(row, idx) in subjectDraftRows"
              :key="idx"
              class="grid grid-cols-[56px_1fr_0.9fr_1fr_72px] gap-0 items-center bg-white group hover:bg-blue-50/50 transition-colors duration-200"
            >
              <div class="py-2 text-center text-xs font-mono text-slate-400 group-hover:text-primary-500 font-bold border-r border-transparent group-hover:border-blue-100/50">
                {{ String(idx + 1).padStart(2, '0') }}
              </div>
              <div class="p-1.5 border-r border-transparent group-hover:border-blue-100/50">
                <el-input
                  v-model="row.name"
                  placeholder="科目名称"
                  class="!w-full"
                  :class="{ 'font-bold text-slate-700': row.name }"
                >
                  <template #prefix>
                    <el-icon class="text-slate-300 group-hover:text-primary-400 transition-colors"><Reading /></el-icon>
                  </template>
                </el-input>
              </div>
              <div class="p-1.5 border-r border-transparent group-hover:border-blue-100/50">
                <el-input
                  :model-value="getRowDate(row)"
                  placeholder="如：6月8日"
                  class="!w-full"
                  @update:model-value="(value: string) => setRowDate(row, value)"
                >
                  <template #prefix>
                    <el-icon class="text-slate-300 group-hover:text-primary-400 transition-colors"><Calendar /></el-icon>
                  </template>
                </el-input>
              </div>
              <div class="p-1.5 border-r border-transparent group-hover:border-blue-100/50">
                <el-time-picker
                  :model-value="getRowTimeRange(row)"
                  is-range
                  value-format="HH:mm"
                  format="HH:mm"
                  range-separator="-"
                  start-placeholder="开始时间"
                  end-placeholder="结束时间"
                  :prefix-icon="Timer"
                  class="!w-full"
                  @update:model-value="(value: any) => setRowTimeRange(row, value)"
                />
              </div>
              <div class="flex items-center justify-center p-1.5">
                <el-tooltip
                  :content="subjectDraftRows.length <= 1 ? '至少保留 1 个科目' : '移除该科目'"
                  placement="top"
                >
                  <el-button
                    link
                    type="danger"
                    class="!px-2"
                    :disabled="subjectDraftRows.length <= 1"
                    @click="emit('remove-subject', idx)"
                  >
                    移除
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </transition-group>

          <div v-if="subjectDraftRows.length === 0" class="h-full flex flex-col items-center justify-center text-slate-400 py-12">
            <el-icon size="32" class="mb-2 opacity-50"><FolderOpened /></el-icon>
            <span class="text-xs">暂无科目</span>
          </div>
        </div>
      </div>

      <div class="mt-2 flex items-center gap-2 text-[10px] text-slate-400 px-1">
        <el-icon><InfoFilled /></el-icon>
        <span>
          提示：可直接编辑名称、日期和时间段，也可移除单条科目；点击“从科目设置同步”可拉取最新科目安排。
        </span>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleVisibleChange(false)">取消</el-button>
        <el-button type="primary" @click="$emit('save-subjects')">保存设置</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { Calendar, FolderOpened, InfoFilled, Notebook, Reading, Timer } from '@element-plus/icons-vue'

type SubjectDraftRow = {
  name: string
  time: string
  [key: string]: any
}

defineProps<{
  modelValue: boolean
  subjectDraftCount: number
  syncingSubjects: boolean
  subjectDraftRows: SubjectDraftRow[]
  getRowDate: (row: SubjectDraftRow) => string
  setRowDate: (row: SubjectDraftRow, value: string) => void
  getRowTimeRange: (row: SubjectDraftRow) => any
  setRowTimeRange: (row: SubjectDraftRow, value: any) => void
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'update:subjectDraftCount': [value: number]
  'sync-subjects': []
  'remove-subject': [index: number]
  'save-subjects': []
}>()

function handleVisibleChange(value: boolean) {
  emit('update:modelValue', value)
}

function handleDraftCountChange(value: number | undefined) {
  emit('update:subjectDraftCount', Number(value ?? 1))
}
</script>
