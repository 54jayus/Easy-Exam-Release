<template>
  <el-dialog
    v-model="visible"
    title="个人资料"
    width="480px"
    align-center
    class="rounded-2xl"
    @open="handleOpen"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      class="flex flex-col gap-6"
    >
      <!-- 头像选择区 -->
      <div class="flex flex-col gap-3">
        <label class="text-sm font-bold text-slate-700 flex items-center gap-2">
          <el-icon><User /></el-icon> 头像
        </label>

        <!-- 预设头像网格 -->
        <div class="grid grid-cols-5 gap-2.5">
          <div
            v-for="seed in AVATAR_SEEDS"
            :key="seed"
            class="relative group"
          >
            <el-tooltip :content="seed" placement="top" :show-after="300">
              <div
                class="aspect-square rounded-full cursor-pointer transition-all duration-200 overflow-hidden border-2"
                :class="form.avatarSeed === seed
                  ? 'border-primary-500 ring-2 ring-primary-200'
                  : 'border-slate-200 hover:border-primary-300 hover:scale-105'"
                @click="handleSelectPreset(seed)"
              >
                <img :src="getAvatarUrl(seed)" class="w-full h-full bg-slate-50" />
              </div>
            </el-tooltip>
            <!-- 选中角标 -->
            <div
              v-if="form.avatarSeed === seed"
              class="absolute -bottom-0.5 -right-0.5 w-5 h-5 bg-primary-500 rounded-full flex items-center justify-center ring-2 ring-white"
            >
              <el-icon class="text-white" :size="10"><Check /></el-icon>
            </div>
          </div>
        </div>

        <!-- 自定义头像上传 -->
        <div
          class="flex items-center gap-3 p-3 border-2 border-dashed rounded-xl cursor-pointer transition-colors"
          :class="store.hasCustomAvatar
            ? 'border-primary-200 bg-primary-50/50 hover:border-primary-300'
            : 'border-slate-200 hover:border-primary-300 hover:bg-slate-50'"
          @click="handleUpload"
        >
          <div class="w-10 h-10 rounded-full overflow-hidden bg-slate-100 flex-shrink-0 flex items-center justify-center">
            <img v-if="store.hasCustomAvatar" :src="form.avatar" class="w-full h-full object-cover" />
            <el-icon v-else class="text-slate-400" :size="20"><Upload /></el-icon>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-slate-700">
              {{ store.hasCustomAvatar ? '更换自定义头像' : '上传自定义头像' }}
            </p>
            <p class="text-xs text-slate-400">支持 JPG、PNG、GIF、WebP，最大 10MB</p>
          </div>
          <el-button
            v-if="store.hasCustomAvatar"
            text
            size="small"
            class="!text-slate-400 !text-xs flex-shrink-0"
            @click.stop="handleReset"
          >
            恢复默认
          </el-button>
        </div>
      </div>

      <!-- 分割线 -->
      <div class="border-t border-slate-100"></div>

      <!-- 基本信息 -->
      <div class="flex flex-col gap-4">
        <el-form-item label="用户名" prop="name" class="!mb-0">
          <el-input
            v-model="form.name"
            placeholder="请输入用户名"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="工作邮箱" prop="email" class="!mb-0">
          <el-input
            v-model="form.email"
            placeholder="请输入工作邮箱（选填）"
          />
        </el-form-item>
      </div>
    </el-form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存更改
        </el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 头像裁剪 -->
  <AvatarCropper
    v-model="showCropper"
    :image-src="cropperImageSrc"
    @crop="handleCrop"
  />
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Check, Upload, User } from '@element-plus/icons-vue'
import { useUserProfileStore, getAvatarUrl, AVATAR_SEEDS } from '@/stores/userProfile'
import { open } from '@/lib/dialog'
import AvatarCropper from './AvatarCropper.vue'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const store = useUserProfileStore()
const formRef = ref<FormInstance>()
const saving = ref(false)
const showCropper = ref(false)
const cropperImageSrc = ref('')

const visible = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 表单数据（副本，不直接修改 store）
const form = reactive({
  name: '',
  email: '',
  avatarSeed: '',
  avatar: '',
  customAvatarPath: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 1, max: 20, message: '用户名不超过 20 个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

function syncFormFromStore() {
  form.name = store.profile.name
  form.email = store.profile.email
  form.avatarSeed = store.profile.avatarSeed
  form.avatar = store.profile.avatar
  form.customAvatarPath = store.profile.customAvatarPath
}

function syncStoreFromForm() {
  store.profile.name = form.name.trim()
  store.profile.email = form.email.trim()
  // 头像相关已在 selectAvatar / saveCustomAvatar / resetAvatar 中直接操作 store
}

function handleOpen() {
  syncFormFromStore()
  store.takeSnapshot()
}

async function handleClose() {
  if (store.isDirty) {
    try {
      await ElMessageBox.confirm('你有未保存的更改，是否保存？', '提示', {
        confirmButtonText: '保存',
        cancelButtonText: '不保存',
        type: 'warning'
      })
      // 用户选择保存
      await handleSave()
    } catch {
      // 用户选择"不保存"或关闭对话框
      syncFormFromStore() // 还原表单
    }
  }
}

function handleSelectPreset(seed: string) {
  store.selectAvatar(seed)
  form.avatarSeed = seed
  form.avatar = store.profile.avatar
  form.customAvatarPath = ''
}

async function handleUpload() {
  const filePath = await open({
    title: '选择头像图片',
    filters: [
      { name: '图片文件', extensions: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'] }
    ]
  })
  if (!filePath || Array.isArray(filePath)) return

  const ext = filePath.split('.').pop()?.toLowerCase()
  if (!ext || !['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)) {
    ElMessage.error('请选择有效的图片文件')
    return
  }

  try {
    const base64 = await (window as any).electron.ipcRenderer.invoke('fs:readFile', filePath)
    cropperImageSrc.value = base64
    showCropper.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '读取图片失败')
  }
}

async function handleCrop(data: string) {
  const ok = await store.saveCustomAvatar(data)
  if (ok) {
    syncFormFromStore()
  }
}

function handleReset() {
  store.resetAvatar()
  syncFormFromStore()
}

async function handleSave() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    syncStoreFromForm()
    store.save()
    store.takeSnapshot()
    visible.value = false
    ElMessage.success('个人资料已保存')
  } finally {
    saving.value = false
  }
}
</script>
