<script setup lang="ts">
import { onMounted, ref } from 'vue'

const emit = defineEmits<{
  (e: 'launch'): void
}>()

const heroVisible = ref(false)
const year = new Date().getFullYear()

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
    <header class="nav-bar">
      <div class="nav-container">
        <div class="nav-left">
          <span class="nav-brand">CHUMBA LABS</span>
        </div>
        <nav class="nav-center" aria-label="Sections">
          <a href="#product" class="nav-link">Products</a>
          <a href="#features" class="nav-link">How it works</a>
          <a href="#why" class="nav-link">Why it matters</a>
          <a href="#company" class="nav-link">Company</a>
          <a
            href="https://github.com/chumbacash/chumba_labs"
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

    <section class="hero">
      <div class="hero-inner">
        <div class="hero-content" :class="{ visible: heroVisible }">
          <p class="overline">Autonomous method development</p>
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
            No account required · Runs locally with optional cloud agent path
          </p>
        </div>

        <svg
          class="chromatogram"
          viewBox="0 0 600 300"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="none"
          aria-hidden="true"
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

    <section id="product" class="product">
      <div class="product-inner">
        <p class="section-title">Products</p>

        <div id="product-method" class="product-block">
          <div class="product-layout">
            <div class="product-copy">
              <p class="product-name">Method Development</p>
              <h2 class="product-heading">
                One agent shell for HPLC and GC-MS method development.
              </h2>
              <p class="product-body">
                Chumba Labs keeps method state structured, calls deterministic
                simulation and scoring tools, and returns auditable proposals your
                chemists can trust enough to take to the bench.
              </p>
              <ul class="product-points">
                <li>HPLC gradient methods with resolution and run-time targets</li>
                <li>SMILES-based analyte input and tool-grounded metrics</li>
                <li>Full agent timeline for every propose → simulate → score cycle</li>
                <li>CSV export for the next confirmatory instrument run</li>
              </ul>
              <button class="cta-button" @click="emit('launch')">Open the workbench</button>
            </div>
            <aside class="product-aside" aria-label="Method development scope">
              <p class="aside-label">In scope</p>
              <p class="aside-text">HPLC method search · GC-MS thin plugin · analyst approval</p>
              <p class="aside-label">Out of scope</p>
              <p class="aside-text">Instrument control · LIMS replace · GxP validation claims</p>
              <p class="aside-note">
                Simulation ranks methods for search. Confirm every method on the
                instrument.
              </p>
            </aside>
          </div>
        </div>

        <div id="product-gateway" class="product-block product-block-secondary">
          <div class="product-layout">
            <div class="product-copy">
              <p class="product-name">Chemistry Data Gateway</p>
              <h2 class="product-heading">
                Ready chemistry data for AI agents.
              </h2>
              <p class="product-body">
                AI agents struggle to pull correct chemistry data from messy,
                incomplete sources. Chemistry Data Gateway delivers curated,
                processed scientific data through a reliable gateway built for
                agent consumption—so models work from ground truth, not guesswork.
              </p>
              <ul class="product-points">
                <li>Processed chemistry data ready for agent workflows</li>
                <li>Consistent, inspectable sources instead of brittle scrapes</li>
                <li>Gateway access designed for AI systems, not just human UIs</li>
              </ul>
            </div>
            <aside class="product-aside" aria-label="Gateway focus">
              <p class="aside-label">Problem</p>
              <p class="aside-text">
                Agents misread or miss chemistry data when sources are raw,
                fragmented, or poorly structured.
              </p>
              <p class="aside-label">What we provide</p>
              <p class="aside-text">
                Agent-ready gateway data—curated, processed, and reliable.
              </p>
            </aside>
          </div>
        </div>
      </div>
    </section>

    <section id="features" class="features">
      <div class="features-inner">
        <p class="section-title">How it works</p>
        <div class="features-grid">
          <div class="feature-card">
            <svg class="feature-icon" viewBox="0 0 40 40" aria-hidden="true">
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
            <svg class="feature-icon" viewBox="0 0 40 40" aria-hidden="true">
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
            <svg class="feature-icon" viewBox="0 0 40 40" aria-hidden="true">
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

    <section id="company" class="company">
      <div class="company-inner">
        <p class="section-title">Company</p>
        <div class="company-layout">
          <div>
            <h2 class="company-heading">
              Analytical agents—and the chemistry data they need.
            </h2>
            <p class="company-body">
              Chumba Labs builds two products for scientific AI. Method
              Development compresses HPLC and GC-MS decision cycles with
              tool-grounded proposals analysts can take to the bench. Chemistry
              Data Gateway gives AI agents curated, processed chemistry data so
              they stop failing on incomplete or incorrect sources.
            </p>
          </div>
          <dl class="company-facts">
            <div>
              <dt>Products</dt>
              <dd>
                Method Development · Chemistry Data Gateway
              </dd>
            </div>
            <div>
              <dt>Focus</dt>
              <dd>
                Separation science agents and agent-ready chemistry data
              </dd>
            </div>
            <div>
              <dt>Approach</dt>
              <dd>Tool-grounded systems with inspectable numbers</dd>
            </div>
            <div>
              <dt>Contact</dt>
              <dd><a href="mailto:hello@chumbalabs.com">hello@chumbalabs.com</a></dd>
            </div>
          </dl>
        </div>
      </div>
    </section>

    <footer class="footer" id="contact">
      <div class="footer-inner">
        <div class="footer-brand">
          <p class="footer-mark">Chumba Labs</p>
          <p class="footer-tagline">
            Method development agents and chemistry data for AI.
            Grounded numbers. Agent-ready data.
          </p>
        </div>

        <div class="footer-cols">
          <div class="footer-col">
            <p class="footer-heading">Products</p>
            <a href="#product-method">Method Development</a>
            <a href="#product-gateway">Chemistry Data Gateway</a>
            <a href="#features">How it works</a>
            <button type="button" class="footer-link-btn" @click="emit('launch')">Workbench</button>
            <a
              href="https://github.com/chumbacash/chumba_labs"
              target="_blank"
              rel="noopener"
              >Open source</a
            >
          </div>
          <div class="footer-col">
            <p class="footer-heading">Company</p>
            <a href="#company">About</a>
            <a href="#why">Why it matters</a>
            <a href="mailto:hello@chumbalabs.com">Contact</a>
          </div>
          <div class="footer-col">
            <p class="footer-heading">Resources</p>
            <a
              href="https://github.com/chumbacash/chumba_labs"
              target="_blank"
              rel="noopener"
              >GitHub</a
            >
            <a
              href="https://github.com/chumbacash/chumba_labs#readme"
              target="_blank"
              rel="noopener"
              >Documentation</a
            >
            <a
              href="https://github.com/chumbacash/chumba_labs/issues"
              target="_blank"
              rel="noopener"
              >Support</a
            >
          </div>
          <div class="footer-col">
            <p class="footer-heading">Legal</p>
            <p class="footer-legal-note">
              Simulation aids method search. Confirm methods on instrument.
              Not a GxP or 21 CFR Part 11 system.
            </p>
          </div>
        </div>

        <div class="footer-bottom">
          <p class="footer-copy">© {{ year }} Chumba Labs. All rights reserved.</p>
          <p class="footer-copy">Built for analytical scientists.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
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

