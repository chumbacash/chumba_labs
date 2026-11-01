<script setup lang="ts">
import { computed } from 'vue'
import type { ScorePayload } from '../types/api'

const props = defineProps<{
  score: ScorePayload | null | undefined
  minResolutionTarget: number
  maxRunTimeTarget: number
}>()

type CardState = 'good' | 'warn' | 'bad' | 'neutral'

function rsState(rs: number | undefined): CardState {
  if (rs == null || Number.isNaN(rs)) return 'neutral'
  if (rs >= props.minResolutionTarget) return 'good'
  if (rs >= props.minResolutionTarget * 0.85) return 'warn'
  return 'bad'
}

function timeState(t: number | undefined): CardState {
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
      title: 'Min Rs',
      value: s.min_resolution.toFixed(2),
      target: `≥ ${props.minResolutionTarget}`,
      state: rsState(s.min_resolution),
    },
    {
      title: 'Run time',
      value: `${s.total_time_min?.toFixed(1) ?? '—'} min`,
      target: `≤ ${props.maxRunTimeTarget} min`,
      state: timeState(s.total_time_min),
    },
    {
      title: 'Goals',
      value: s.passed ? 'Pass' : 'Miss',
      target: 'resolution & time',
      state: (s.passed ? 'good' : 'bad') as CardState,
    },
  ]
})
</script>

<template>
  <div class="score-cards">
    <div
      v-for="card in cards"
      :key="card.title"
      class="score-card"
      :class="card.state"
    >
      <span class="card-title">{{ card.title }}</span>
      <span class="card-value">
        {{ card.value }}
        <span class="truth-badge">Source of truth: tool output</span>
      </span>
      <span class="card-target">Target: {{ card.target }}</span>
    </div>
    <p v-if="!cards.length" class="empty">Scores appear after a run.</p>
  </div>
</template>
