import { watch, type Ref } from 'vue'
import { usePageSessionState } from '@/composables/usePageSessionState'

export function useRoomsPersistence() {
  const storage = usePageSessionState('rooms')

  // Generic storage helpers
  const getStored = (key: string, def: string) => {
    return storage.getPref(key, def)
  }

  const getCache = (key: string, def: string) => {
    return storage.getCache(key, def)
  }

  const setStored = (key: string, value: string) => {
    storage.setPref(key, value)
  }

  const setCache = (key: string, value: string) => {
    storage.setCache(key, value)
  }

  const removeStored = (key: string) => {
    storage.removePref(key)
  }

  const removeCache = (key: string) => {
    storage.removeCache(key)
  }

  // Initialize state from storage
  const initializeFromStorage = () => {
    return {
      sidebarCollapsed: getStored('sidebarCollapsed', 'false') === 'true',
      activeTab: getStored('activeTab', 'settings'),
      cachedResultsPath: getCache('resultsPath', '')
    }
  }

  // Setup watchers for auto-save
  const setupWatchers = (refs: {
    sidebarCollapsed: Ref<boolean>
    activeTab: Ref<string>
    cachedResultsPath: Ref<string>
  }) => {
    watch(refs.sidebarCollapsed, (val) => {
      setStored('sidebarCollapsed', String(val))
    })

    watch(refs.activeTab, (val) => {
      setStored('activeTab', val)
    })

    watch(refs.cachedResultsPath, (val) => {
      if (val) {
        setCache('resultsPath', val)
      } else {
        removeCache('resultsPath')
      }
    })
  }

  // Clear all storage
  const clearAllStorage = () => {
    removeStored('sidebarCollapsed')
    removeStored('activeTab')
    removeCache('resultsPath')
  }

  return {
    getStored,
    getCache,
    setStored,
    setCache,
    removeStored,
    removeCache,
    initializeFromStorage,
    setupWatchers,
    clearAllStorage
  }
}
