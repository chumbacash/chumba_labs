<script setup lang="ts">
import { onMounted, ref } from 'vue'

const emit = defineEmits<{
  (e: 'launch'): void
}>()

const heroVisible = ref(false)

onMounted(() => {
  requestAnimationFrame(() => {
    heroVisible.value = true
  })
})

/**
 * Generate Gaussian peak points as a polyline string.
 */
function gaussianPeakPoints(
  mu: number,
  sigma: number,
  amplitude: number,
  baseline: number,
  xStart: number,
  xEnd: number,
  steps: number = 80
): string {
  const points: string[] = []
  for (let i = 0; i <= steps; i++) {
    const x = xStart + (xEnd - xStart) * (i / steps)
    const exponent = -0.5 * Math.pow((x - mu) / sigma, 2)
    const y = baseline - amplitude * Math.exp(exponent)
    points.push(`${x.toFixed(1)},${y.toFixed(1)}`)
  }
  return points.join(' ')
}

const chromBaseline = 280
const baselinePoints = `0,${chromBaseline} 600,${chromBaseline}`
const peak1Points = gaussianPeakPoints(160, 25, 200, chromBaseline, 80, 240)
const peak2Points = gaussianPeakPoints(320, 30, 140, chromBaseline, 220, 420)
const peak3Points = gaussianPeakPoints(460, 20, 90, chromBaseline, 390, 530)
</script>

<template>
  <div class="landing">
    <!-- HEADER / NAV BAR -->
    <header class="nav-bar">
      <div class="nav-left">
        <img src="/favicon.svg" alt="Chumba Labs" class="nav-logo" />
        <span class="nav-brand">CHUMBA LABS</span>
      </div>
      <nav class="nav-right">
        <a href="#" class="nav-link">Documentation</a>
        <a href="#" class="nav-link">GitHub</a>
        <a href="#" class="nav-link">About</a>
      </nav>
    </header>

    <!-- HERO SECTION -->
    <section class="hero">
      <div class="hero-content" :class="{ visible: heroVisible }">
        <p class="overline">AUTONOMOUS METHOD DEVELOPMENT</p>
        <h1 class="headline">
          Compress weeks of HPLC method development into minutes.
        </h1>
        <p class="subheadline">
          An agentic copilot that proposes, simulates, and scores chromatography
          methods — so the analyst approves the next experiment, not the model
          alone.
        </p>
        <button class="cta-button" @click="emit('launch')">
          Launch Workbench →
        </button>
        <p class="cta-note">
          No account required · Runs locally or via Meta Muse Spark
        </p>
      </div>

      <!-- Decorative chromatogram SVG -->
      <svg
        class="chromatogram"
        viewBox="0 0 600 300"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        <polyline
          :points="baselinePoints"
          fill="none"
          stroke="#67e8f9"
          stroke-width="1.5"
        />
        <polyline
          :points="peak1Points"
          fill="none"
          stroke="#67e8f9"
          stroke-width="1.5"
        />
        <polyline
          :points="peak2Points"
          fill="none"
          stroke="#fbbf24"
          stroke-width="1.5"
        />
        <polyline
          :points="peak3Points"
          fill="none"
          stroke="#fb7185"
          stroke-width="1.5"
        />
      </svg>
    </section>

    <!-- FEATURES SECTION -->
    <section class="features">
      <p class="section-title">HOW IT WORKS</p>
      <div class="features-grid">
        <div class="feature-card">
          <svg class="feature-icon" viewBox="0 0 40 40">
            <circle cx="20" cy="20" r="19" fill="none" stroke="currentColor" stroke-width="1" />
            <text x="20" y="25" text-anchor="middle" fill="currentColor" font-size="16" font-family="'SF Mono', 'IBM Plex Mono', ui-monospace, monospace">1</text>
          </svg>
          <h3 class="feature-title">Propose</h3>
          <p class="feature-desc">
            Agent generates HPLC method parameters — column, gradient, flow,
            temperature — within instrument constraints.
          </p>
        </div>
        <div class="feature-card">
          <svg class="feature-icon" viewBox="0 0 40 40">
            <circle cx="20" cy="20" r="19" fill="none" stroke="currentColor" stroke-width="1" />
            <text x="20" y="25" text-anchor="middle" fill="currentColor" font-size="16" font-family="'SF Mono', 'IBM Plex Mono', ui-monospace, monospace">2</text>
          </svg>
          <h3 class="feature-title">Simulate</h3>
          <p class="feature-desc">
            Deterministic LSS retention model and peak-width calculation. No
            hallucinated metrics.
          </p>
        </div>
        <div class="feature-card">
          <svg class="feature-icon" viewBox="0 0 40 40">
            <circle cx="20" cy="20" r="19" fill="none" stroke="currentColor" stroke-width="1" />
            <text x="20" y="25" text-anchor="middle" fill="currentColor" font-size="16" font-family="'SF Mono', 'IBM Plex Mono', ui-monospace, monospace">3</text>
          </svg>
          <h3 class="feature-title">Score</h3>
          <p class="feature-desc">
            Resolution, run time, and penalty scoring against your targets.
            Pass/fail is code, not opinion.
          </p>
        </div>
      </div>
    </section>

    <!-- FOOTER -->
    <footer class="footer">
      <p class="footer-text">Built for the Meta Global AI Hackathon 2026</p>
    </footer>
  </div>
