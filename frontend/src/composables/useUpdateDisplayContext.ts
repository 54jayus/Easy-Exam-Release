import type { ComputedRef, InjectionKey, Ref } from 'vue'
import type { UpdateHistoryEntry, UpdateStatus } from '@/types/appUpdate'

export type UpdateDisplayContext = {
  currentVersion: Ref<string>
  latestVersion: Ref<string>
  releaseDate: Ref<string>
  notes: Ref<string[]>
  visibleNotes: ComputedRef<string[]>
  showAllNotes: Ref<boolean>
  showHistoryPanel: Ref<boolean>
  historyLoading: Ref<boolean>
  historyError: Ref<string>
  updateHistory: Ref<UpdateHistoryEntry[]>
  updateStatus: Ref<UpdateStatus>
  updateStatusTitle: ComputedRef<string>
  updateStatusDescription: ComputedRef<string>
  updateStatusMessage: Ref<string>
  updateStatusTitleClass: ComputedRef<string>
  updateStatusPanelClass: ComputedRef<string>
  updateStatusChipText: ComputedRef<string>
  updateStatusChipClass: ComputedRef<string>
  downloadProgress: Ref<number>
  backgroundDownloadActive: Ref<boolean>
  maxVisibleNotes: ComputedRef<number>
  skipCurrentVersion: () => void
  remindLater: (hours?: number) => void
}

export const UPDATE_DISPLAY_INJECTION_KEY: InjectionKey<UpdateDisplayContext> = Symbol('UpdateDisplayContext')
