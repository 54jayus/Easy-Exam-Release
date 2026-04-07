import { readonly, ref, type Ref } from 'vue'
import { usePageSessionState } from './usePageSessionState'

const frontendResetEpoch = ref(0)

type ManagedPageId = 'subjects' | 'proctoring' | 'rooms' | 'printing'
type DependencySignalId = 'proctoring' | 'printingSubjects' | 'printingSchedule'

const PRESERVED_LOCAL_STORAGE_KEYS = ['license_registration_code_len_v1']
const PRESERVED_SESSION_STORAGE_KEYS: string[] = []

const pageResetEpochs: Record<ManagedPageId, Ref<number>> = {
  subjects: ref(0),
  proctoring: ref(0),
  rooms: ref(0),
  printing: ref(0),
}

const dependencySignalEpochs: Record<DependencySignalId, Ref<number>> = {
  proctoring: ref(0),
  printingSubjects: ref(0),
  printingSchedule: ref(0),
}

const PAGE_STORAGE_RULES: Record<ManagedPageId, { prefs: string[]; caches: string[] }> = {
  subjects: {
    prefs: ['viewMode'],
    caches: [],
  },
  proctoring: {
    prefs: ['sidebarCollapsed', 'activeTab'],
    caches: [],
  },
  rooms: {
    prefs: ['sidebarCollapsed', 'activeTab'],
    caches: ['resultsPath'],
  },
  printing: {
    prefs: ['sidebarCollapsed', 'activeTab', 'subjectRows_v1', 'studentInfoTitles_v1'],
    caches: ['filePreview_v1'],
  },
}

const DEPENDENCY_STORAGE_RULES: Record<DependencySignalId, Array<{ pageId: ManagedPageId; prefs?: string[]; caches?: string[] }>> = {
  proctoring: [
    { pageId: 'proctoring', prefs: ['sidebarCollapsed', 'activeTab'] },
  ],
  printingSubjects: [
    { pageId: 'printing', prefs: ['subjectRows_v1'] },
  ],
  printingSchedule: [],
}

const RESET_PROPAGATION_RULES: Record<ManagedPageId, DependencySignalId[]> = {
  subjects: ['proctoring', 'printingSubjects'],
  proctoring: [],
  rooms: ['printingSchedule'],
  printing: [],
}

function clearManagedPageStorage(pageId: ManagedPageId): void {
  const storage = usePageSessionState(pageId)
  const rule = PAGE_STORAGE_RULES[pageId]
  if (rule.prefs.length > 0) {
    storage.clearPrefs(rule.prefs)
  }
  if (rule.caches.length > 0) {
    storage.clearCaches(rule.caches)
  }
}

function clearScopedStorage(pageId: ManagedPageId, prefs: string[] = [], caches: string[] = []): void {
  const storage = usePageSessionState(pageId)
  if (prefs.length > 0) {
    storage.clearPrefs(prefs)
  }
  if (caches.length > 0) {
    storage.clearCaches(caches)
  }
}

function bumpDependencySignal(signalId: DependencySignalId): void {
  for (const target of DEPENDENCY_STORAGE_RULES[signalId]) {
    clearScopedStorage(target.pageId, target.prefs ?? [], target.caches ?? [])
  }
  const epoch = dependencySignalEpochs[signalId]
  if (!epoch) return
  epoch.value += 1
}

function bumpAllResetSignals(): void {
  for (const pageId of Object.keys(pageResetEpochs) as ManagedPageId[]) {
    const epoch = pageResetEpochs[pageId]
    if (epoch) epoch.value += 1
  }
  for (const signalId of Object.keys(dependencySignalEpochs) as DependencySignalId[]) {
    const epoch = dependencySignalEpochs[signalId]
    if (epoch) epoch.value += 1
  }
}

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

  bumpAllResetSignals()
  frontendResetEpoch.value += 1
}

export function applyPageReset(pageId: ManagedPageId): void {
  clearManagedPageStorage(pageId)
  const epoch = pageResetEpochs[pageId]
  if (epoch) epoch.value += 1
  for (const signalId of RESET_PROPAGATION_RULES[pageId]) {
    bumpDependencySignal(signalId)
  }
}

export function useAppCacheControl() {
  return {
    frontendResetEpoch: readonly(frontendResetEpoch),
    subjectsResetEpoch: readonly(pageResetEpochs.subjects),
    proctoringResetEpoch: readonly(pageResetEpochs.proctoring),
    roomsResetEpoch: readonly(pageResetEpochs.rooms),
    printingResetEpoch: readonly(pageResetEpochs.printing),
    proctoringDependencyEpoch: readonly(dependencySignalEpochs.proctoring),
    printingSubjectDependencyEpoch: readonly(dependencySignalEpochs.printingSubjects),
    printingScheduleDependencyEpoch: readonly(dependencySignalEpochs.printingSchedule),
  }
}
