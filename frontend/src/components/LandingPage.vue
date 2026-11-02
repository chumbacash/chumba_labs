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
        <nav class="nav-center" aria-label="Sections">
          <a href="#features" class="nav-link">How it works</a>
          <a href="#why" class="nav-link">Why it matters</a>
          <a
            href="https://github.com/chumba-labs"
            target="_blank"
            rel="noopener"
            class="nav-link"
            >GitHub</a
          >
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
            methods. The analyst approves the next experiment. The model does
            the guessing.
          </p>
          <button class="cta-button" @click="emit('launch')">
            Launch workbench
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
            stroke="#0e7490"
            stroke-width="1.5"
          />
          <polyline
            :points="peak1Points"
            fill="none"
            stroke="#0e7490"
            stroke-width="1.5"
          />
          <polyline
            :points="peak2Points"
            fill="none"
            stroke="#b45309"
            stroke-width="1.5"
          />
          <polyline
            :points="peak3Points"
            fill="none"
            stroke="#be123c"
            stroke-width="1.5"
          />
        </svg>
      </div>
    </section>

    <!-- FEATURES SECTION -->
    <section id="features" class="features">
      <div class="features-inner">
      <p class="section-title">How it works</p>
      <div class="features-grid">
        <div class="feature-card">
          <svg class="feature-icon" viewBox="0 0 40 40">
            <circle cx="20" cy="20" r="19" fill="none" stroke="currentColor" stroke-width="1" />
            <text x="20" y="25" text-anchor="middle" fill="currentColor" font-size="16" font-family="'SF Mono', 'IBM Plex Mono', ui-monospace, monospace">1</text>
          </svg>
          <h3 class="feature-title">Propose</h3>
          <p class="feature-desc">
            Agent generates HPLC method parameters (column, gradient, flow,
            temperature) within instrument constraints.
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
      </div>
    </section>

    <!-- WHY IT MATTERS SECTION -->
    <section id="why" class="why">
      <div class="why-inner">
        <p class="section-title">Why it matters</p>
        <p class="why-lede">
          Every new impurity ends the same way: an analyst in front of an
          HPLC, guessing at gradients.
        </p>
        <div class="features-grid">
          <div class="feature-card">
            <h3 class="feature-title">The bottleneck</h3>
            <p class="feature-desc">
              A robust separation can take weeks of trial runs. The know-how
              lives in experts' heads, so labs without one wait, outsource,
              or settle for fragile methods.
            </p>
          </div>
          <div class="feature-card">
            <h3 class="feature-title">The shift</h3>
            <p class="feature-desc">
              The agent proposes inside real constraints, simulates in
              seconds, and scores against your targets. Every tool call is
              shown. The chemist approves the next run.
            </p>
          </div>
          <div class="feature-card">
            <h3 class="feature-title">The bigger picture</h3>
            <p class="feature-desc">
              Pharma QC, food safety, environmental, forensics. Every
              analytical lab hits the same wall. One verifiable loop serves
              them all.
            </p>
          </div>
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
  --bg: #fafafa;
  --bg-alt: #ffffff;
  --text-primary: #131316;
  --text-muted: #5b5b64;
  --accent: #0e7490;
  --surface: #f4f4f5;
  --border: #e7e7ea;
  --font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI',
    system-ui, sans-serif;
  --font-mono: 'IBM Plex Mono', ui-monospace, 'SF Mono', monospace;

  background: var(--bg);
  color: var(--text-primary);
  font-family: var(--font-sans);
  min-height: 100vh;
  overflow-x: hidden;
}

/* ───────── NAV BAR, same language as the workbench header ───────── */
.nav-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(250, 250, 250, 0.92);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.nav-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  max-width: 1280px;
  height: 56px;
  margin: 0 auto;
  padding: 0 1rem;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.nav-brand {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--text-primary);
}

.nav-center {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin: 0 auto;
}

.nav-link {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  text-decoration: none;
  letter-spacing: 0.04em;
  padding: 6px 10px;
  border-radius: 999px;
  transition: color 0.15s ease, background 0.15s ease;
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--surface);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: auto;
}

.nav-cta {
  font-family: var(--font-sans);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: #fff;
  background: var(--text-primary);
  border: 1px solid var(--text-primary);
  border-radius: 999px;
  padding: 0.5rem 1.25rem;
  cursor: pointer;
  transition: background 0.15s ease;
  white-space: nowrap;
}

.nav-cta:hover {
  background: #2b2b31;
  border-color: #2b2b31;
}

/* ───────── HERO ───────── */
.hero {
  position: relative;
  min-height: calc(100vh - 56px);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.hero-inner {
  position: relative;
  width: 100%;
  max-width: 1280px;
  padding: 0 1rem;
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
  font-size: 0.9rem;
  font-weight: 600;
  color: #fff;
  background: var(--text-primary);
  border: 1px solid var(--text-primary);
  border-radius: 999px;
  padding: 0.8rem 2rem;
  cursor: pointer;
  transition: background 0.15s ease;
  letter-spacing: -0.01em;
}

.cta-button:hover {
  background: #2b2b31;
  border-color: #2b2b31;
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
  opacity: 0.35;
  pointer-events: none;
  z-index: 1;
}

/* ───────── FEATURES ───────── */
.features {
  background: var(--bg-alt);
  border-top: 1px solid var(--border);
  padding: 4rem 1rem;
  scroll-margin-top: 56px;
}

.features-inner {
  max-width: 1280px;
  margin: 0 auto;
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
}

.feature-card {
  background: var(--bg);
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

/* ───────── WHY IT MATTERS ───────── */
.why {
  background: var(--bg);
  border-top: 1px solid var(--border);
  padding: 4rem 1rem;
  scroll-margin-top: 56px;
}

.why-inner {
  max-width: 1280px;
  margin: 0 auto;
}

.why-lede {
  font-size: 1.35rem;
  font-weight: 600;
  line-height: 1.45;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  max-width: 640px;
  margin: 0 0 2rem 0;
}

.why .features-grid {
  margin-bottom: 0;
}

/* ───────── FOOTER ───────── */
.footer {
  background: var(--bg-alt);
  border-top: 1px solid var(--border);
  padding: 2.5rem 1rem;
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
}

@media (max-width: 768px) {
  .nav-cta {
    font-size: 0.68rem;
    padding: 0.45rem 1rem;
  }

  .hero-inner {
    width: 100%;
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

  .why-lede {
    font-size: 1.1rem;
  }

  .chromatogram {
    width: 90%;
    opacity: 0.08;
  }
}
</style>
