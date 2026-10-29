<script setup lang="ts">
import { computed } from 'vue'
import type { SimulationPayload } from '../types/api'

const props = defineProps<{
  simulation: SimulationPayload | null | undefined
}>()

const width = 640
const height = 220
const pad = { l: 48, r: 16, t: 24, b: 36 }

const plot = computed(() => {
  const peaks = props.simulation?.peaks ?? []
  if (!peaks.length) {
    return { path: '', labels: [] as { x: number; y: number; name: string }[], xMax: 12 }
  }
  const xMax = Math.max(
    props.simulation?.total_time_min ?? 0,
    ...peaks.map((p) => p.retention_min + p.width_min * 3),
    1,
  )
  const xScale = (t: number) => pad.l + (t / xMax) * (width - pad.l - pad.r)
  const yScale = (y: number) => pad.t + (1 - y) * (height - pad.t - pad.b)

  const points: string[] = []
  const steps = 400
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * xMax
    let signal = 0.02
    for (const peak of peaks) {
      const sigma = peak.width_min / 2.355
      const z = (t - peak.retention_min) / Math.max(sigma, 0.01)
      signal += Math.exp(-0.5 * z * z)
    }
    points.push(`${xScale(t)},${yScale(Math.min(signal, 1.2) / 1.2)}`)
  }

  const labels = peaks.map((p) => ({
    x: xScale(p.retention_min),
    y: yScale(0.92),
    name: p.name,
  }))

  return { path: points.join(' '), labels, xMax }
})
</script>

<template>
  <div class="chrom-wrap">
    <div class="chrom-header">
      <h3>Chromatogram</h3>
      <p class="disclaimer">Predicted retention times (LSS model)</p>
    </div>
    <svg
      v-if="simulation?.peaks?.length"
      :viewBox="`0 0 ${width} ${height}`"
      class="chrom-svg"
      role="img"
      aria-label="Simulated chromatogram"
    >
      <line
        :x1="pad.l"
        :y1="height - pad.b"
        :x2="width - pad.r"
        :y2="height - pad.b"
        class="axis"
      />
      <line :x1="pad.l" :y1="pad.t" :x2="pad.l" :y2="height - pad.b" class="axis" />
      <polyline :points="plot.path" class="trace" fill="none" />
      <text :x="width / 2" :y="height - 8" class="axis-label" text-anchor="middle">
        Time (min)
      </text>
      <g v-for="lbl in plot.labels" :key="lbl.name">
        <line :x1="lbl.x" :y1="lbl.y + 4" :x2="lbl.x" :y2="height - pad.b" class="peak-marker" />
        <text :x="lbl.x" :y="lbl.y" class="peak-label" text-anchor="middle">{{ lbl.name }}</text>
      </g>
    </svg>
    <p v-else class="empty">No peaks to plot.</p>
  </div>
</template>