.product,
.features,
.why,
.company {
  border-top: 1px solid var(--border);
  padding: 4rem 1rem;
  scroll-margin-top: 56px;
}

.product,
.company {
  background: var(--bg);
}

.features {
  background: var(--bg-alt);
}

.why {
  background: var(--bg);
}

.product-inner,
.features-inner,
.why-inner,
.company-inner {
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

.product-block {
  scroll-margin-top: 56px;
}

.product-block-secondary {
  margin-top: 3.5rem;
  padding-top: 3.5rem;
  border-top: 1px solid var(--border);
}

.product-layout,
.company-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.8fr);
  gap: 2.5rem;
  align-items: start;
}

.product-name {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0 0 0.75rem 0;
}

.product-heading,
.company-heading {
  font-size: clamp(1.5rem, 2.4vw, 2rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.2;
  margin: 0 0 1rem 0;
}

.product-body,
.company-body {
  font-size: 1rem;
  line-height: 1.7;
  color: var(--text-muted);
  margin: 0 0 1.25rem 0;
  max-width: 42rem;
}

.product-points {
  margin: 0 0 1.75rem 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.65rem;
}

.product-points li {
  position: relative;
  padding-left: 1rem;
  font-size: 0.92rem;
  line-height: 1.55;
  color: var(--text-primary);
}

.product-points li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.55em;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
}

