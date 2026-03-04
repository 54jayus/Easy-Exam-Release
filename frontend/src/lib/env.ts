export function isElectron(): boolean {
  if (typeof window === "undefined") return false
  return !!(window as any).electron
}
