<template>
  <div class="h-full w-full flex items-center justify-center relative overflow-hidden bg-slate-50">
    <!-- Background Decorations -->
    <div class="absolute inset-0 bg-grid-slate-200/[0.04] bg-[length:32px_32px]"></div>
    <div class="absolute top-0 right-0 w-[500px] h-[500px] bg-primary-100/50 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none mix-blend-multiply opacity-70"></div>
    <div class="absolute bottom-0 left-0 w-[500px] h-[500px] bg-indigo-100/50 rounded-full blur-3xl -ml-32 -mb-32 pointer-events-none mix-blend-multiply opacity-70"></div>

    <div class="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10 items-stretch px-6">
      
      <!-- Left Column: Value Proposition -->
      <div class="flex flex-col justify-center space-y-8 pr-8">
        <div>
          <h1 class="text-4xl font-extrabold text-slate-900 tracking-tight mb-3">
            解锁<span class="text-primary-600">专业版</span>功能
          </h1>
          <p class="text-lg text-slate-500 leading-relaxed">
            激活软件以使用体验，提升考务管理效率。
          </p>
        </div>

        <!-- Status Card -->
        <div class="bg-white/60 backdrop-blur-md p-6 rounded-2xl border border-white/50 shadow-sm">
          <div class="flex items-center gap-4">
            <div :class="`p-3 rounded-xl ${licenseStatus.valid ? 'bg-emerald-100 text-emerald-600' : 'bg-orange-100 text-orange-600'}`">
              <el-icon :size="24"><Monitor /></el-icon>
            </div>
            <div>
              <div class="text-xs text-slate-500 font-bold uppercase tracking-wider mb-0.5">当前状态</div>
              <div class="text-base font-bold text-slate-800 flex items-center gap-2 whitespace-pre-wrap">
                {{ licenseStatus.message }}
                <span v-if="licenseStatus.valid" class="text-xs px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full">Pro</span>
              </div>
            </div>
          </div>
          <div v-if="licenseStatus.valid" class="mt-4 pt-4 border-t border-slate-200/60 flex items-center gap-2 text-sm text-slate-600">
            <el-icon class="text-emerald-500"><Calendar /></el-icon>
            有效期至：<span class="font-mono font-medium">{{ licenseStatus.expireDate }}</span>
            <span class="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full ml-auto">剩余 {{ licenseStatus.daysLeft }} 天</span>
          </div>
        </div>

        <!-- Features List -->
        <div class="space-y-4">
          <div v-for="(feature, index) in features" :key="index" class="flex items-center gap-3 group">
            <div class="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center group-hover:bg-primary-600 group-hover:text-white transition-colors duration-300">
              <el-icon :size="14"><Check /></el-icon>
            </div>
            <span class="text-slate-700 font-medium">{{ feature }}</span>
          </div>
        </div>

        <!-- Developer Contact / Social -->
        <div class="mt-auto pt-8">
          <div class="flex items-center gap-4 p-4 bg-slate-100/50 rounded-2xl border border-slate-200/60 hover:bg-white hover:shadow-md transition-all duration-300 cursor-pointer group" @click="openSocialLink">
            <!-- Avatar Placeholder -->
            <div class="w-12 h-12 rounded-full bg-gradient-to-br from-red-500 to-pink-500 p-0.5 shadow-sm group-hover:scale-105 transition-transform">
              <div class="w-full h-full rounded-full bg-white flex items-center justify-center overflow-hidden">
                <img src="/images/xhs_avater.jpg" alt="Avatar" class="w-full h-full object-cover" />
              </div>
            </div>
            
            <div class="flex-1">
              <div class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-0.5">关注开发者</div>
              <div class="font-bold text-slate-800 flex items-center gap-2">
                <span>小红书主页</span>
                <el-icon :size="14" class="text-slate-400 group-hover:text-red-500 transition-colors"><TopRight /></el-icon>
              </div>
            </div>

            <!-- Xiaohongshu Logo SVG -->
            <div class="w-8 h-8 text-slate-300 group-hover:text-red-500 transition-colors">
              <svg t="1769171918166" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="4858" width="100%" height="100%"><path d="M1021.72444445 836.54883555V187.48757333C1021.72444445 85.61550222 938.38449778 2.27555555 836.51242667 2.27555555H187.48757333C85.61550222 2.27555555 2.27555555 85.61550222 2.27555555 187.48757333v649.06126222c0 100.85262222 81.70154667 183.57361778 182.2264889 185.1756089h654.9959111c100.48853333-1.60199111 182.22648889-84.28657778 182.2264889-185.1756089" fill="#FF2442" p-id="4859"></path><path d="M726.52117333 366.36444445h57.344v20.53461333c0 1.6384 0.80099555 2.40298667 2.36657778 2.36657777 34.00590222-1.01944889 68.26666667 0.07281778 85.81575111 34.95253334 10.44935111 20.68024889 8.30122667 52.13752889 7.71868445 76.82275556-0.03640889 1.45635555 0.65536 2.25735111 2.03889778 2.40298666 4.00497778 0.36408889 7.90072889 0.72817778 11.68725333 1.20149334 67.61130667 8.11918222 54.24924445 71.87114667 54.46769777 121.96977777 0.10922667 17.47626667-1.85685333 30.25578667-5.82542222 38.41137778-8.37404445 16.89372445-23.37450667 26.57848889-45.00138666 28.98147555H854.97173333l-21.55406222-50.02581333a1.6384 1.6384 0 0 1 0.10922667-1.52917333 1.56558222 1.56558222 0 0 1 1.31072-0.72817778l45.72956444-0.03640889c2.54862222 0 4.95160889-1.09226667 6.69923556-2.98552889a10.12167111 10.12167111 0 0 0 2.69425777-7.02691555c-0.21845333-15.29173333-0.32768-30.54705778-0.25486222-45.80238223 0-13.72615111-6.48078222-20.75306667-19.55157333-21.11715555-14.78200889-0.36408889-42.78044445-0.36408889-84.03171555 0.07281778-1.45635555 0-2.18453333 0.80099555-2.18453334 2.36657777l-0.21845333 126.81216H726.44835555l-0.18204444-127.35829333a2.25735111 2.25735111 0 0 0-2.22094222-2.33016889h-53.52106667a2.54862222 2.54862222 0 0 1-2.47580444-2.54862222l0.07281777-55.41432889c0-1.85685333 0.87381333-2.80348445 2.62144-2.80348444l52.90211556 0.10922667a2.51221333 2.51221333 0 0 0 1.82044444-0.80099556 2.76707555 2.76707555 0 0 0 0.72817778-1.89326222v-47.91409778a3.16757333 3.16757333 0 0 0-3.05834666-3.24039111l-32.65877334 0.14563555c-1.71121778 0-2.54862222-0.91022222-2.54862222-2.69425778l-0.10922666-55.7056c0-1.6384 0.72817778-2.43939555 2.36657777-2.43939555h33.82385778c1.45635555 0 2.18453333-0.72817778 2.18453333-2.29376l0.36408889-20.46179555z m59.38289778 137.37073777l35.57148444-0.07281777c0.58254222 0 1.12867555-0.25486222 1.52917334-0.6917689a2.29376 2.29376 0 0 0 0.61895111-1.6019911l-0.18204445-44.52807112c0-3.49525333-2.54862222-6.33514667-5.64337777-6.33514666l-28.54456889 0.07281778a5.35210667 5.35210667 0 0 0-4.00497778 1.89326222 6.80846222 6.80846222 0 0 0-1.6384 4.55111111l0.18204444 44.52807111c0 1.23790222 0.98304 2.18453333 2.11171556 2.18453333zM417.95584 507.74016c-13.83537778 0.25486222-38.84828445 4.11420445-44.30961778-13.68974222-3.31320889-10.63139555 4.18702222-25.44981333 8.73813333-35.82634667 12.96156445-29.52760889 25.66826667-59.16444445 38.15651556-88.91050666 0.50972445-1.20149333 1.38353778-1.82044445 2.62144-1.82044445h54.72256c0.47331555 0 0.87381333 0.25486222 1.09226667 0.65536a1.45635555 1.45635555 0 0 1 0.14563555 1.31072l-31.67573333 74.01927111c-0.72817778 1.71121778-0.54613333 3.64088889 0.40049778 5.24288a5.17006222 5.17006222 0 0 0 4.36906667 2.47580444h46.89464888c0.58254222 0 1.09226667 0.29127111 1.41994667 0.76458667 0.29127111 0.50972445 0.36408889 1.09226667 0.10922667 1.6384-13.54410667 31.56650667-27.05180445 62.91456-40.52309334 94.04416-1.34712889 3.09475555-1.92967111 5.38851555-1.71121778 6.84487111 0.47331555 3.16757333 2.25735111 4.76956445 5.31569778 4.80597334l29.67324445 0.18204444c1.71121778 0.03640889 2.25735111 0.87381333 1.56558222 2.54862222l-19.18748445 45.14702222a3.78652445 3.78652445 0 0 1-3.64088888 2.51221334c-30.14656 0.36408889-51.22730667 0.36408889-63.24224-0.18204444-19.87925333-0.91022222-24.75804445-18.31367111-17.03936-36.26325334l27.27025778-63.64273778a1.38353778 1.38353778 0 0 0-0.10922667-1.23790222 1.23790222 1.23790222 0 0 0-1.09226667-0.61895111zM190.58232889 694.00803555h-21.48124444l-21.04433778-49.40686222a1.60199111 1.60199111 0 0 1 0.10922666-1.49276444 1.45635555 1.45635555 0 0 1 1.23790222-0.72817778l29.70965334-0.07281778a6.95409778 6.95409778 0 0 0 6.80846222-7.09973333l0.80099556-262.03477333a2.54862222 2.54862222 0 0 1 2.51221333-2.62144h51.11808c2.40298667 0 3.60448 1.27431111 3.64088889 3.78652444 0.21845333 88.72846222 0.21845333 175.92775111 0 261.63427556-0.14563555 35.17098667-16.45681778 59.20085333-53.41184 58.03576888z" fill="#FFFFFF" p-id="4860"></path><path d="M670.08739555 694.00803555h-193.91374222l25.99594667-58.6183111a3.45884445 3.45884445 0 0 1 3.38602667-2.22094223l47.47719111 0.07281778c1.67480889 0 2.54862222-0.83740445 2.54862222-2.54862222v-177.85742223c0-1.52917333-0.72817778-2.29376-2.18453333-2.29376l-31.49368889-0.03640888c-1.41994667 0-2.54862222-1.23790222-2.54862223-2.73066667v-57.05272889c0-0.87381333 0.65536-1.60199111 1.49276445-1.60199111h128.37774222c1.60199111 0 2.36657778 0.83740445 2.36657778 2.51221333l0.07281778 56.43377778c0 1.6384-0.80099555 2.47580445-2.40298667 2.47580444h-31.74855111c-1.45635555 0-2.18453333 0.76458667-2.18453333 2.29376v177.74819556c0 1.71121778 0.83740445 2.54862222 2.43939555 2.54862222l50.31708445 0.10922667c1.38353778 0 2.07530667 0.72817778 2.07530666 2.18453333L670.08739555 694.04444445zM901.02897778 394.65415111c39.61287111-27.23384889 67.50208 42.19790222 24.10268444 54.10360889-7.06332445 1.96608-18.31367111 2.07530667-33.71463111 0.36408889-1.38353778-0.14563555-2.03889778-0.91022222-2.03889778-2.36657778-0.21845333-16.384-3.45884445-41.72458667 11.65084445-52.06471111zM354.20387555 598.79879111l-26.2144 61.05770667c-2.36657778 5.46133333-4.95160889 5.57056-7.8279111 0.43690667-19.29671111-34.87971555-25.85031111-63.35146667-29.63683556-106.71445334-2.91271111-33.67822222-5.42492445-67.35644445-7.60945778-101.10748444-0.07281778-1.52917333 0.61895111-2.29376 2.07530667-2.29376l53.12056889 0.03640888c1.49276445 0 2.33016889 0.80099555 2.43939555 2.3301689 2.73066667 39.24878222 5.60696889 78.38833778 8.59249778 117.41866666 0.76458667 10.04885333 2.47580445 18.38648889 5.09724445 25.01290667a4.73315555 4.73315555 0 0 1-0.0364089 3.82293333zM75.09333333 596.54144v-2.51221333a25.70467555 25.70467555 0 0 0 4.73315556-11.50520889c3.93216-43.32657778 7.13614222-86.61674667 9.64835556-129.94332445 0.10922667-1.34712889 0.76458667-2.03889778 2.03889777-2.03889778h54.24924445c0.47331555 0 0.94663111 0.21845333 1.31072 0.61895112 0.32768 0.36408889 0.50972445 0.87381333 0.47331555 1.38353778a7226.07217778 7226.07217778 0 0 1-9.57553777 119.67601777c-2.54862222 28.94506667-11.79648 67.68412445-31.1296 91.16785778-1.23790222 1.49276445-2.29376 1.34712889-3.09475556-0.47331555L75.09333333 596.54144zM445.08046222 694.00803555h-78.57038222l-10.01244445-3.96856888c-1.41994667-0.54613333-1.82044445-1.52917333-1.16508444-2.94912l24.64881778-56.43377778c0.72817778-1.6384 1.89326222-2.25735111 3.56807111-1.82044444 26.94257778 7.31818667 58.14499555 4.29624889 85.70652445 4.40547555 1.71121778 0.03640889 2.18453333 0.87381333 1.45635555 2.47580445l-25.63185778 58.25422222z" fill="#FFFFFF" p-id="4861"></path></svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Activation Workflow -->
      <div class="bg-white/80 backdrop-blur-xl p-8 rounded-3xl border border-white/40 shadow-xl flex flex-col relative overflow-hidden">
        <!-- Decoration -->
        <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary-500/10 to-transparent rounded-bl-full -mr-8 -mt-8 pointer-events-none"></div>

        <h2 class="text-xl font-bold text-slate-900 mb-8 flex items-center gap-2">
          <span class="w-1 h-6 bg-primary-500 rounded-full block"></span>
          软件激活
        </h2>

        <div class="space-y-8 flex-1">
          <!-- Step 1: Machine Code -->
          <div class="relative">
            <div class="absolute -left-3 -top-3 w-8 h-8 bg-slate-900 text-white rounded-lg flex items-center justify-center text-sm font-bold shadow-md z-10 border-2 border-white">1</div>
            <div class="bg-slate-50 border-2 border-dashed border-slate-300 rounded-2xl p-5 pt-6 hover:border-primary-300 transition-colors group">
              <div class="flex justify-between items-center mb-2">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">机器特征码</span>
                <span class="text-xs text-primary-600 bg-primary-50 px-2 py-0.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">点击复制</span>
              </div>
              <div class="flex items-center gap-3">
                <code class="flex-1 font-mono text-lg text-slate-700 font-bold tracking-wider select-all truncate" @click="copyMachineCode" title="点击复制">{{ machineCode }}</code>
                <el-button circle type="primary" plain @click="copyMachineCode">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </div>
            </div>
            <p class="text-xs text-slate-400 mt-2 pl-2">请将此代码发送给管理员以获取注册码</p>
          </div>

          <!-- Step 2: License Key -->
          <div class="relative">
            <div class="absolute -left-3 -top-3 w-8 h-8 bg-slate-900 text-white rounded-lg flex items-center justify-center text-sm font-bold shadow-md z-10 border-2 border-white">2</div>
            <div class="bg-white border border-slate-200 rounded-2xl p-5 pt-6 shadow-sm">
              <label class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">输入注册码</label>
              <el-input 
                v-model="registrationCodeDisplay" 
                placeholder="在此粘贴 16 位注册码" 
                size="large"
                class="custom-input font-mono text-lg"
                :clearable="!licenseStatus.valid || isEditingRegistrationCode"
                @focus="handleRegistrationCodeFocus"
                @blur="handleRegistrationCodeBlur"
              >
              </el-input>
              
              
              <el-button 
                type="primary" 
                size="large" 
                class="w-full !rounded-xl !h-12 !text-base !mt-6 shadow-lg shadow-primary-500/20 hover:shadow-primary-500/30 hover:-translate-y-0.5 transition-all duration-300"
                :loading="isValidating"
                @click="handleRegister"
              >
                立即激活
              </el-button>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="mt-8 pt-6 border-t border-slate-100 text-center">
          <el-button link type="info" size="small" @click="$router.push('/help')" class="!text-slate-400 hover:!text-primary-600">
            遇到问题？联系技术支持
          </el-button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useClipboard } from '@vueuse/core'
