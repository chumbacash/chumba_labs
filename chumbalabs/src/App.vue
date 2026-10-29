<script setup lang="ts">
import { computed, ref } from 'vue'
import AgentTimeline from './components/AgentTimeline.vue'
import Chromatogram from './components/Chromatogram.vue'
import InputPanel from './components/InputPanel.vue'
import MethodTable from './components/MethodTable.vue'
import ScoreCards from './components/ScoreCards.vue'
import type { HistoryEntry, RunRequest, RunResponse } from './types/api'

const loading = ref(false)
const error = ref<string | null>(null)
const response = ref<RunResponse | null>(null)
const lastRequest = ref<RunRequest | null>(null)
const selectedIteration = ref(0)

const goals = computed(() => ({
  minResolution: lastRequest.value?.min_resolution ?? 1.5,
  maxRunTime: lastRequest.value?.max_run_time_min ?? 12,
}))

const history = computed(() => response.value?.history ?? [])

const activeEntry = computed<HistoryEntry | null>(() => {
  const h = history.value
  if (!h.length) return null
  const idx = Math.min(selectedIteration.value, h.length - 1)
  return h[idx] ?? null
})

const displayMethod = computed(() => activeEntry.value?.method ?? response.value?.method)
const displaySimulation = computed(() => activeEntry.value?.simulation ?? response.value?.simulation)
const displayScore = computed(() => activeEntry.value?.score ?? response.value?.score)

async function runAgent(request: RunRequest) {
  loading.value = true
  error.value = null
  lastRequest.value = request
  selectedIteration.value = 0
  try {
    const res = await fetch('/api/hplc/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    const data = (await res.json()) as RunResponse & { error?: string }
    if (!res.ok) {
      error.value = data.error ?? `Request failed (${res.status})`
      response.value = null
      return
    }
    response.value = data
    if (data.history?.length) {
      const bestIdx = data.history.findIndex((e) => e.score?.passed)
      selectedIteration.value = bestIdx >= 0 ? bestIdx : data.history.length - 1
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Network error'
    response.value = null
  } finally {
    loading.value = false
  }
}

function onFollowUp(_message: string) {
  if (lastRequest.value) {
    runAgent(lastRequest.value)
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
  <div class="app-shell">
    <header class="top-bar">
      <div class="brand">
        <span class="brand-mark">Chumba Labs</span>
        <span class="brand-sub">Method development workstation</span>
      </div>
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
