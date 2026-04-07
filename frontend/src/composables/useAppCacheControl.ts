import { readonly, ref } from 'vue'

const frontendResetEpoch = ref(0)

const PRESERVED_LOCAL_STORAGE_KEYS = ['license_registration_code_len_v1']
const PRESERVED_SESSION_STORAGE_KEYS: string[] = []

function snapshotStorage(storage: Storage, keys: string[]): Array<[string, string]> {
  const kept: Array<[string, string]> = []
  for (const key of keys) {
    try {
      const value = storage.getItem(key)
      if (value !== null) kept.push([key, value])
    } catch (error) {
      console.warn(`[useAppCacheControl] failed to read preserved key ${key}`, error)
    }
  }
  return kept
}

function restoreStorage(storage: Storage, entries: Array<[string, string]>): void {
  for (const [key, value] of entries) {
    try {
      storage.setItem(key, value)
    } catch (error) {
      console.warn(`[useAppCacheControl] failed to restore preserved key ${key}`, error)
    }
  }
}

function clearStorageWithPreservedKeys(storage: Storage, keys: string[]): void {
  const kept = snapshotStorage(storage, keys)
  try {
    storage.clear()
  } catch (error) {
    console.warn('[useAppCacheControl] failed to clear storage', error)
    return
  }
  restoreStorage(storage, kept)
}

export function resetFrontendCaches(): void {
  try {
    clearStorageWithPreservedKeys(localStorage, PRESERVED_LOCAL_STORAGE_KEYS)
  } catch (error) {
    console.warn('[useAppCacheControl] localStorage reset failed', error)
  }

  try {
    clearStorageWithPreservedKeys(sessionStorage, PRESERVED_SESSION_STORAGE_KEYS)
  } catch (error) {
    console.warn('[useAppCacheControl] sessionStorage reset failed', error)
  }

  frontendResetEpoch.value += 1
}

export function useAppCacheControl() {
  return {
    frontendResetEpoch: readonly(frontendResetEpoch),
  }
}