import { ElMessage } from 'element-plus'
import { 
  Monitor, Calendar, CopyDocument, Check, User, TopRight
} from '@element-plus/icons-vue'
import { pythonBackend } from '../lib/pythonBackend'
import { useLicenseStore } from '../stores/license'

const licenseStore = useLicenseStore()

// WeChat QR Code
const wechatDialogVisible = ref(false)
const showWechatQr = () => {
  wechatDialogVisible.value = true
}

// Social Link
const openSocialLink = () => {
  // Replace with your actual Xiaohongshu profile URL
  const profileUrl = 'https://xhslink.com/m/4KXDLPPFipy'
  
  // Use Electron's shell to open external URL
  if ((window as any).electron && (window as any).electron.ipcRenderer) {
    (window as any).electron.ipcRenderer.invoke('open_external', profileUrl)
  } else {
    // Fallback for browser dev mode
    window.open(profileUrl, '_blank')
  }
}

// Features List
const features = [
  '智能排考：一键自动安排考场与监考',
  '数据导出：支持 Excel/PDF 格式导出',
  '灵活设置：自定义规则满足多样化需求',
  '优先支持：专属技术支持服务'
]

// Machine Code & License State
const machineCode = ref('Loading...')
const { copy, copied, isSupported } = useClipboard({ source: machineCode })
const licenseStatus = computed(() => licenseStore.status)