</template>

<style scoped>
/* ───────── CSS Variables ───────── */
.landing {
  --bg: #06060a;
  --bg-alt: #080810;
  --text-primary: #e8e8ed;
  --text-muted: #6b6b76;
  --accent: #67e8f9;
  --surface: rgba(255, 255, 255, 0.03);
  --border: rgba(255, 255, 255, 0.06);
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui,
    sans-serif;
  --font-mono: 'SF Mono', 'IBM Plex Mono', ui-monospace, monospace;

  background: var(--bg);
  color: var(--text-primary);
  font-family: var(--font-sans);
  min-height: 100vh;
  overflow-x: hidden;
}

/* ───────── NAV BAR ───────── */
.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
  background: transparent;
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.nav-logo {
  width: 22px;
  height: 22px;
}

.nav-brand {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--text-primary);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 1.75rem;
}

.nav-link {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-muted);
  text-decoration: none;
  letter-spacing: 0.02em;
  transition: color 0.2s ease;
}

.nav-link:hover {
  color: var(--text-primary);
}

/* ───────── HERO ───────── */
.hero {
  position: relative;
  height: calc(100vh - 56px);
  margin-top: 56px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 640px;
  padding-left: 4rem;
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}

.hero-content.visible {
  opacity: 1;
  transform: translateY(0);
}

.overline {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  margin: 0 0 1.25rem 0;
  text-transform: uppercase;
}

.headline {
  font-family: var(--font-sans);
  font-size: 3.2rem;
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin: 0 0 1.5rem 0;
}

.subheadline {
  font-size: 1.1rem;
  line-height: 1.6;
  color: var(--text-muted);
  margin: 0 0 2rem 0;
  max-width: 540px;
}

.cta-button {
  display: inline-block;
  font-family: var(--font-sans);
  font-size: 0.95rem;
  font-weight: 600;
  color: #06060a;
  background: var(--text-primary);
  border: none;
  border-radius: 100px;
  padding: 0.75rem 2rem;
  cursor: pointer;
  transition: background 0.2s ease;
  letter-spacing: -0.01em;
}

.cta-button:hover {
  background: #c8c8d0;
}

.cta-button:active {
  background: #b0b0ba;
}

.cta-note {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  margin: 1rem 0 0 0;
  letter-spacing: 0.01em;
}

/* ───────── Chromatogram decoration ───────── */
.chromatogram {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 55%;
  height: 60%;
  opacity: 0.15;
  pointer-events: none;
  z-index: 1;
}

/* ───────── FEATURES ───────── */
.features {
  background: var(--bg-alt);
  padding: 5rem 4rem;
}

.section-title {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  text-transform: uppercase;
  margin: 0 0 2.5rem 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
}

.feature-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 2rem;
}

.feature-icon {
  width: 40px;
  height: 40px;
  color: var(--text-muted);
  margin-bottom: 1.25rem;
}

.feature-title {
  font-family: var(--font-sans);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
}

.feature-desc {
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--text-muted);
  margin: 0;
}

/* ───────── FOOTER ───────── */
.footer {
  background: var(--bg);
  padding: 3rem 2rem;
  text-align: center;
}

.footer-text {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  margin: 0;
  letter-spacing: 0.02em;
}

/* ───────── Responsive ───────── */
@media (max-width: 768px) {
  .hero-content {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }

  .headline {
    font-size: 2.2rem;
  }

  .features {
    padding: 3rem 1.5rem;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .chromatogram {
    width: 90%;
    opacity: 0.08;
  }

  .nav-bar {
    padding: 0 1rem;
  }

  .nav-right {
    gap: 1rem;
  }

  .nav-link {
    font-size: 0.7rem;
  }
}
</style>
