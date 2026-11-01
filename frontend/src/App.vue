<script setup lang="ts">
import { computed, ref } from 'vue'
import AgentTimeline from './components/AgentTimeline.vue'
import Chromatogram from './components/Chromatogram.vue'
import InputPanel from './components/InputPanel.vue'
import LandingPage from './components/LandingPage.vue'
import MethodTable from './components/MethodTable.vue'
import ScoreCards from './components/ScoreCards.vue'
import type { HistoryEntry, RunRequest, RunResponse, ScorePayload } from './types/api'

const page = ref<'landing' | 'workbench'>('landing')

const loading = ref(false)
const error = ref<string | null>(null)
const response = ref<RunResponse | null>(null)
const lastRequest = ref<RunRequest | null>(null)
const selectedIteration = ref(0)

const goals = computed(() => ({
  minResolution: lastRequest.value?.min_resolution ?? 1.5,
  maxRunTime: lastRequest.value?.max_run_time_min ?? 12,
}))

function isDisplayable(entry: HistoryEntry | null | undefined): entry is HistoryEntry {
  const peaks = entry?.simulation?.peaks
  const score = entry?.score
  if (!peaks?.length || !score) return false
  if (typeof score.min_resolution !== 'number' || typeof score.passed !== 'boolean') return false
  if ('error' in score && (score as ScorePayload & { error?: unknown }).error) return false
  return peaks.every((peak) => Boolean(peak?.name) && typeof peak.retention_min === 'number')
}

function penaltySum(score: ScorePayload): number {
  return Object.values(score.penalties ?? {}).reduce((sum, value) => sum + Number(value), 0)
}

function betterScore(candidate: ScorePayload, incumbent: ScorePayload | null): boolean {
  if (!incumbent) return true
  if (Boolean(candidate.passed) !== Boolean(incumbent.passed)) return Boolean(candidate.passed)
  const candidatePenalty = penaltySum(candidate)
  const incumbentPenalty = penaltySum(incumbent)
  if (candidatePenalty !== incumbentPenalty) return candidatePenalty < incumbentPenalty
  return candidate.min_resolution > incumbent.min_resolution
}

function bestIndex(entries: HistoryEntry[]): number {
  let best = 0
  entries.forEach((entry, index) => {
    if (betterScore(entry.score, entries[best]?.score ?? null)) best = index
  })
  return best
}

const history = computed(() => (response.value?.history ?? []).filter(isDisplayable))

const activeEntry = computed<HistoryEntry | null>(() => {
  const entries = history.value
  if (!entries.length) {
    const fallback: HistoryEntry = {
      method: response.value?.method as HistoryEntry['method'],
      simulation: response.value?.simulation as HistoryEntry['simulation'],
      score: response.value?.score as HistoryEntry['score'],
    }
    return isDisplayable(fallback) ? fallback : null
  }
  const idx = Math.min(Math.max(selectedIteration.value, 0), entries.length - 1)
  return entries[idx] ?? null
})

const displayMethod = computed(() => activeEntry.value?.method)
const displaySimulation = computed(() => activeEntry.value?.simulation)
const displayScore = computed(() => activeEntry.value?.score)

async function runAgent(request: RunRequest, followUp?: string) {
  loading.value = true
  error.value = null
  lastRequest.value = {
    modality: request.modality,
    analytes: request.analytes,
    max_run_time_min: request.max_run_time_min,
    min_resolution: request.min_resolution,
  }
  selectedIteration.value = 0
  try {
    const body: RunRequest = { ...lastRequest.value }
    if (followUp?.trim()) body.follow_up = followUp.trim()
    const res = await fetch('/api/hplc/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = (await res.json()) as RunResponse & { error?: string }
    if (!res.ok) {
      error.value = data.error ?? `Request failed (${res.status})`
      response.value = null
      return
    }
    response.value = data
    const entries = (data.history ?? []).filter(isDisplayable)
    selectedIteration.value = entries.length ? bestIndex(entries) : 0
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Network error'
    response.value = null
  } finally {
    loading.value = false
  }
}

function onFollowUp(message: string) {
  if (lastRequest.value) {
    runAgent(lastRequest.value, message)
  }
}

function exportCsv() {
  const m = displayMethod.value
  const s = displayScore.value
  if (!m?.column_id || !s) return
  const lines = [
    'field,value',
    `column_id,${m.column_id}`,
    `flow_ml_min,${m.flow_ml_min}`,
    `temperature_c,${m.temperature_c}`,
    `min_resolution,${s.min_resolution}`,
    `total_time_min,${s.total_time_min}`,
    `passed,${s.passed}`,
    'gradient_time_min,percent_b',
    ...m.gradient.map((g) => `${g.time_min},${g.percent_b}`),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'hplc_method.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <LandingPage v-if="page === 'landing'" @launch="page = 'workbench'" />

  <div v-else class="app-shell">
    <header class="top-bar">
      <div class="brand">
        <span class="brand-mark">Chumba Labs</span>
        <span class="brand-sub">method development workbench</span>
      </div>
      <button type="button" class="back-link" @click="page = 'landing'">← Home</button>
    </header>

    <div v-if="error" class="banner error">{{ error }}</div>
    <div v-if="response?.message" class="banner info">{{ response.message }}</div>

    <main class="dashboard">
      <InputPanel :loading="loading" @run="runAgent" />

      <section class="center-pane panel">
        <div v-if="history.length > 1" class="iteration-strip">
          <span class="label">Proposal</span>
          <button
            v-for="(_, i) in history"
            :key="i"
            type="button"
            class="iter-btn"
            :class="{ active: selectedIteration === i }"
            @click="selectedIteration = i"
          >
            {{ i + 1 }}
          </button>
        </div>

        <MethodTable :method="displayMethod" />
        <ScoreCards
          :score="displayScore"
          :min-resolution-target="goals.minResolution"
          :max-run-time-target="goals.maxRunTime"
        />
        <Chromatogram :simulation="displaySimulation" />

        <div class="center-actions">
          <button type="button" class="btn-secondary" :disabled="!displayMethod?.column_id" @click="exportCsv">
            Export method CSV
          </button>
        </div>
      </section>

      <AgentTimeline
        :steps="response?.steps ?? []"
        :explanation="response?.explanation ?? ''"
        :path="response?.path ?? '—'"
        :spark-error="response?.spark_error"
        :loading="loading"
        @follow-up="onFollowUp"
      />
    </main>
  </div>
</template>

<style scoped>
.back-link {
  margin-left: auto;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  padding: 0.3rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  letter-spacing: 0.04em;
  transition: color 0.15s, border-color 0.15s;
}
.back-link:hover {
  color: var(--text-primary);
  border-color: var(--border-active);
}
</style>
