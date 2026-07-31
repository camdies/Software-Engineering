export const REFRESH_TTL = Object.freeze({
  enrollment: 30_000,
  schedule: 30_000,
  audit: 30_000,
  grades: 60_000,
  statistics: 60_000,
  logs: 60_000,
  semester: 300_000,
  classPeriods: 300_000,
})

export const FOCUS_REFRESH = Object.freeze({
  meaningfulHiddenMs: 15_000,
  minTriggerIntervalMs: 10_000,
})
