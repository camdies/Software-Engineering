// Shared ECharts constants and base configuration for all chart components
// in the academic management system.

export const CHART_COLORS = {
  primary: '#6366f1',
  emerald: '#059669',
  amber: '#d97706',
  coral: '#ff6b6b',
  sky: '#0ea5e9',
  mint: '#34d399',
  purple: '#8b5cf6',
  slate: '#64748b',
}

export const chartPalette = Object.values(CHART_COLORS)

export function chartBaseOpts(overrides = {}) {
  return {
    animationDuration: 600,
    animationEasing: 'cubicOut',
    color: chartPalette,
    tooltip: {
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e4e7ec',
      borderWidth: 1,
      textStyle: {
        color: '#1f2937',
        fontSize: 13,
        fontFamily: "'Satoshi','PingFang SC','Microsoft YaHei',sans-serif",
      },
      boxShadow: '0 4px 16px rgba(15,23,42,0.08)',
      extraCssText: 'border-radius:8px;padding:10px 14px;',
    },
    grid: {
      top: 20,
      right: 24,
      bottom: 24,
      left: 24,
      containLabel: true,
    },
    ...overrides,
  }
}

export const GRADE_BAND_COLORS = ['#059669', '#3b82f6', '#d97706', '#ef4444']
export const GRADE_BAND_LABELS = ['优秀 90-100', '良好 75-89', '中等 60-74', '不及格 0-59']
