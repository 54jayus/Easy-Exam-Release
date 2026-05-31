import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'

const STORAGE_KEY = 'user_profile'
const DICEBEAR_BG = 'e1f5fe,ffecb3,ffe082,ffcdd2,f8bbd0,e1bee7,d1c4e9,c5cae9,bbdefb,b3e5fc,b2ebf2,b2dfdb,c8e6c9,dcedc8,f0f4c3,fff9c4'

export interface UserProfile {
  name: string
  email: string
  avatarSeed: string
  avatar: string
  customAvatarPath: string
}

function createDefault(): UserProfile {
  return {
    name: '管理员',
    email: '',
    avatarSeed: 'Cali',
    avatar: `https://api.dicebear.com/9.x/notionists/svg?seed=Cali&backgroundColor=${DICEBEAR_BG}`,
    customAvatarPath: ''
  }
}

export function getAvatarUrl(seed: string): string {
  return `https://api.dicebear.com/9.x/notionists/svg?seed=${seed}&backgroundColor=${DICEBEAR_BG}`
}

export const AVATAR_SEEDS = ['Admin', 'Felix', 'Aneka', 'Zack', 'Milo', 'Bandit', 'Tinker', 'Cali', 'Coco', 'Bear']

export const useUserProfileStore = defineStore('userProfile', () => {
  const profile = reactive<UserProfile>(createDefault())

  // 快照：打开设置弹窗时保存，用于 isDirty 判断
  let snapshot = ''

  function load() {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return
    try {
      const data = JSON.parse(saved)
      Object.assign(profile, data)
      if (data.customAvatarPath) {
        profile.avatar = `file:///${data.customAvatarPath.replace(/\\/g, '/')}`
      }
    } catch (e) {
      console.error('Failed to load user profile', e)
    }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile))
  }

  function reset() {
    Object.assign(profile, createDefault())
    localStorage.removeItem(STORAGE_KEY)
  }

  function takeSnapshot() {
    snapshot = JSON.stringify(profile)
  }

  const isDirty = computed(() => {
    return snapshot !== '' && snapshot !== JSON.stringify(profile)
  })

  function selectAvatar(seed: string) {
    profile.avatarSeed = seed
    profile.customAvatarPath = ''
    profile.avatar = getAvatarUrl(seed)
  }

  async function saveCustomAvatar(base64: string): Promise<boolean> {
    try {
      const avatarPath = await (window as any).electron.ipcRenderer.invoke('avatar:save', base64)
      profile.customAvatarPath = avatarPath
      profile.avatar = `file:///${avatarPath.replace(/\\/g, '/')}`
      profile.avatarSeed = ''
      ElMessage.success('自定义头像已保存')
      return true
    } catch {
      ElMessage.error('保存头像失败')
      return false
    }
  }

  function resetAvatar() {
    profile.customAvatarPath = ''
    profile.avatarSeed = 'Cali'
    profile.avatar = getAvatarUrl('Cali')
  }

  const hasCustomAvatar = computed(() => !!profile.customAvatarPath)

  return {
    profile,
    isDirty,
    hasCustomAvatar,
    load,
    save,
    reset,
    takeSnapshot,
    selectAvatar,
    saveCustomAvatar,
    resetAvatar
  }
})
