<script setup lang="ts">
import { ref } from 'vue'
import type { AnalyteInput, Modality, RunRequest } from '../types/api'

const emit = defineEmits<{
  run: [payload: RunRequest]
}>()

defineProps<{
  loading: boolean
}>()

const modality = ref<Modality>('hplc')
const minResolution = ref(1.5)
const maxRunTime = ref(12)
const analytes = ref<AnalyteInput[]>([
  { name: 'A', smiles: 'CCO' },
  { name: 'B', smiles: 'CC(=O)O' },
  { name: 'C', smiles: 'c1ccccc1' },
])

const newName = ref('')
const newSmiles = ref('')

function addAnalyte() {
  const name = newName.value.trim()
  const smiles = newSmiles.value.trim()
  if (!name || !smiles) return
  analytes.value.push({ name, smiles })
  newName.value = ''
  newSmiles.value = ''
}

function removeAnalyte(index: number) {
  analytes.value.splice(index, 1)
}

function submit() {
  if (analytes.value.length === 0) return
  emit('run', {
    modality: modality.value,
    analytes: [...analytes.value],
    max_run_time_min: maxRunTime.value,
    min_resolution: minResolution.value,
  })
}
</script>

<template>
  <aside class="panel input-panel">
    <header class="panel-header">
      <h2>Experiment input</h2>
    </header>

    <section class="section">
      <span class="label">Modality</span>
      <div class="toggle-row">
        <label class="toggle">
          <input v-model="modality" type="radio" value="hplc" />
          HPLC
        </label>
        <label class="toggle">
          <input v-model="modality" type="radio" value="gc_ms" />
          GC-MS
        </label>
      </div>
      <p v-if="modality === 'gc_ms'" class="hint">
        GC-MS is stub-only in this build; the API returns a not-implemented notice.
      </p>
    </section>

    <section class="section">
      <span class="label">Analytes</span>
      <ul class="analyte-list">
        <li v-for="(a, i) in analytes" :key="`${a.name}-${i}`" class="analyte-row">
          <span class="analyte-name">{{ a.name }}</span>
          <code class="smiles">{{ a.smiles }}</code>
          <button type="button" class="btn-ghost" aria-label="Remove" @click="removeAnalyte(i)">×</button>
        </li>
      </ul>
      <div class="add-row">
        <input v-model="newName" placeholder="Name" class="field" />
        <input v-model="newSmiles" placeholder="SMILES" class="field flex" />
        <button type="button" class="btn-secondary" @click="addAnalyte">Add</button>
      </div>
    </section>

    <section class="section goals">
      <span class="label">Goals</span>
      <label class="goal-field">
        Min resolution (Rs)
        <input v-model.number="minResolution" type="number" step="0.1" min="0.5" class="field" />
      </label>
      <label class="goal-field">
        Max run time (min)
        <input v-model.number="maxRunTime" type="number" step="0.5" min="1" class="field" />
      </label>
    </section>

    <button type="button" class="btn-primary run-btn" :disabled="loading || analytes.length === 0" @click="submit">
      {{ loading ? 'Running agent…' : 'Run agent' }}
    </button>
  </aside>
</template>
