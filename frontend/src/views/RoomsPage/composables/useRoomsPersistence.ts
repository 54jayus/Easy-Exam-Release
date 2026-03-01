import { watch, type Ref } from 'vue'

export function useRoomsPersistence() {
  // Generic storage helpers
  const getStored = (key: string, def: string) => {
    return sessionStorage.getItem(`rooms_pref_${key}`) || def
  }

  const getCache = (key: string, def: string) => {
    return sessionStorage.getItem(`rooms_cache_${key}`) || def
  }

  const setStored = (key: string, value: string) => {
    sessionStorage.setItem(`rooms_pref_${key}`, value)
  }

  const setCache = (key: string, value: string) => {
    sessionStorage.setItem(`rooms_cache_${key}`, value)
  }

  const removeStored = (key: string) => {
    sessionStorage.removeItem(`rooms_pref_${key}`)
  }

  const removeCache = (key: string) => {
    sessionStorage.removeItem(`rooms_cache_${key}`)
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