.product-aside {
  background: var(--bg-alt);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem 1.35rem;
}

.aside-label {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 0.35rem 0;
}

.aside-label + .aside-text + .aside-label {
  margin-top: 1.1rem;
}

.aside-text {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.55;
  color: var(--text-primary);
}

.aside-note {
  margin: 1.25rem 0 0 0;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--text-muted);
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

.features .feature-card {
  background: var(--bg);
}

.why .feature-card {
  background: var(--bg-alt);
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

.why-lede {
  font-size: 1.35rem;
  font-weight: 600;
  line-height: 1.45;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  max-width: 640px;
  margin: 0 0 2rem 0;
}

.company-facts {
  margin: 0;
  display: grid;
  gap: 1.1rem;
}

.company-facts div {
  border-top: 1px solid var(--border);
  padding-top: 0.85rem;
}

.company-facts dt {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 0.3rem 0;
}

.company-facts dd {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text-primary);
}

.company-facts a {
  color: var(--accent);
  text-decoration: none;
}

.company-facts a:hover {
  text-decoration: underline;
}

.footer {
  background: #131316;
  color: #d4d4d8;
  padding: 3.5rem 1rem 1.75rem;
}

.footer-inner {
  max-width: 1280px;
  margin: 0 auto;
}

.footer-brand {
  max-width: 28rem;
  margin-bottom: 2.5rem;
}

.footer-mark {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #fff;
  margin: 0 0 0.75rem 0;
}

.footer-tagline {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.6;
  color: #a1a1aa;
}

.footer-cols {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1.75rem;
  padding-bottom: 2.25rem;
  border-bottom: 1px solid #2b2b31;
}

.footer-heading {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #fff;
  margin: 0 0 0.9rem 0;
}

.footer-col {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.55rem;
}

.footer-col a,
.footer-link-btn {
  font-size: 0.88rem;
  color: #a1a1aa;
  text-decoration: none;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
}

.footer-col a:hover,
.footer-link-btn:hover {
  color: #fff;
}

.footer-legal-note {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.55;
  color: #8e8e96;
  max-width: 18rem;
}

.footer-bottom {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  padding-top: 1.25rem;
}

.footer-copy {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  letter-spacing: 0.02em;
  color: #71717a;
}

@media (max-width: 968px) {
  .nav-center {
    display: none;
  }

  .product-layout,
  .company-layout,
  .footer-cols {
    grid-template-columns: 1fr 1fr;
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

  .product,
  .features,
  .why,
  .company {
    padding: 3rem 1.5rem;
  }

  .features-grid,
  .product-layout,
  .company-layout,
  .footer-cols {
    grid-template-columns: 1fr;
  }

  .why-lede {
    font-size: 1.1rem;
  }

  .chromatogram {
    width: 90%;
    opacity: 0.08;
  }

  .footer {
    padding: 3rem 1.5rem 1.5rem;
  }

  .footer-bottom {
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-content {
    opacity: 1;
    transform: none;
    transition: none;
  }
}
</style>
