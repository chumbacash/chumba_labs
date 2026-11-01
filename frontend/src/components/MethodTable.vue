<script setup lang="ts">
import { computed } from 'vue'
import type { HplcMethod } from '../types/api'

const props = defineProps<{
  method: HplcMethod | null | undefined
}>()

const rows = computed(() => {
  const m = props.method
  if (!m || !m.column_id) return []
  return [
    { label: 'Column', value: m.column_id },
    { label: 'Flow (mL/min)', value: String(m.flow_ml_min) },
    { label: 'Temperature (°C)', value: String(m.temperature_c) },
  ]
})

const gradientText = computed(() => {
  const g = props.method?.gradient ?? []
  if (!g.length) return '—'
  return g.map((s) => `${s.time_min} min → ${s.percent_b}% B`).join('; ')
})
</script>

<template>
  <div class="method-table-wrap">
    <h3>Proposed method</h3>
    <table v-if="rows.length" class="method-table">
      <tbody>
        <tr v-for="row in rows" :key="row.label">
          <th>{{ row.label }}</th>
          <td>
            {{ row.value }}
            <span class="truth-badge" title="From tool output">Source of truth: tool output</span>
          </td>
        </tr>
        <tr>
          <th>Gradient</th>
          <td>{{ gradientText }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty">Run the agent to generate a method.</p>
  </div>
</template>