const copyMachineCode = async () => {
  if (!isSupported.value) {
    ElMessage.error('当前环境不支持复制到剪贴板')
    return
  }
  try {
    await copy(machineCode.value) // Explicitly pass the value to copy
    ElMessage.success('机器码已复制到剪贴板')
  } catch (e: any) {
    ElMessage.error(`复制失败: ${e?.message || '未知错误'}`)
  }
}

// Fetch Data on Mount
onMounted(async () => {
  try {
    // Only fetch machine code - license status already in store from router guard
    const resCode = await pythonBackend.request<any>('licensing.machineCode', {})
    if (resCode && resCode.machineCode) {
      machineCode.value = resCode.machineCode
    }
  } catch (e) {
    console.error("读取机器码失败", e)
    ElMessage.error('无法连接后端服务')
  }
})

// Registration Logic
const registrationCode = ref('')
const isEditingRegistrationCode = ref(false)
const REGISTRATION_CODE_LEN_STORAGE_KEY = 'license_registration_code_len_v1'
const _getStoredRegistrationCodeLen = (): number => {
  try {
    const raw = localStorage.getItem(REGISTRATION_CODE_LEN_STORAGE_KEY)
    const n = raw ? Number(raw) : NaN
    if (Number.isFinite(n) && n > 0) return n
  } catch {}
  return 16
}
const lastRegistrationCodeLen = ref<number>(_getStoredRegistrationCodeLen())

