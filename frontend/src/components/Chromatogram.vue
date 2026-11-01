<script setup lang="ts">
import { computed } from 'vue'
import type { SimulatedPeak, SimulationPayload } from '../types/api'

const props = defineProps<{
  simulation: SimulationPayload | null | undefined
}>()

const width = 640
const colors = ['#67e8f9', '#fbbf24', '#fb7185', '#a3e635', '#c4b5fd', '#fdba74']

const plot = computed(() => {
  const peaks = props.simulation?.peaks ?? []
  const empty = {
    traces: [] as { points: string; color: string }[],
    labels: [] as { x: number; y: number; name: string; color: string }[],
    ticks: [] as { x: number; label: string }[],
    xMax: 12,
    height: 220,
    pad: { l: 48, r: 16, t: 28, b: 36 },
    coelution: '',
  }
  if (!peaks.length) return empty

  const xMax = Math.max(
    props.simulation?.total_time_min ?? 0,
    ...peaks.map((p) => p.retention_min + p.width_min * 3),
    1,
  )
  const padL = 48
  const padR = 16
  const padB = 36
  const xScale = (t: number) => padL + (t / xMax) * (width - padL - padR)
  const labelHalf = (name: string) => Math.max(name.length * 3.35, 8)

  const placed: { x: number; row: number; half: number; name: string; color: string }[] = []
  peaks.forEach((peak, index) => {
    const half = labelHalf(peak.name)
    const x = Math.min(width - padR - half - 2, Math.max(padL + half + 2, xScale(peak.retention_min)))
    let row = 0
    while (
      placed.some((other) => other.row === row && Math.abs(other.x - x) < other.half + half + 8) &&
      row < 5
    ) {
      row += 1
    }
    placed.push({ x, row, half, name: peak.name, color: colors[index % colors.length] })
  })

  const rows = Math.max(...placed.map((item) => item.row), 0) + 1
  const padT = 8 + rows * 14
  const height = padT + 160 + padB
  const yScale = (y: number) => padT + (1 - y) * (height - padT - padB)
  const minWidth = Math.min(...peaks.map((peak) => Math.max(peak.width_min, 0.02)))
  const steps = Math.max(500, Math.min(4000, Math.ceil(xMax / Math.min(xMax / 500, minWidth / 10))))

  const traceFor = (peak: SimulatedPeak) => {
    const points: string[] = []
    const sigma = Math.max(peak.width_min / 2.355, 0.01)
    for (let i = 0; i <= steps; i++) {
      const t = (i / steps) * xMax
      const z = (t - peak.retention_min) / sigma
      const signal = Math.exp(-0.5 * z * z)
      points.push(`${xScale(t)},${yScale(Math.min(signal, 1.2) / 1.2)}`)
    }
    return points.join(' ')
  }

  const pairs: string[] = []
  for (let i = 0; i < peaks.length; i++) {
    for (let j = i + 1; j < peaks.length; j++) {
      if (Math.abs(peaks[i].retention_min - peaks[j].retention_min) < 0.05) {
        pairs.push(`${peaks[i].name} and ${peaks[j].name}`)
      }
    }
  }

  // Nice-ticks for the time axis (1 / 2 / 5 / 10 minute steps).
  const rawStep = xMax / 6
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)))
  const normalized = rawStep / magnitude
  const niceMultiple = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10
  const tickStep = niceMultiple * magnitude
  const tickCount = Math.floor(xMax / tickStep + 1e-9)
  const ticks = Array.from({ length: tickCount + 1 }, (_, i) => {
    const t = Math.round(i * tickStep * 10) / 10
    return { x: xScale(t), label: String(t) }
  })

  return {
    traces: peaks.map((peak, index) => ({
      points: traceFor(peak),
      color: colors[index % colors.length],
    })),
    labels: placed.map((item) => ({
      x: item.x,
      y: 4 + item.row * 14 + 11,
      name: item.name,
      color: item.color,
    })),
    ticks,
    xMax,
    height,
    pad: { l: padL, r: padR, t: padT, b: padB },
    coelution: pairs.length ? `LSS model predicts co-elution: ${pairs.join('; ')}` : '',
  }
})
</script>

<template>
  <div class="chrom-wrap">
    <div class="section-head">
      <h3>Chromatogram</h3>
      <p>Predicted retention times from the LSS model.</p>
    </div>
    <svg
      v-if="simulation?.peaks?.length"
      :viewBox="`0 0 ${width} ${plot.height}`"
      class="chrom-svg"
      role="img"
      aria-label="Simulated chromatogram"
    >
      <line
        :x1="plot.pad.l"
        :y1="plot.height - plot.pad.b"
        :x2="width - plot.pad.r"
        :y2="plot.height - plot.pad.b"
        class="axis"
      />
      <line
        :x1="plot.pad.l"
        :y1="plot.pad.t"
        :x2="plot.pad.l"
        :y2="plot.height - plot.pad.b"
        class="axis"
      />
      <polyline
        v-for="(trace, i) in plot.traces"
        :key="`trace-${i}`"
        :points="trace.points"
        class="trace"
        fill="none"
        :style="{ stroke: trace.color }"
      />
      <g v-for="(tick, i) in plot.ticks" :key="`tick-${i}`">
        <line
          :x1="tick.x"
          :y1="plot.height - plot.pad.b"
          :x2="tick.x"
          :y2="plot.height - plot.pad.b + 4"
          class="tick"
        />
        <text :x="tick.x" :y="plot.height - plot.pad.b + 14" class="tick-label" text-anchor="middle">
          {{ tick.label }}
        </text>
      </g>
      <text :x="width / 2" :y="plot.height - 2" class="axis-label" text-anchor="middle">
        Time (min)
      </text>
      <g v-for="(lbl, i) in plot.labels" :key="`label-${i}`">
        <line
          :x1="lbl.x"
          :y1="lbl.y + 4"
          :x2="lbl.x"
          :y2="plot.height - plot.pad.b"
          class="peak-marker"
          :style="{ stroke: lbl.color }"
        />
        <text :x="lbl.x" :y="lbl.y" class="peak-label" text-anchor="middle" :style="{ fill: lbl.color }">
          {{ lbl.name }}
        </text>
      </g>
    </svg>
    <p v-if="plot.coelution" class="coelute-note">{{ plot.coelution }}</p>
    <p v-else-if="!simulation?.peaks?.length" class="empty">No peaks to plot.</p>
  </div>
</template>
