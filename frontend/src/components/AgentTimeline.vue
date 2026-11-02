<script setup lang="ts">
import { ref } from 'vue'
import type { AgentStep } from '../types/api'

defineProps<{
  steps: AgentStep[]
  explanation: string
  path: string
  sparkError?: string
  loading: boolean
  sectionId?: string
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
    return JSON.stringify(roundFloats(value), null, 2)
  } catch {
    return String(value)
  }
}

/**
 * Round every float in tool output to 4 decimals so JSON dumps stay
 * scannable. Integers, strings, and short floats pass through untouched.
 */
function roundFloats(value: unknown): unknown {
  if (typeof value === 'number') {
    if (!Number.isFinite(value) || Number.isInteger(value)) return value
    return Number(value.toFixed(4))
  }
  if (Array.isArray(value)) return value.map(roundFloats)
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, entry]) => [key, roundFloats(entry)]),
    )
  }
  return value
}

/**
 * The model returns plain text with **Section** markers, " - " separators,
 * and full-precision floats. Parse the markers into real subheaded
 * paragraphs so Method / Simulation / Score read as separate blocks.
 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function roundLongFloats(text: string): string {
  return text.replace(/(\d+)\.(\d{3})\d+/g, '$1.$2')
}

function formatItems(body: string): string {
  const items = body
    .replace(/^[:*\-\s]+/, '')
    .split(/\s+(?:-|\*)\s+/)
    .map((item) => item.trim())
    .filter(Boolean)
  return items
    .map((item) => {
      const match = item.match(/^([^:]+):\s*(.*)$/)
      const labeled = match
        ? `<strong>${match[1].trim()}:</strong> ${match[2].trim()}`
        : item
      return `<span class="muse-sep">•</span> ${labeled}`
    })
    .join('<br>')
}

function formatTitle(header: string): string {
  return header
    .trim()
    .replace(/\s*\(from .+\)$/, '')
    .replace(/:$/, '')
}

function formatExplanation(text: string): string {
  const cleaned = roundLongFloats(escapeHtml(text))
  const parts = cleaned.split(/\*\*(.+?)\*\*/g)
  if (parts.length === 1) {
    return `<p class="muse-intro">${formatItems(cleaned)}</p>`
  }
  let html = ''
  const intro = parts[0].trim().replace(/:?-?\s*$/, '')
  if (intro) html += `<p class="muse-intro">${intro}</p>`
  for (let i = 1; i < parts.length; i += 2) {
    const title = formatTitle(parts[i] ?? '')
    const body = formatItems(parts[i + 1] ?? '')
    if (!title && !body) continue
    html += `<div class="muse-section"><h4 class="muse-section-title">${title}</h4>`
    if (body) html += `<p class="muse-items">${body}</p>`
    html += `</div>`
  }
  return html || `<p class="muse-intro">${cleaned}</p>`
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
  <aside id="timeline" class="panel timeline-panel">
    <header class="panel-header">
      <h2 class="heading-anchor">Agent timeline</h2>
      <span class="panel-sub">Tool calls, in order.</span>
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
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div class="muse-text" v-html="formatExplanation(explanation)"></div>
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
