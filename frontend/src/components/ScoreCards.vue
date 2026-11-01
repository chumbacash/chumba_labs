<script setup lang="ts">
import { computed } from 'vue'
import type { ScorePayload } from '../types/api'

const props = defineProps<{
  score: ScorePayload | null | undefined
  minResolutionTarget: number
  maxRunTimeTarget: number
}>()

type KpiState = 'good' | 'warn' | 'bad' | 'neutral'

function rsState(rs: number | undefined): KpiState {
  if (rs == null || Number.isNaN(rs)) return 'neutral'
  if (rs >= props.minResolutionTarget) return 'good'
  if (rs >= props.minResolutionTarget * 0.85) return 'warn'
  return 'bad'
}

function timeState(t: number | undefined): KpiState {
  if (t == null || Number.isNaN(t)) return 'neutral'
  if (t <= props.maxRunTimeTarget) return 'good'
  if (t <= props.maxRunTimeTarget * 1.1) return 'warn'
  return 'bad'
}

const cards = computed(() => {
  const s = props.score
  if (!s || s.min_resolution == null) {
    return []
  }
  return [
    {
      label: 'Min resolution',
      value: s.min_resolution.toFixed(2),
      unit: '',
      target: `≥ ${props.minResolutionTarget}`,
      ghost: String(props.minResolutionTarget),
      state: rsState(s.min_resolution),
    },
    {
      label: 'Run time',
      value: s.total_time_min?.toFixed(1) ?? '—',
      unit: 'min',
      target: `≤ ${props.maxRunTimeTarget} min`,
      ghost: String(props.maxRunTimeTarget),
      state: timeState(s.total_time_min),
    },
    {
      label: 'Goals',
      value: s.passed ? 'Pass' : 'Miss',
      unit: '',
      target: 'resolution & time',
      ghost: s.passed ? '✓' : '✕',
      state: (s.passed ? 'good' : 'bad') as KpiState,
    },
  ]
})
</script>

<template>
  <div class="score-band">
    <template v-if="cards.length">
      <div v-for="card in cards" :key="card.label" class="kpi" :class="card.state">
        <span class="kpi-ghost" aria-hidden="true">{{ card.ghost }}</span>
        <span class="kpi-label">{{ card.label }}</span>
        <span class="kpi-value">
          {{ card.value }}
          <span v-if="card.unit" class="kpi-unit">{{ card.unit }}</span>
        </span>
        <span class="kpi-target">Target {{ card.target }}</span>
      </div>
      <p class="truth-note">Scores are tool output, not narrative.</p>
    </template>
    <p v-else class="empty">Scores appear after a run.</p>
  </div>
</template>
