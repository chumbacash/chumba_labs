<script setup lang="ts">
import { ref } from 'vue'
import type { AgentStep } from '../types/api'

defineProps<{
  steps: AgentStep[]
  explanation: string
  path: string
  sparkError?: string
  loading: boolean
}>()

const emit = defineEmits<{
  followUp: [message: string]
}>()

const open = ref<Record<number, boolean>>({})
const followUp = ref('')

function toggle(i: number) {
  open.value[i] = !open.value[i]
}

function prettyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function sendFollowUp() {
  const text = followUp.value.trim()
  if (!text) return
  emit('followUp', text)
  followUp.value = ''
}

function stepError(output: unknown): string | null {
  let value = output
  if (typeof value === 'string') {
    try {
      value = JSON.parse(value)
    } catch {
      return null
    }
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  const error = (value as { error?: unknown }).error
  return typeof error === 'string' && error ? error : null
}
</script>

<template>
  <aside class="panel timeline-panel">
    <header class="panel-header">
      <h2>Agent timeline</h2>
      <span class="path-tag">{{ path }}</span>
    </header>

    <p v-if="loading" class="loading-line">
      <span class="spinner"></span>Agent running…
    </p>
    <p v-if="sparkError" class="warn">Spark fallback: {{ sparkError }}</p>

    <ol class="timeline">
      <li v-for="(step, i) in steps" :key="i" class="timeline-item" :class="{ error: stepError(step.output) }">
        <button type="button" class="tool-card" :class="{ error: stepError(step.output) }" @click="toggle(i)">
          <span class="tool-name">{{ step.tool }}</span>
          <span v-if="stepError(step.output)" class="tool-flag">error</span>
          <span class="chevron">{{ open[i] ? '▼' : '▶' }}</span>
        </button>
        <p v-if="stepError(step.output)" class="tool-error">{{ stepError(step.output) }}</p>
        <pre v-if="open[i]" class="tool-json">{{ prettyJson(step.output) }}</pre>
      </li>
    </ol>

    <section v-if="explanation" class="muse-block">
      <h3>Agent decision (Muse Spark)</h3>
      <p class="muse-text">{{ explanation }}</p>
      <p class="hint">Numbers in the narrative should match tool cards above.</p>
    </section>

    <section class="follow-up">
      <label class="label">Follow-up (re-runs agent)</label>
      <textarea v-model="followUp" rows="2" class="field" placeholder="Optional note to the agent…" />
      <button type="button" class="btn-secondary" :disabled="loading || !followUp.trim()" @click="sendFollowUp">
        Send
      </button>
    </section>
  </aside>
</template>
