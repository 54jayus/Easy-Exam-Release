import { defineStore } from "pinia"
import { ref } from "vue"
import { pythonBackend } from "../lib/pythonBackend"

type LicenseStatus = {
  valid: boolean
  expireDate: string
  daysLeft: number
  message: string
}

export const useLicenseStore = defineStore("license", () => {
  const valid = ref(false)
  const checked = ref(false)
  const status = ref<LicenseStatus>({
    valid: false,
    expireDate: "--",
    daysLeft: 0,
    message: "未注册 / 试用版",
  })

  async function refreshStatus(): Promise<LicenseStatus> {
    try {
      const res = await pythonBackend.request<any>("licensing.verify", {})
      const next: LicenseStatus = {
        valid: !!res?.valid,
        expireDate: res?.expireDate ? String(res.expireDate).split("T")[0] : "--",
        daysLeft: res?.daysLeft || 0,
        message: res?.valid ? "已激活 / 正式版" : res?.message || "未注册",
      }
      status.value = next
      valid.value = next.valid
      return next
    } catch (e) {
      const next: LicenseStatus = {
        valid: false,
        expireDate: "--",
        daysLeft: 0,
        message: "无法连接授权服务",
      }
      status.value = next
      valid.value = false
      return next
    } finally {
      checked.value = true
    }
  }

  function applyStatus(next: Partial<LicenseStatus>): void {
    const merged: LicenseStatus = {
      valid: next.valid ?? status.value.valid,
      expireDate: next.expireDate ?? status.value.expireDate,
      daysLeft: next.daysLeft ?? status.value.daysLeft,
      message: next.message ?? status.value.message,
    }
    status.value = merged
    valid.value = merged.valid
    checked.value = true
  }

  return {
    valid,
    checked,
    status,
    refreshStatus,
    applyStatus,
  }
})

