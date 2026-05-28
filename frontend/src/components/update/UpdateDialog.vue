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
          link
          class="!text-slate-400 !text-xs"
          @click="skipCurrentVersion()"
        >
          忽略此版本
        </el-button>
        <el-button
          v-if="updateStatus === 'available'"
          link
          class="!text-slate-400 !text-xs"
          @click="remindLater()"
        >
          稍后提醒
        </el-button>
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
import { inject } from 'vue'
import UpdateDetailsContent from './UpdateDetailsContent.vue'
import { UPDATE_DISPLAY_INJECTION_KEY } from '@/composables/useUpdateDisplayContext'

const ctx = inject(UPDATE_DISPLAY_INJECTION_KEY)!
const updateStatus = ctx.updateStatus
const skipCurrentVersion = ctx.skipCurrentVersion
const remindLater = ctx.remindLater

defineProps<{
  modelValue: boolean
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
</script>
