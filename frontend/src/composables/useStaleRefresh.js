import { onBeforeUnmount, onMounted } from 'vue'
import { FOCUS_REFRESH } from '@/config/refresh-policy'

export function invalidateRefresh(...domains) {
  window.dispatchEvent(new CustomEvent('edumgmt:invalidate', { detail: { domains } }))
}

export function useStaleRefresh(loader, ttlMs, domain = '') {
  let lastSuccessAt = 0
  let hiddenAt = 0
  let lastTriggerAt = 0
  let inFlight = null
  let sequence = 0

  async function loadData({ force = false } = {}) {
    const now = Date.now()
    if (!force && now - lastSuccessAt < ttlMs) return
    if (inFlight) return inFlight
    const current = ++sequence
    inFlight = Promise.resolve(loader(current)).then((result) => {
      if (current === sequence) lastSuccessAt = Date.now()
      return result
    }).finally(() => {
      if (current === sequence) inFlight = null
    })
    return inFlight
  }

  function invalidate() { lastSuccessAt = 0 }

  function onVisibility() {
    if (document.hidden) {
      hiddenAt = Date.now()
      return
    }
    const now = Date.now()
    if (
      hiddenAt && now - hiddenAt >= FOCUS_REFRESH.meaningfulHiddenMs &&
      now - lastTriggerAt >= FOCUS_REFRESH.minTriggerIntervalMs
    ) {
      lastTriggerAt = now
      loadData().catch(() => {})
    }
  }

  function onFocus() {
    const now = Date.now()
    if (
      hiddenAt && now - hiddenAt >= FOCUS_REFRESH.meaningfulHiddenMs &&
      now - lastTriggerAt >= FOCUS_REFRESH.minTriggerIntervalMs
    ) {
      lastTriggerAt = now
      loadData().catch(() => {})
    }
  }

  function onInvalidation(event) {
    if (!domain || event.detail?.domains?.includes(domain)) {
      invalidate()
      loadData({ force: true }).catch(() => {})
    }
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', onVisibility)
    window.addEventListener('focus', onFocus)
    window.addEventListener('edumgmt:invalidate', onInvalidation)
  })
  onBeforeUnmount(() => {
    document.removeEventListener('visibilitychange', onVisibility)
    window.removeEventListener('focus', onFocus)
    window.removeEventListener('edumgmt:invalidate', onInvalidation)
  })

  return { loadData, invalidate }
}
