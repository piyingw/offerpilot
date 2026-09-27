import { BarChart, FunnelChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
} from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsCoreOption } from 'echarts/core'
import { useEffect, useRef } from 'react'

echarts.use([
  BarChart,
  FunnelChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  CanvasRenderer,
])

interface EChartProps {
  option: EChartsCoreOption
  height?: number
}

/** 轻量 ECharts 封装：按需注册图表类型，自动处理初始化 / 更新 / 销毁 / resize */
export default function EChart({ option, height = 300 }: EChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!containerRef.current) return undefined
    const chart = echarts.init(containerRef.current)
    chartRef.current = chart
    const handleResize = () => chart.resize()
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      chart.dispose()
      chartRef.current = null
    }
  }, [])

  useEffect(() => {
    chartRef.current?.setOption(option, true)
  }, [option])

  return <div ref={containerRef} style={{ width: '100%', height }} />
}
