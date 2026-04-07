type StorageBucket = 'pref' | 'cache'

function buildStorageKey(pageId: string, bucket: StorageBucket, key: string): string {
  return `${pageId}_${bucket}_${key}`
}

export function usePageSessionState(pageId: string) {
  const warn = (action: string, key: string, error: unknown): void => {
    console.warn(`[usePageSessionState] ${pageId}.${action}(${key}) failed`, error)
  }

  const getRaw = (bucket: StorageBucket, key: string): string | null => {
    const storageKey = buildStorageKey(pageId, bucket, key)
    try {
      return sessionStorage.getItem(storageKey)
    } catch (error) {
      warn('getRaw', storageKey, error)
      return null
    }
  }

  const has = (bucket: StorageBucket, key: string): boolean => {
    return getRaw(bucket, key) !== null
  }

  const get = (bucket: StorageBucket, key: string, fallback: string): string => {
    return getRaw(bucket, key) ?? fallback
  }

  const set = (bucket: StorageBucket, key: string, value: string): void => {
    const storageKey = buildStorageKey(pageId, bucket, key)
    try {
      sessionStorage.setItem(storageKey, value)
    } catch (error) {
      warn('set', storageKey, error)
    }
  }

  const remove = (bucket: StorageBucket, key: string): void => {
    const storageKey = buildStorageKey(pageId, bucket, key)
    try {
      sessionStorage.removeItem(storageKey)
    } catch (error) {
      warn('remove', storageKey, error)
    }
  }

  const getJson = <T>(bucket: StorageBucket, key: string, fallback: T): T => {
    const raw = getRaw(bucket, key)
    if (!raw) return fallback
    try {
      return JSON.parse(raw) as T
    } catch {
      return fallback
    }
  }

  const setJson = (bucket: StorageBucket, key: string, value: unknown): void => {
    const storageKey = buildStorageKey(pageId, bucket, key)
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(value))
    } catch (error) {
      warn('setJson', storageKey, error)
    }
  }

  const clear = (bucket: StorageBucket, keys: string[]): void => {
    for (const key of keys) {
      remove(bucket, key)
    }
  }

  return {
    hasPref: (key: string) => has('pref', key),
    hasCache: (key: string) => has('cache', key),
    getPref: (key: string, fallback: string) => get('pref', key, fallback),
    getCache: (key: string, fallback: string) => get('cache', key, fallback),
    setPref: (key: string, value: string) => set('pref', key, value),
    setCache: (key: string, value: string) => set('cache', key, value),
    removePref: (key: string) => remove('pref', key),
    removeCache: (key: string) => remove('cache', key),
    getJsonPref: <T>(key: string, fallback: T) => getJson<T>('pref', key, fallback),
    getJsonCache: <T>(key: string, fallback: T) => getJson<T>('cache', key, fallback),
    setJsonPref: (key: string, value: unknown) => setJson('pref', key, value),
    setJsonCache: (key: string, value: unknown) => setJson('cache', key, value),
    clearPrefs: (keys: string[]) => clear('pref', keys),
    clearCaches: (keys: string[]) => clear('cache', keys),
  }
}