const handleRegistrationCodeFocus = () => {
  if (!licenseStatus.value.valid) return
  isEditingRegistrationCode.value = true
  registrationCode.value = ''
}

const handleRegistrationCodeBlur = () => {
  if (!licenseStatus.value.valid) return
  if (!registrationCode.value.trim()) {
    isEditingRegistrationCode.value = false
  }
}

const registrationCodeDisplay = computed({
  get() {
    if (licenseStatus.value.valid && !isEditingRegistrationCode.value) {
      return '*'.repeat(Math.max(0, lastRegistrationCodeLen.value))
    }
    return registrationCode.value
  },
  set(v: string) {
    if (licenseStatus.value.valid && !isEditingRegistrationCode.value) return
    registrationCode.value = v
    const n = String(v || '').length
    if (n > 0) {
      lastRegistrationCodeLen.value = n
      try {
        localStorage.setItem(REGISTRATION_CODE_LEN_STORAGE_KEY, String(n))
      } catch {}
    }
  }
})

const isValidating = ref(false)

const handleRegister = async () => {
  if (!registrationCode.value) {
    ElMessage.warning('请输入注册码')
    return
  }

  isValidating.value = true
  
  try {
    const res = await pythonBackend.request<any>('licensing.register', {
        code: registrationCode.value
    })
    
    if (res && res.valid) {
      if (registrationCode.value.length > 0) {
        lastRegistrationCodeLen.value = registrationCode.value.length
        try {
          localStorage.setItem(REGISTRATION_CODE_LEN_STORAGE_KEY, String(lastRegistrationCodeLen.value))
        } catch {}
      }
       ElMessage.success({
        message: '软件激活成功！感谢您的支持。',
        type: 'success',
        duration: 3000
      })
      // Update store with new status
      licenseStore.applyStatus({
        valid: res.valid,
        expireDate: res.expireDate ? res.expireDate.split('T')[0] : '--',
        daysLeft: res.daysLeft || 0,
        message: '已激活'
      })
      registrationCode.value = '' // Clear input on success
      isEditingRegistrationCode.value = false
    } else {
      ElMessage.error(res?.message || '注册验证失败，请确认注册码正确')
    }
  } catch (e: any) {
      console.error(e)
      ElMessage.error(`激活失败: ${e.message || '未知错误'}`)
    } finally {
      isValidating.value = false
    }
}
</script>

<style scoped>
.custom-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  padding: 8px 16px;
  transition: all 0.2s;
}

.custom-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #cbd5e1 inset;
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px var(--el-color-primary) inset !important;
}

.custom-input :deep(.el-input__inner) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  letter-spacing: 0.05em;
  color: #334155;
}
</style>
