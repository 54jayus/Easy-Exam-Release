<template>
  <el-dialog
    v-model="visible"
    title="设置头像"
    width="520px"
    align-center
    destroy-on-close
    :close-on-click-modal="false"
    class="avatar-cropper-dialog rounded-2xl"
    @close="handleClose"
  >
    <div class="flex flex-col gap-5">
      <!-- 裁剪区域 + 圆形遮罩 -->
      <div class="relative mx-auto" style="width: 360px; height: 360px">
        <div class="w-full h-full rounded-2xl overflow-hidden bg-slate-900/5">
          <VueCropper
            ref="cropperRef"
            :img="imageSrc"
            :auto-crop="true"
            :fixed="true"
            :fixed-number="[1, 1]"
            :center-box="true"
            :info="false"
            :can-move="true"
            :can-scale="true"
            :output-type="'png'"
            :output-size="200"
            :full="false"
            @realTime="handleRealTime"
          />
        </div>
        <!-- 圆形遮罩：裁剪框外变暗，中间圆形透明 -->
        <div class="absolute inset-0 pointer-events-none rounded-2xl overflow-hidden">
          <div class="w-full h-full" :style="cropMaskStyle" />
        </div>
      </div>

      <!-- 缩放滑块 -->
      <div class="flex items-center gap-3 px-2">
        <el-icon class="text-slate-400 flex-shrink-0"><ZoomOut /></el-icon>
        <el-slider
          v-model="scaleValue"
          :min="100"
          :max="500"
          :step="10"
          :show-tooltip="false"
          class="flex-1"
          @change="handleScaleChange"
        />
        <el-icon class="text-slate-400 flex-shrink-0"><ZoomIn /></el-icon>
      </div>

      <!-- 实时预览 -->
      <div class="flex items-center justify-center gap-6">
        <div class="flex flex-col items-center gap-1.5">
          <div class="text-xs text-slate-400 font-medium">头像预览</div>
          <div class="w-20 h-20 rounded-full overflow-hidden border-2 border-primary-200 shadow-lg shadow-primary-500/10 bg-slate-100">
            <div
              v-if="previewUrl"
              class="w-full h-full bg-cover bg-center"
              :style="{ backgroundImage: `url(${previewUrl})` }"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-slate-300">
              <el-icon :size="28"><Picture /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-between items-center">
        <el-button text @click="handleClose" class="!text-slate-500">
          取消
        </el-button>
        <el-button type="primary" @click="handleConfirm" :loading="saving" class="!rounded-xl !px-6">
          使用此头像
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { VueCropper } from 'vue-cropper'
import { Picture, ZoomIn, ZoomOut } from '@element-plus/icons-vue'
import 'vue-cropper/dist/index.css'

const props = defineProps<{
  modelValue: boolean
  imageSrc: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'crop', data: string): void
}>()

const visible = ref(props.modelValue)
const cropperRef = ref<any>(null)
const previewUrl = ref('')
const scaleValue = ref(200)
const saving = ref(false)

// 圆形遮罩样式 —— 裁剪框外部变暗
const cropMaskStyle = computed(() => {
  // 遮罩使用径向渐变，中心透明（圆形），外部变暗
  return {
    background: 'radial-gradient(circle at center, transparent 48%, rgba(0,0,0,0.45) 48.5%, rgba(0,0,0,0.45) 100%)',
  }
})

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    scaleValue.value = 200
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const handleRealTime = (data: any) => {
  if (data.url) {
    previewUrl.value = data.url
  }
}

const handleScaleChange = (val: number) => {
  if (cropperRef.value) {
    const scale = val / 200
    cropperRef.value.reload()
    nextTick(() => {
      cropperRef.value.changeScale(scale - 1)
    })
  }
}

const handleClose = () => {
  visible.value = false
  previewUrl.value = ''
  saving.value = false
}

const handleConfirm = async () => {
  if (!cropperRef.value || saving.value) return
  saving.value = true
  try {
    await new Promise<void>((resolve) => {
      cropperRef.value.getCropData((data: string) => {
        emit('crop', data)
        resolve()
      })
    })
    handleClose()
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.avatar-cropper-dialog :deep(.el-dialog__body) {
  padding: 20px 24px 16px;
}

:deep(.cropper) {
  width: 100%;
  height: 100%;
}

:deep(.cropper-crop-box) {
  border-radius: 50% !important;
}

:deep(.cropper-view-box) {
  border-radius: 50% !important;
  outline: 2px solid rgba(255, 255, 255, 0.8);
  outline-color: rgba(255, 255, 255, 0.8);
}

:deep(.el-slider__runway) {
  height: 6px;
}

:deep(.el-slider__bar) {
  height: 6px;
  background: linear-gradient(90deg, #6366f1, #818cf8);
}

:deep(.el-slider__button) {
  width: 18px;
  height: 18px;
  border: 2px solid #6366f1;
}
</style>
