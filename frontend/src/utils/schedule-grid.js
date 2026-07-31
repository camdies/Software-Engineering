export function buildScheduleGrid(courses) {
  const grid = Array.from({ length: 11 }, () =>
    Array.from({ length: 7 }, () => ({ courses: [], rowspan: 1, covered: false })),
  )
  for (const course of courses) {
    const start = Number(course.period_start) - 1
    const count = Number(course.period_count)
    const day = Number(course.weekday) - 1
    if (day < 0 || day > 6 || start < 0 || count < 1 || start + count > 11) continue
    for (let period = start; period < start + count; period += 1) {
      grid[period][day].courses.push(course)
    }
  }

  for (let day = 0; day < 7; day += 1) {
    let period = 0
    while (period < 11) {
      const group = grid[period][day].courses
      const signature = group.map((course) => String(course.plan_id)).sort().join(',')
      let end = period + 1
      while (
        end < 11 &&
        grid[end][day].courses.map((course) => String(course.plan_id)).sort().join(',') === signature
      ) end += 1
      const span = end - period
      const merge = group.length > 0 && span > 1 && group.every((course) =>
        Number(course.period_start) === period + 1 && Number(course.period_count) === span,
      )
      if (merge) {
        grid[period][day].rowspan = span
        for (let covered = period + 1; covered < end; covered += 1) {
          grid[covered][day].covered = true
        }
      }
      period = end
    }
  }
  return grid
}
