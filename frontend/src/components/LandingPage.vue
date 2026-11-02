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
    <!-- HEADER / NAV BAR - Floating -->
    <header class="nav-bar">
      <div class="nav-container">
        <div class="nav-left">
          <span class="nav-brand">CHUMBA LABS</span>
        </div>
        <nav class="nav-center">
          <a href="#features" class="nav-link">How It Works</a>
          <a href="https://github.com/chumba-labs" target="_blank" class="nav-link">GitHub</a>
          <a href="#about" class="nav-link">About</a>
        </nav>
        <div class="nav-right">
          <button class="nav-cta" @click="emit('launch')">Launch Workbench</button>
        </div>
      </div>
    </header>

    <!-- HERO SECTION -->
    <section class="hero">
      <div class="hero-inner">
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
      </div>
    </section>

    <!-- FEATURES SECTION -->
    <section id="features" class="features">
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

/* ───────── NAV BAR - Floating Header ───────── */
.nav-bar {
  position: fixed;
  top: 2rem;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 2rem;
  pointer-events: none;
}

.nav-bar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 94%;
  max-width: 1200px;
  height: 100%;
  background: rgba(8, 8, 11, 0.7);
  border: 1px solid var(--border);
  border-radius: 100px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  pointer-events: auto;
}

.nav-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 94%;
  max-width: 1200px;
  height: 52px;
  padding: 0 1.5rem;
  pointer-events: auto;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  z-index: 2;
}

.nav-brand {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--text-primary);
  cursor: pointer;
  transition: color 0.2s ease;
}

.nav-brand:hover {
  color: var(--accent);
}

.nav-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 2rem;
  z-index: 1;
}

.nav-link {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--text-muted);
  text-decoration: none;
  letter-spacing: 0.02em;
  transition: color 0.2s ease;
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--text-primary);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  z-index: 2;
}

.nav-cta {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #06060a;
  background: var(--text-primary);
  border: none;
  border-radius: 100px;
  padding: 0.5rem 1.25rem;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
  white-space: nowrap;
}

.nav-cta:hover {
  background: #c8c8d0;
  transform: translateY(-1px);
}

.nav-cta:active {
  background: #b0b0ba;
  transform: translateY(0);
}

/* ───────── HERO ───────── */
.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding-top: 100px;
}

.hero-inner {
  position: relative;
  width: 94%;
  max-width: 1200px;
  display: flex;
  align-items: center;
}

.hero-content {
  position: relative;
  z-index: 2;
  max-width: 560px;
  padding-left: 0;
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 1s cubic-bezier(0.16, 1, 0.3, 1), 
              transform 1s cubic-bezier(0.16, 1, 0.3, 1);
}

.hero-content.visible {
  opacity: 1;
  transform: translateY(0);
}

.overline {
  font-family: var(--font-mono);
  font-size: var(--text-label);
  font-weight: var(--weight-medium);
  letter-spacing: 0.12em;
  color: var(--text-muted);
  margin: 0 0 var(--space-lg) 0;
  text-transform: uppercase;
}

.headline {
  font-family: var(--font-sans);
  font-size: var(--text-hero);
  font-weight: var(--weight-bold);
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin: 0 0 var(--space-xl) 0;
}

.headline::after {
  content: '';
  display: block;
  width: 60px;
  height: 3px;
  background: var(--accent);
  margin-top: var(--space-xl);
  border-radius: 2px;
}

.subheadline {
  font-size: var(--text-section-title);
  line-height: 1.7;
  color: var(--text-muted);
  margin: 0 0 var(--space-2xl) 0;
  max-width: 520px;
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
  padding: 0.85rem 2.25rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  letter-spacing: -0.01em;
  box-shadow: 0 8px 24px rgba(232, 232, 237, 0.2);
}

.cta-button:hover {
  background: #c8c8d0;
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(232, 232, 237, 0.3);
}

.cta-button:active {
  background: #b0b0ba;
  transform: translateY(0);
  box-shadow: 0 4px 16px rgba(232, 232, 237, 0.2);
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
  padding: 4rem 2rem;
  max-width: 1100px;
  margin: 0 auto;
  scroll-margin-top: 100px;
}

.section-title {
  font-family: var(--font-mono);
  font-size: var(--text-label);
  font-weight: var(--weight-medium);
  letter-spacing: 0.12em;
  color: var(--text-muted);
  text-transform: uppercase;
  margin: 0 0 var(--space-2xl) 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
  max-width: 1000px;
  margin: 0 auto;
}

.feature-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--space-xl);
}

.feature-icon {
  width: 40px;
  height: 40px;
  color: var(--text-muted);
  margin-bottom: var(--space-lg);
}

.feature-title {
  font-family: var(--font-sans);
  font-size: var(--text-section-title);
  font-weight: var(--weight-bold);
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
}

.feature-desc {
  font-size: var(--text-body);
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
@media (max-width: 968px) {
  .nav-center {
    display: none;
  }
  
  .nav-container {
    width: 90%;
  }
}

@media (max-width: 768px) {
  .nav-bar::before {
    width: 90%;
  }
  
  .nav-container {
    padding: 0 1rem;
  }
  
  .nav-cta {
    font-size: 0.68rem;
    padding: 0.45rem 1rem;
  }

  .hero {
    padding-top: 120px;
  }

  .hero-inner {
    width: 90%;
  }

  .hero-content {
    padding-left: 0;
    padding-right: 0;
  }

  .headline {
    font-size: 2.2rem;
  }

  .subheadline {
    font-size: 0.95rem;
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
}
</style>
