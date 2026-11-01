export type Modality = 'hplc' | 'gc_ms'

export interface AnalyteInput {
  name: string
  smiles: string
}

export interface RunRequest {
  modality: Modality
  analytes: AnalyteInput[]
  max_run_time_min: number
  min_resolution: number
  follow_up?: string
}

export interface SimulatedPeak {
  name: string
  retention_min: number
  width_min: number
}

export interface SimulationPayload {
  peaks: SimulatedPeak[]
  total_time_min: number
}

export interface HplcMethod {
  column_id: string
  flow_ml_min: number
  temperature_c: number
  gradient: { time_min: number; percent_b: number }[]
}

export interface ScorePayload {
  min_resolution: number
  total_time_min: number
  passed: boolean
  penalties: Record<string, number>
  method?: HplcMethod
  simulation?: SimulationPayload
}

export interface HistoryEntry {
  method: HplcMethod
  simulation: SimulationPayload
  score: ScorePayload
}

export interface AgentStep {
  tool: string
  output: unknown
}

export interface RunResponse {
  path: string
  modality: Modality
  message?: string
  min_resolution: number | null
  total_time_min: number | null
  passed: boolean
  penalties: Record<string, number>
  method: HplcMethod
  simulation: SimulationPayload
  score: ScorePayload
  steps: AgentStep[]
  history: HistoryEntry[]
  explanation: string
  iterations: number
  spark_error?: string
}
