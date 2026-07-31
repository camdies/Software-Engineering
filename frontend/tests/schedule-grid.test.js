import test from 'node:test'
import assert from 'node:assert/strict'

import { REFRESH_TTL, FOCUS_REFRESH } from '../src/config/refresh-policy.js'
import { buildScheduleGrid } from '../src/utils/schedule-grid.js'

test('identical two-period coverage merges from the first atomic row', () => {
  const grid = buildScheduleGrid([{
    plan_id: 1, weekday: 1, period_start: 1, period_count: 2,
  }])
  assert.equal(grid[0][0].rowspan, 2)
  assert.equal(grid[1][0].covered, true)
})

test('different spans sharing a start cell never merge', () => {
  const grid = buildScheduleGrid([
    { plan_id: 1, weekday: 1, period_start: 1, period_count: 2 },
    { plan_id: 2, weekday: 1, period_start: 1, period_count: 1 },
  ])
  assert.equal(grid[0][0].rowspan, 1)
  assert.equal(grid[0][0].courses.length, 2)
  assert.equal(grid[1][0].covered, false)
  assert.equal(grid[1][0].courses.length, 1)
})

test('refresh policy uses reviewed TTL and focus thresholds', () => {
  assert.equal(REFRESH_TTL.schedule, 30_000)
  assert.equal(REFRESH_TTL.audit, 30_000)
  assert.equal(REFRESH_TTL.statistics, 60_000)
  assert.equal(REFRESH_TTL.semester, 300_000)
  assert.equal(FOCUS_REFRESH.meaningfulHiddenMs, 15_000)
  assert.equal(FOCUS_REFRESH.minTriggerIntervalMs, 10_000)
})
