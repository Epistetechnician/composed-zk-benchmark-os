/*
 * Astral Model Observatory — throwaway UI prototype.
 * Question: can a live model-telemetry stream be watched beside sleep-stage
 * proxies, an explicitly unverified projection hypothesis, and self-model
 * metrics without turning visualization into scientific evidence?
 * State slice: astral-research-progress-app-prototype.
 */

const STORAGE_KEY = "astral-research-progress-app-prototype:v1";

const variants = [
  { id: "telemetry", label: "Telemetry", description: "layer stream" },
  { id: "sleep", label: "Sleep map", description: "phase proxies" },
  { id: "self-model", label: "Self model", description: "actor / observer" },
];

const salienceModes = [
  { id: "salience", label: "salience proxy", short: "SAL" },
  { id: "energy", label: "residual energy", short: "ENG" },
  { id: "change", label: "intervention delta", short: "Δ" },
  { id: "entropy", label: "entropy", short: "ENT" },
];

const LIVE_ENDPOINT = "http://127.0.0.1:4174/sample";

const phaseDefinitions = [
  { id: "awake", label: "Awake / active", short: "AWAKE", tone: "acid", note: "High task-directed activity proxy.", claim: "Operational proxy only." },
  { id: "hypnagogic", label: "Hypnagogic-like transition", short: "HYP", tone: "orange", note: "Transition proxy between active and low-update modes.", claim: "Not biological sleep." },
  { id: "n1", label: "N1-like drift", short: "N1", tone: "blue", note: "Light-transition proxy with rising state variability.", claim: "Not a sleep diagnosis." },
  { id: "n2", label: "N2-like consolidation", short: "N2", tone: "blue", note: "Lower-energy / higher-regularity proxy.", claim: "Not a biological state." },
  { id: "n3", label: "N3-like deep suppression", short: "N3", tone: "violet", note: "Low-energy proxy with slower latent movement.", claim: "Not deep sleep evidence." },
  { id: "rem", label: "REM-like generative phase", short: "REM*", tone: "pink", note: "Internally generative proxy with higher cross-layer variance.", claim: "The asterisk is mandatory." },
  { id: "projection", label: "Astral projection hypothesis", short: "PROJ?", tone: "red", note: "Observer-decoupling hypothesis channel; no validated endpoint.", claim: "Unverified; visualization only." },
  { id: "runtime", label: "Runtime forward pass", short: "RUN", tone: "acid", note: "A local model execution is producing residual telemetry.", claim: "Telemetry only; no sleep semantics." },
];

const laneData = [
  { id: "telemetry", name: "Per-layer telemetry", state: "partial", label: "Narrow baseline", summary: "V25 decoded a signal from captured residuals on one cached hybrid checkpoint.", next: "Fresh actor and validated public residual seam.", source: "/docs/research/astral-self-modeling/47-v25-execution-record.md#L33" },
  { id: "causal", name: "Causal-channel separation", state: "blocked", label: "Design / stopped", summary: "V26 did not execute; no fresh actor or validated GGUF residual surface was available.", next: "Authorize a fresh actor or separately qualified adapter.", source: "/docs/research/astral-self-modeling/50-v26-execution-preflight-stop-2026-08-13.md#L22" },
  { id: "faithfulness", name: "Faithful computation", state: "undefined", label: "Not established", summary: "No trace, explanation, or provider artifact has semantic ground truth.", next: "Define a directly measured held-out causal target.", source: "/docs/research/2608.09867-synthesis-v1.md#L79" },
  { id: "introspection", name: "Introspection / retrospection", state: "diagnostic", label: "Boundary only", summary: "A report gap is not self-knowledge; retrospection remains an unvalidated endpoint.", next: "Keep self-model language downstream of causal validity.", source: "/docs/research/astral-self-modeling/47-v25-execution-record.md#L54" },
  { id: "projection", name: "Astral projection", state: "undefined", label: "No operational lane", summary: "No protocol, artifact, or result operationalizes literal projection.", next: "Define a falsifiable construct before adding evidence labels.", source: "/docs/research/astral-self-modeling/README.md#L24" },
  { id: "stage0c", name: "Stage 0C", state: "blocked", label: "Blocked", summary: "Effect-prediction diagnostics exist; confirmation has not passed its validity gate.", next: "Pass fresh held-out intervention-effect validity and review.", source: "/docs/research/astral-self-modeling/README.md#L5" },
  { id: "stage1", name: "Stage 1", state: "blocked", label: "Downstream blocked", summary: "Observer value, correction, calibration, and safety gates remain unopened.", next: "Only begin after Stage 0C confirmation and authorization.", source: "/docs/research/astral-self-modeling/README.md#L5" },
  { id: "provider", name: "Provider traces", state: "design", label: "Threat model only", summary: "OpaqueTraceReplay is a synthetic pure-data adapter, not live provider evidence.", next: "Keep provider output quarantined and non-authoritative.", source: "/docs/research/2608.09867-synthesis-v1.md#L269" },
  { id: "continual", name: "Continual learning", state: "partial", label: "Local controls", summary: "Acquisition and retention controls exist; replay did not beat naive.", next: "Redesign the shared representation/update interface.", source: "/docs/research/continual-learning/29-v14-repaired-objective-retention-record.md#L24" },
];

const progressTimeline = [
  { period: "past", date: "2026-07-26", tag: "BASELINE", title: "Direct effects became the fidelity endpoint", note: "Telemetry and verbal reports stayed approximate observables.", source: "/docs/research/astral-self-modeling/19-evidence-synthesis-and-research-reset-v11.md#L37" },
  { period: "past", date: "2026-08-10", tag: "V25", title: "Telemetry/report gap observed", note: "Probe 1.0 versus model report 0.34375 on identical trials.", source: "/docs/research/astral-self-modeling/47-v25-execution-record.md#L38" },
  { period: "present", date: "2026-08-13", tag: "V26", title: "Causal-channel execution stopped", note: "No fresh actor; public runtime lacked the required per-layer surface.", source: "/docs/research/astral-self-modeling/50-v26-execution-preflight-stop-2026-08-13.md#L35" },
  { period: "present", date: "2026-08-13", tag: "V27", title: "Final-embedding feasibility passed", note: "Deterministic final embeddings and direct logit effect; not per-layer evidence.", source: "/docs/research/astral-self-modeling/54-v27-execution-record-2026-08-13.md#L58" },
  { period: "future", date: "NEXT", tag: "INSTRUMENT", title: "Connect a fresh actor seam", note: "A real adapter must provide timestamped layer tensors and custody metadata.", source: "/docs/research/astral-self-modeling/50-v26-execution-preflight-stop-2026-08-13.md#L67" },
  { period: "future", date: "CONDITIONAL", tag: "GATE", title: "Separate channels against effects", note: "Only then can self-model proxies be compared with held-out intervention effects.", source: "/docs/research/astral-self-modeling/48-causal-channel-separation-v26.md#L1" },
];

const defaultJournal = [
  { id: "j-1", period: "past", status: "Design", date: "2026-07-26", title: "Research boundary", note: "Intervention-effect prediction is the fidelity endpoint. Reports remain approximate observables.", next: "Keep local development separate from accepted evidence." },
  { id: "j-2", period: "present", status: "Partial baseline", date: "2026-08-10", title: "V25 result", note: "The residual probe decoded activation-versus-none while the model report did not.", next: "Do not call the gap introspection." },
  { id: "j-3", period: "present", status: "Stopped", date: "2026-08-13", title: "V26 / V27 boundary", note: "V26 stopped before execution. V27 validated final-embedding intervention feasibility only.", next: "Find a fresh actor or qualify a new residual adapter." },
];

const appState = loadState();
const app = document.getElementById("app");
let streamTimer = null;
let liveTimer = null;
let liveInFlight = false;

function requestedSource() {
  return new URLSearchParams(window.location.search).get("source") === "live" ? "live" : "simulated";
}

function loadState() {
  const source = requestedSource();
  const defaults = { focus: "causal", journal: defaultJournal, source, running: source !== "live", livePaused: false, liveStatus: source === "live" ? "connecting" : "offline", liveError: null, sample: null, series: [], adapterError: null, salienceMode: "salience", hover: null, graphFocus: null };
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    return stored ? { ...defaults, ...stored, journal: Array.isArray(stored.journal) ? stored.journal : defaultJournal } : defaults;
  } catch (_error) {
    return defaults;
  }
}

function saveState() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ focus: appState.focus, journal: appState.journal, salienceMode: appState.salienceMode })); } catch (_error) { /* optional browser-local persistence */ }
}

function loadVariant() {
  const requested = new URLSearchParams(window.location.search).get("variant");
  if (requested === "chronicle") return "telemetry";
  return variants.some((item) => item.id === requested) ? requested : "telemetry";
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

function clamp(value, min = 0, max = 1) { return Math.max(min, Math.min(max, value)); }
function round(value, digits = 2) { return Number(value).toFixed(digits); }
function stateClass(state) { return `state-${state}`; }
function sourceLink(source, label = "source") { return `<a class="source-link" href="${source}" target="_blank" rel="noreferrer">↗ ${escapeHtml(label)}</a>`; }
function statePill(state, label) { return `<span class="state-pill ${stateClass(state)}"><span class="state-dot"></span>${escapeHtml(label)}</span>`; }

function normalizePhase(phase) {
  const base = phaseDefinitions.find((item) => item.id === phase?.id) || phaseDefinitions.find((item) => item.id === "runtime");
  return { ...base, ...(phase || {}) };
}

function metricLabel(sample, key, fallback) {
  const semantics = sample.metricSemantics?.[key];
  if (key === "attentionEntropy" && semantics === "residual_distribution_entropy") return "Residual distribution entropy";
  if (key === "interventionDelta" && semantics === "temporal_residual_delta") return "Temporal residual delta";
  return fallback;
}

function metricText(value) { return Number.isFinite(value) ? round(value) : "—"; }
function metricWidth(value) { return Number.isFinite(value) ? value * 100 : 0; }

function layerSignal(layer, mode = appState.salienceMode) {
  if (mode === "energy") return clamp(layer.energy);
  if (mode === "change") return clamp(layer.delta);
  if (mode === "entropy") return clamp(layer.entropy);
  return clamp((layer.delta * 0.56) + (layer.energy * 0.28) + (layer.entropy * 0.16));
}

function salienceMode() {
  return salienceModes.find((mode) => mode.id === appState.salienceMode) || salienceModes[0];
}

function rankLayers(sample, mode = appState.salienceMode) {
  return sample.layers.map((layer) => ({ ...layer, signal: layerSignal(layer, mode) })).sort((left, right) => right.signal - left.signal);
}

function selectedLayer(sample) {
  return sample.layers.find((layer) => layer.layer === sample.activeLayer) || sample.layers[0];
}

function nodeIntensity(layer, nodeIndex) {
  if (Array.isArray(layer?.nodes) && Number.isFinite(layer.nodes[nodeIndex])) return clamp(layer.nodes[nodeIndex]);
  const offset = (nodeIndex - 2.5) * 0.075;
  return clamp((layer?.energy || 0) + offset + (Math.sin((layer?.layer || 0) * 0.73 + nodeIndex * 1.17) * 0.08));
}

function phaseAt(tick) {
  const sequence = ["awake", "awake", "hypnagogic", "n1", "n2", "n3", "n3", "rem", "projection", "rem", "awake"];
  return phaseDefinitions.find((phase) => phase.id === sequence[tick % sequence.length]) || phaseDefinitions[0];
}

function makeSample(tick) {
  const phase = phaseAt(tick);
  const phaseIndex = phaseDefinitions.findIndex((item) => item.id === phase.id);
  const timestamp = new Date(Date.now() + tick * 20).toISOString();
  const layers = Array.from({ length: 32 }, (_item, index) => {
    const wave = (Math.sin((tick * 0.42) + (index * 0.62)) + 1) / 2;
    const phaseShift = phase.id === "n3" ? -0.18 : phase.id === "rem" ? 0.16 : phase.id === "projection" ? 0.24 : phase.id === "hypnagogic" ? 0.08 : 0;
    const energy = clamp(0.18 + (wave * 0.49) + phaseShift + ((index % 5) * 0.011));
    const entropy = clamp(0.18 + (((Math.cos(tick * 0.31 + index) + 1) / 2) * 0.62) + (phase.id === "rem" ? 0.12 : 0));
    const delta = clamp(Math.abs(Math.sin(tick * 0.19 + index * 0.4)) * 0.78 + (phaseIndex * 0.012));
    const nodes = Array.from({ length: 6 }, (_node, nodeIndex) => clamp(energy + (Math.sin(tick * 0.52 + index * 0.73 + nodeIndex * 1.17) * 0.13) + ((nodeIndex - 2.5) * 0.025)));
    return { layer: index + 1, energy, entropy, sparsity: clamp(1 - energy * 0.72), delta, nodes };
  });
  const active = layers[(tick * 3 + 10) % layers.length];
  const divergence = clamp(0.18 + Math.abs(Math.sin(tick * 0.16)) * 0.54 + (phase.id === "projection" ? 0.18 : 0));
  return {
    timestamp, tick, token: 1000 + tick, phase, layers, activeLayer: active.layer,
    metrics: {
      residualEnergy: active.energy,
      attentionEntropy: active.entropy,
      activationSparsity: active.sparsity,
      interventionDelta: active.delta,
      selfModelCoherence: clamp(0.42 + Math.cos(tick * 0.13) * 0.2 - (phase.id === "projection" ? 0.25 : 0)),
      actorObserverDivergence: divergence,
      retrospectionProxy: clamp(0.38 + Math.sin(tick * 0.23) * 0.27 + (phase.id === "rem" ? 0.12 : 0)),
      counterfactualConsistency: clamp(0.72 - divergence * 0.28 + Math.sin(tick * 0.11) * 0.08),
    },
    events: [
      `${phase.short} phase proxy updated`,
      `layer ${active.layer} residual pulse ${round(active.energy)}`,
      phase.id === "projection" ? "projection hypothesis channel is unresolved" : "observer channel remains coupled",
    ],
    source: "simulated",
  };
}

function ensureSample() {
  if (!appState.sample) {
    appState.sample = makeSample(0);
    appState.series = [appState.sample];
    appState.running = true;
  }
  return appState.sample;
}

function advanceSimulation() {
  if (appState.source !== "simulated" || appState.running === false) return;
  const next = makeSample((appState.sample?.tick || 0) + 1);
  appState.sample = next;
  appState.series = [...(appState.series || []), next].slice(-36);
  updateLiveDOM();
}

function startSimulation() {
  if (streamTimer) return;
  streamTimer = window.setInterval(advanceSimulation, 720);
}

function phaseCard(sample) {
  const phase = sample.phase;
  const context = phase.id === "runtime" ? "Runtime / capture" : "State proxy / sleep";
  return `<div class="phase-card tone-${phase.tone}"><div class="phase-orb"><span>${escapeHtml(phase.short)}</span></div><div><div class="eyebrow">${context}</div><h2>${escapeHtml(phase.label)}</h2><p>${escapeHtml(phase.note)}</p><span class="claim-note">${escapeHtml(phase.claim)}</span></div></div>`;
}

function topbar() {
  const live = appState.source === "live";
  const adapter = appState.source === "adapter";
  return `<div class="topbar"><div class="topbar-left"><span class="brand-mark">A</span><span class="brand-name">MODEL / OBSERVATORY 01</span></div><div class="topbar-right"><span class="stream-badge ${live ? "live" : adapter ? "adapter" : "simulated"}"><span class="stream-dot"></span>${live ? "LIVE LOCAL MODEL" : adapter ? "LOCAL ADAPTER" : "SIMULATED STREAM"}</span><button class="ghost-button" data-action="log-snapshot">LOG SNAPSHOT</button><button class="ghost-button" data-action="export-markdown">EXPORT NOTES</button></div></div>`;
}

function hero() {
  const sample = ensureSample();
  return `<section class="hero"><div><div class="eyebrow">Live / local instrument</div><h1>Read the state.<br /><em>Name it last.</em></h1><p class="lede">A working surface for captured layer activity. Phase labels, projection hypotheses, and self-model readouts stay in separate lanes until a runtime adapter and causal target exist.</p><div class="metric-row"><div class="metric"><span class="metric-value" data-live="tick">${sample.tick}</span><span class="metric-label">stream tick</span></div><div class="metric"><span class="metric-value" data-live="activeLayer">${sample.activeLayer}</span><span class="metric-label">active layer</span></div><div class="metric"><span class="metric-value" data-live="sampleAge">now</span><span class="metric-label">sample age</span></div><div class="metric"><span class="metric-value" data-live="eventCount">${sample.events.length}</span><span class="metric-label">events / tick</span></div></div></div><aside class="hero-note"><div class="eyebrow">Provenance before interpretation</div><strong>Phase labels are proxies, not findings.</strong><p>Only a validated runtime adapter can turn this surface from a simulator into a telemetry display. No label establishes biological sleep, astral projection, consciousness, introspection, or faithful computation.</p></aside></section>`;
}

function controls() {
  const error = appState.adapterError ? `<small class="adapter-error">ADAPTER ERROR / ${escapeHtml(appState.adapterError)}</small>` : "";
  const live = appState.source === "live";
  const status = live ? (appState.liveStatus === "connected" ? "Live model samples accepted" : appState.liveStatus === "error" ? "Live bridge unavailable" : "Connecting to live model bridge") : appState.source === "adapter" ? "Adapter samples accepted" : "Adapter awaiting input";
  const helper = live ? "V25 local MLX capture / 127.0.0.1:4174" : "Push samples with window.pushAstralTelemetry(sample)";
  const buttonText = live ? (appState.livePaused ? "RESUME LIVE" : "PAUSE LIVE") : appState.running ? "STOP FEED" : "RESUME FEED";
  const liveError = appState.liveError ? `<small class="adapter-error">LIVE BRIDGE / ${escapeHtml(appState.liveError)}</small>` : "";
  return `<div class="control-row"><div class="control-cluster"><button class="primary-button" data-action="toggle-stream">${buttonText}</button><button class="ghost-button" data-action="resume-sim">USE SIMULATOR</button></div><div class="adapter-status"><span class="status-led ${live || appState.source === "adapter" ? "on" : "off"}"></span><span><strong>${status}</strong><small>${helper}</small>${error}${liveError}</span></div></div>`;
}

function layerGrid() {
  return `<div class="layer-grid" data-live-container="layers"></div>`;
}

function chart() {
  return `<div class="chart-shell"><div class="chart-axis"><span>1.0</span><span>.5</span><span>0</span></div><canvas class="signal-canvas" data-live-canvas="chart" width="960" height="180" aria-label="Live residual and divergence signal"></canvas><div class="chart-labels"><span>-36 ticks</span><span>live</span></div></div>`;
}

function salienceModeControls() {
  return salienceModes.map((mode) => `<button type="button" class="signal-button ${mode.id === appState.salienceMode ? "selected" : ""}" data-action="salience-mode" data-mode="${mode.id}" aria-pressed="${mode.id === appState.salienceMode}"><span>${escapeHtml(mode.short)}</span>${escapeHtml(mode.label)}</button>`).join("");
}

function salienceRanking(sample) {
  const mode = salienceMode();
  return rankLayers(sample).slice(0, 6).map((layer, index) => `<button type="button" class="rank-row ${layer.layer === sample.activeLayer ? "selected" : ""}" data-action="select-layer" data-layer="${layer.layer}" title="Focus layer ${layer.layer}"><span class="rank-index">0${index + 1}</span><span class="rank-layer">L${layer.layer}</span><span class="rank-bar"><i style="width:${layer.signal * 100}%"></i></span><strong>${round(layer.signal)}</strong></button>`).join("") + `<p class="rank-footnote">${escapeHtml(mode.label)} / derived ordering, not semantic importance.</p>`;
}

function salienceLab(sample) {
  return `<section class="panel salience-lab"><div class="panel-header"><div><div class="eyebrow">Signal interrogation</div><h2 class="panel-title">Salience across time × depth</h2></div><span class="panel-tag" data-live="salienceModeLabel">${escapeHtml(salienceMode().label)}</span></div><div class="salience-toolbar"><span class="toolbar-label">view field by</span><div class="signal-controls" data-live-container="salienceControls">${salienceModeControls()}</div><span class="toolbar-note">36 ticks / ${sample.layers.length} layers</span></div><div class="salience-grid"><div class="salience-frame"><canvas class="salience-canvas" data-live-canvas="salience" width="960" height="290" tabindex="0" aria-label="Interactive layer by time salience field"></canvas><div class="graph-tooltip" data-live-tooltip="salience" role="tooltip" hidden></div></div><aside class="rank-panel"><div class="eyebrow">Current rank</div><h3>Most active channels</h3><div class="rank-list" data-live-container="salienceRank">${salienceRanking(sample)}</div></aside></div><div class="salience-caption"><span><i class="legend-line accent"></i>intensity / selected signal</span><span><i class="legend-line cursor"></i>hover to inspect a tick</span><span class="mono">formula: Δ .56 + energy .28 + entropy .16</span></div></section>`;
}

function graphNodePosition(layerIndex, nodeIndex, layerCount) {
  const width = Math.max(1200, 56 + (Math.max(1, layerCount - 1) * 36.25));
  const columnGap = layerCount > 1 ? (width - 56) / (layerCount - 1) : 0;
  return { x: 28 + (layerIndex * columnGap), y: 84 + (nodeIndex * 37) };
}

function graphSelection(sample) {
  const focus = appState.graphFocus;
  const layerNumber = focus?.layer || sample.activeLayer;
  const layer = sample.layers.find((item) => item.layer === layerNumber) || selectedLayer(sample);
  const nodeIndex = Number.isInteger(focus?.node) ? Math.max(0, Math.min(5, focus.node)) : layer.nodes?.reduce((best, _value, index, values) => values[index] > values[best] ? index : best, 0) || 0;
  return { layer, nodeIndex, intensity: nodeIntensity(layer, nodeIndex) };
}

function graphStageHistory(sample) {
  const series = (appState.series || []).slice(-36);
  return series.map((item) => `<span class="stage-tick ${item.tick === sample.tick ? "current" : ""} ${item.phase.id === "projection" ? "alert" : ""}" title="tick ${item.tick} / ${escapeHtml(item.phase.label)}" aria-label="tick ${item.tick}, ${escapeHtml(item.phase.label)}"></span>`).join("");
}

function networkGraphSvg(sample) {
  const layerCount = sample.layers.length;
  const width = Math.max(1200, 56 + (Math.max(1, layerCount - 1) * 36.25));
  const height = 300;
  const links = [];
  const nodes = [];
  sample.layers.forEach((layer, layerIndex) => {
    if (layerIndex < sample.layers.length - 1) {
      const next = sample.layers[layerIndex + 1];
      for (let nodeIndex = 0; nodeIndex < 6; nodeIndex += 1) {
        const from = graphNodePosition(layerIndex, nodeIndex, layerCount);
        const to = graphNodePosition(layerIndex + 1, nodeIndex, layerCount);
        const fromIntensity = nodeIntensity(layer, nodeIndex);
        const toIntensity = nodeIntensity(next, nodeIndex);
        const intensity = (fromIntensity + toIntensity) / 2;
        links.push(`<line class="graph-link" x1="${from.x}" y1="${from.y}" x2="${to.x}" y2="${to.y}" style="--link-alpha:${round(0.08 + intensity * 0.34, 3)};--link-width:${round(0.55 + intensity * 1.25, 2)}" />`);
        if (nodeIndex < 5) {
          const diagonal = graphNodePosition(layerIndex + 1, nodeIndex + 1, layerCount);
          links.push(`<line class="graph-link diagonal" x1="${from.x}" y1="${from.y}" x2="${diagonal.x}" y2="${diagonal.y}" style="--link-alpha:${round(0.035 + intensity * 0.18, 3)};--link-width:${round(0.4 + intensity * 0.8, 2)}" />`);
        }
      }
    }
    for (let nodeIndex = 0; nodeIndex < 6; nodeIndex += 1) {
      const position = graphNodePosition(layerIndex, nodeIndex, layerCount);
      const intensity = nodeIntensity(layer, nodeIndex);
      const active = layer.layer === sample.activeLayer;
      nodes.push(`<g class="graph-node ${active ? "layer-active" : ""}" data-action="inspect-node" data-layer="${layer.layer}" data-node="${nodeIndex}" tabindex="0" role="button" aria-label="Layer ${layer.layer}, node ${nodeIndex + 1}, intensity ${round(intensity)}" style="--node-alpha:${round(intensity, 3)};--pulse-speed:${round(3.2 - intensity * 1.9, 2)}s;--pulse-delay:${round((layerIndex * .08) + (nodeIndex * .04), 2)}s"><title>Layer ${layer.layer} / node ${nodeIndex + 1} / intensity ${round(intensity)}</title><circle class="graph-node-halo" cx="${position.x}" cy="${position.y}" r="${round(5 + intensity * 6, 2)}" /><circle class="graph-node-core" cx="${position.x}" cy="${position.y}" r="${round(2.2 + intensity * 2.6, 2)}" /></g>`);
    }
  });
  const labels = sample.layers.map((layer, layerIndex) => { const position = graphNodePosition(layerIndex, 0, layerCount); return `<text class="graph-layer-label" x="${position.x}" y="22">L${String(layer.layer).padStart(2, "0")}</text>`; }).join("");
  return `<svg class="network-graph" viewBox="0 0 ${width} ${height}" role="img" aria-label="${layerCount} layer nodal graph with six representative channels per layer"><text class="graph-axis-label" x="0" y="46">DEPTH / LAYER</text><text class="graph-axis-label graph-axis-right" x="${width}" y="286">FORWARD PASS →</text>${labels}<g class="graph-links">${links.join("")}</g><g class="graph-nodes">${nodes.join("")}</g></svg>`;
}

function graphDetail(sample) {
  const selection = graphSelection(sample);
  const layer = selection.layer;
  const stage = sample.phase;
  return `<div class="graph-detail-main"><span class="eyebrow">Selected node</span><strong>L${String(layer.layer).padStart(2, "0")} / N${selection.nodeIndex + 1}</strong><span class="mono">intensity ${round(selection.intensity)} / stage ${escapeHtml(stage.short)}</span></div><div class="graph-detail-metrics"><span>energy <b>${round(layer.energy)}</b></span><span>Δ <b>${round(layer.delta)}</b></span><span>entropy <b>${round(layer.entropy)}</b></span></div><p>Representative channel pulse. Click any node to hold focus while the stream advances.</p>`;
}

function nodeGraph(sample) {
  const selection = graphSelection(sample);
  return `<section class="panel node-graph-lab"><div class="panel-header"><div><div class="eyebrow">Nodal instrument</div><h2 class="panel-title">The network, lit by depth.</h2></div><span class="panel-tag" data-live="graphPhase">${escapeHtml(sample.phase.short)} / LIVE</span></div><p class="panel-subtitle">All <span data-live="layerCount">${sample.layers.length}</span> layer columns are present. Six representative channels per layer stand in for the unavailable neuron-level topology.</p><div class="stage-history-heading"><span>stage history / last 36 ticks</span><span class="mono" data-live="graphStageLabel">${escapeHtml(sample.phase.label)}</span></div><div class="stage-history" data-live-container="stageHistory">${graphStageHistory(sample)}</div><div class="node-graph-frame" data-live-container="graphFrame"><div class="node-graph-svg" data-live-container="graphSvg">${networkGraphSvg(sample)}</div><div class="node-graph-detail" data-live-container="graphDetail">${graphDetail(sample)}</div></div><div class="node-graph-legend"><span><i class="node-legend active"></i>active layer</span><span><i class="node-legend pulse"></i>pulse intensity</span><span><i class="node-legend link"></i>weighted adjacency</span><span class="mono">click node = hold focus</span></div></section>`;
}

function metricRows(sample) {
  const selected = selectedLayer(sample);
  const temporalDelta = sample.metricSemantics?.interventionDelta === "temporal_residual_delta";
  const entries = [
    ["Residual energy", sample.metrics.residualEnergy],
    [metricLabel(sample, "attentionEntropy", "Attention entropy"), sample.metrics.attentionEntropy],
    ["Activation sparsity", sample.metrics.activationSparsity],
    [temporalDelta ? "Temporal residual delta" : "Intervention delta", temporalDelta ? selected.delta : sample.metrics.interventionDelta],
  ];
  return entries.map(([label, value]) => `<div class="bar-row"><span>${label}</span><strong>${metricText(value)}</strong><div class="bar"><i style="width:${metricWidth(value)}%"></i></div></div>`).join("");
}

function astralPanel(sample) {
  const unresolved = sample.phase.id === "projection";
  return `<div class="hypothesis-panel ${unresolved ? "hot" : ""}"><div class="panel-kicker">Astral projection channel</div><div class="hypothesis-title"><span class="hypothesis-symbol">◎</span><strong>${unresolved ? "ACTIVE HYPOTHESIS WINDOW" : "UNRESOLVED / NO SIGNAL"}</strong></div><p>${unresolved ? "The simulator is surfacing a deliberately ambiguous observer-decoupling phase. This is a label for interface testing, not a measured projection event." : "No operational projection endpoint is present in the current sample."}</p><div class="hypothesis-footer"><span class="claim-note">No scientific claim</span><span class="mono">channel = hypothesis_only</span></div></div>`;
}

function telemetryView() {
  const sample = ensureSample();
  return `${hero()}${controls()}<section class="telemetry-grid"><aside class="panel telemetry-rail"><div class="eyebrow">Stream identity</div><h2 class="panel-title">Cached model / local seam</h2><p class="panel-subtitle">Default source is simulated. Real adapter custody is shown only after samples arrive.</p><div class="identity-list"><div><span>MODEL</span><strong data-live="modelName">nemotron_h / local</strong></div><div><span>LAYERS</span><strong><span data-live="layerCount">${sample.layers.length}</span> available</strong></div><div><span>CAPTURE</span><strong data-live="captureLabel">final-position residual</strong></div><div><span>CEILING</span><strong>information presence only</strong></div></div><div class="rail-divider"></div><div class="eyebrow">Live sample</div><div class="big-readout"><span data-live="phaseShort">${sample.phase.short}</span><small data-live="phaseLabel">${sample.phase.label}</small></div><div class="mini-readouts"><div><span>timestamp</span><strong data-live="timestamp">${sample.timestamp.slice(11, 19)}Z</strong></div><div><span>token</span><strong data-live="token">${sample.token}</strong></div></div>${astralPanel(sample)}</aside><section class="panel spectrum-panel"><div class="panel-header"><div><div class="eyebrow">Per-layer residual field</div><h2 class="panel-title" data-live="layerFieldLabel">Layer field / ${sample.layers.length} channels</h2></div><span class="panel-tag">${appState.running || appState.source === "live" ? "STREAMING" : "PAUSED"}</span></div>${layerGrid()}<div class="spectrum-legend"><span><i class="legend-dot low"></i>low energy</span><span><i class="legend-dot mid"></i>transition</span><span><i class="legend-dot high"></i>high energy</span><span class="selected-legend">selected: layer <b data-live="activeLayer">${sample.activeLayer}</b></span></div><div class="chart-heading"><span>Residual / observer divergence</span><span class="mono" data-live="sourceLabel">source = simulated</span></div>${chart()}<div class="metric-rows" data-live-container="metricRows">${metricRows(sample)}</div></section><aside class="panel phase-rail">${phaseCard(sample)}<div class="eyebrow">Channel detail</div><div class="selected-layer"><strong>layer <span data-live="activeLayer">${sample.activeLayer}</span></strong><span class="mono" data-live="selectedLayerState">energy ${round(sample.metrics.residualEnergy)} / salience ${round(layerSignal(selectedLayer(sample)))}</span></div><div class="metric-rows compact">${metricRows(sample)}</div><div class="panel-divider"></div><div class="eyebrow">Event stream</div><div class="event-list" data-live-container="events"></div></aside></section>${salienceLab(sample)}${nodeGraph(sample)}<section class="lower-grid">${selfModelPanel(sample)}${docsPanel()}</section>`;
}

function phaseStrip(sample) {
  return `<div class="phase-strip">${phaseDefinitions.filter((phase) => phase.id !== "runtime").map((phase) => `<div class="phase-step ${phase.id === sample.phase.id ? "active" : ""} tone-${phase.tone}"><span>${escapeHtml(phase.short)}</span><small>${escapeHtml(phase.label.replace("-like", ""))}</small></div>`).join("")}</div>`;
}

function selfModelMetrics(sample) {
  const metrics = [
    ["Self-model coherence", sample.metrics.selfModelCoherence, "proxy"],
    ["Actor / observer divergence", sample.metrics.actorObserverDivergence, "gap"],
    ["Retrospection proxy", sample.metrics.retrospectionProxy, "proxy"],
    ["Counterfactual consistency", sample.metrics.counterfactualConsistency, "proxy"],
  ];
  return metrics.map(([label, value, suffix]) => `<div class="model-metric"><div><span>${label}</span><strong>${metricText(value)} <small>${suffix}</small></strong></div><div class="metric-track"><i style="width:${metricWidth(value)}%"></i></div></div>`).join("");
}

function selfModelPanel(sample = ensureSample()) {
  return `<section class="panel self-model-panel"><div class="panel-header"><div><div class="eyebrow">General self-model diagnostics</div><h2 class="panel-title">Actor ↔ observer</h2></div><span class="panel-tag">PROXY CHANNELS</span></div><p class="panel-subtitle">These are operational readouts for a future causal test. They are not introspection evidence.</p><div class="actor-observer"><div class="agent-block actor"><span class="agent-label">ACTOR</span><strong>forward state</strong><div class="agent-pulse" data-live="actorPulse"></div></div><div class="coupling-arrow"><span data-live="divergenceLabel">coupled</span><i></i></div><div class="agent-block observer"><span class="agent-label">OBSERVER</span><strong>readout state</strong><div class="agent-pulse observer-pulse" data-live="observerPulse"></div></div></div><div class="model-metrics" data-live-container="selfMetrics">${selfModelMetrics(sample)}</div><div class="channel-grid"><div class="channel-row"><span>text report</span><i style="width:34%"></i><b>report</b></div><div class="channel-row"><span>synthetic artifact</span><i style="width:0%"></i><b>not connected</b></div><div class="channel-row"><span>privileged telemetry</span><i data-live-style="telemetryChannel" style="width:68%"></i><b>local proxy</b></div></div></section>`;
}

function docsTimeline() {
  return `<div class="docs-timeline">${["past", "present", "future"].map((period) => `<div class="docs-period ${period}"><div class="docs-period-label">${period}</div>${progressTimeline.filter((item) => item.period === period).map((item) => `<div class="docs-event"><span>${escapeHtml(item.date)}</span><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.note)}</p>${sourceLink(item.source, item.tag)}</div>`).join("")}</div>`).join("")}</div>`;
}

function journalMarkup(limit = 4) {
  const entries = (appState.journal || []).slice().reverse().slice(0, limit);
  if (!entries.length) return `<div class="empty-state">No entries yet. Log a snapshot or add a field note.</div>`;
  return `<div class="journal-list">${entries.map((entry) => `<article class="journal-entry"><div class="journal-meta"><span>${escapeHtml(entry.date)} / ${escapeHtml(entry.period)}</span><button class="delete-entry" title="Delete entry" data-action="delete-entry" data-id="${escapeHtml(entry.id)}">×</button></div><h4>${escapeHtml(entry.title)}</h4><p>${escapeHtml(entry.note)}</p><p class="mono next-note">NEXT / ${escapeHtml(entry.next)}</p></article>`).join("")}</div>`;
}

function composer() {
  return `<div class="composer"><h3>Document concurrently</h3><form id="journal-form"><div class="form-grid"><div class="field"><label for="entry-title">Title</label><input id="entry-title" name="title" required placeholder="e.g. adapter connected" /></div><div class="field"><label for="entry-status">Status</label><input id="entry-status" name="status" required placeholder="e.g. observed / blocked" /></div><div class="field"><label for="entry-period">Horizon</label><select id="entry-period" name="period"><option value="past">Past</option><option value="present" selected>Present</option><option value="future">Future</option></select></div><div class="field"><label for="entry-next">Next gate</label><input id="entry-next" name="next" required placeholder="What must be true next?" /></div><div class="field full"><label for="entry-note">Observation</label><textarea id="entry-note" name="note" required placeholder="Record the signal, interpretation, and ceiling."></textarea></div></div><div class="form-actions"><small>browser-local only</small><button class="primary-button" type="submit">ADD FIELD NOTE</button></div></form></div>`;
}

function docsPanel() {
  return `<section class="panel docs-panel"><div class="panel-header"><div><div class="eyebrow">Past / present / future</div><h2 class="panel-title">Document the stream.</h2></div><span class="panel-tag">LOCAL JOURNAL</span></div>${docsTimeline()}<div class="panel-divider"></div><div class="eyebrow">Recent notes</div>${journalMarkup()}${composer()}</section>`;
}

function sleepView() {
  const sample = ensureSample();
  return `${hero()}${controls()}<section class="sleep-layout"><section class="panel sleep-main"><div class="panel-header"><div><div class="eyebrow">State progression</div><h2 class="panel-title">Sleep-stage proxy map</h2></div><span class="panel-tag">NO BIOLOGICAL CLAIM</span></div><p class="panel-subtitle">The stream cycles through operational labels to test the interface. A real adapter must supply its own state semantics and validation.</p>${phaseStrip(sample)}${phaseCard(sample)}<div class="sleep-chart-title"><span>Composite model-state trajectory</span><span class="mono">last 36 samples</span></div>${chart()}<div class="sleep-observation"><div><span class="eyebrow">Current interpretation</span><strong data-live="phaseLabel">${sample.phase.label}</strong><p data-live="phaseNote">${sample.phase.note}</p></div><div class="confidence-dial"><span data-live="phaseConfidence">${round(0.55 + Math.abs(Math.sin(sample.tick * .2)) * .33)}</span><small>proxy<br />confidence</small></div></div></section><aside class="sleep-aside"><div class="panel">${astralPanel(sample)}<div class="panel-divider"></div><div class="eyebrow">Unresolved channel</div><p class="muted" style="font-size:13px">Astral projection is not an established project lane. This panel prevents the phrase from disappearing while keeping it outside the evidence path.</p><div class="boundary-box"><span>allowed</span><strong>hypothesis visualization</strong><span>not allowed</span><strong>literal projection claim</strong></div></div><div class="panel"><div class="eyebrow">Layer field</div><h2 class="panel-title" style="margin-top:8px">State under the hood</h2><p class="panel-subtitle">Energy by layer, updated with the stream.</p>${layerGrid()}<div class="spectrum-legend"><span><i class="legend-dot low"></i>low</span><span><i class="legend-dot high"></i>high</span></div></div></aside></section><section class="lower-grid">${selfModelPanel(sample)}${docsPanel()}</section>`;
}

function selfModelView() {
  const sample = ensureSample();
  return `${hero()}${controls()}<section class="self-layout"><section class="panel self-main">${selfModelPanel(sample)}<div class="causal-separation"><div class="panel-header"><div><div class="eyebrow">Causal-channel separation</div><h2 class="panel-title">Three observers, one held-out effect.</h2></div><span class="panel-tag">V26 DESIGN ONLY</span></div><div class="observer-columns"><div><span class="observer-type">TEXT REPORT</span><strong>What the model says</strong><p>Visible report surface. May be incomplete.</p></div><div><span class="observer-type">OPAQUE ARTIFACT</span><strong>What a provider trace carries</strong><p>Synthetic boundary only. No live provider.</p></div><div class="selected"><span class="observer-type">PRIVILEGED TELEMETRY</span><strong>What the layer stream shows</strong><p>Local proxy; V25 ceiling remains narrow.</p></div></div><div class="separation-arrow"><span>compare against directly measured held-out intervention effects</span></div></div></section><aside class="self-aside"><div class="panel"><div class="eyebrow">Retrospection proxy</div><h2 class="panel-title" style="margin-top:8px">What changed?</h2><p class="panel-subtitle">Event log, not recovered private computation.</p><div class="event-list large" data-live-container="events"></div></div><div class="panel">${astralPanel(sample)}<div class="panel-divider"></div><div class="eyebrow">Claim ceiling</div><h2 class="panel-title" style="margin-top:8px">Local visualization only.</h2><p class="muted" style="font-size:13px">No display state here can authorize Stage 0C, Stage 1, faithful computation, introspection, or literal projection claims.</p>${sourceLink("/docs/research/astral-self-modeling/README.md#L51", "read boundary")}</div></aside></section><section class="panel docs-wide"><div class="panel-header"><div><div class="eyebrow">Concurrent record</div><h2 class="panel-title">History stays attached to the live signal.</h2></div><span class="panel-tag">${appState.journal.length} NOTES</span></div>${docsTimeline()}<div class="panel-divider"></div>${journalMarkup(6)}${composer()}</section>`;
}

function dock() {
  const index = variants.findIndex((item) => item.id === loadVariant());
  const previous = variants[(index - 1 + variants.length) % variants.length];
  const next = variants[(index + 1) % variants.length];
  const active = variants[index];
  return `<nav class="dock" aria-label="Prototype view switcher"><div class="dock-inner"><button class="dock-control" data-action="variant" data-variant="${previous.id}" aria-label="Previous view">←</button><span class="dock-label">${active.label} / ${active.description}</span><button class="dock-control" data-action="variant" data-variant="${next.id}" aria-label="Next view">→</button></div></nav>`;
}

function render() {
  const variant = loadVariant();
  const view = variant === "sleep" ? sleepView() : variant === "self-model" ? selfModelView() : telemetryView();
  app.innerHTML = `<div class="app-shell">${topbar()}${view}</div>${dock()}`;
  bindInteractions();
  updateLiveDOM();
}

function updateLiveDOM() {
  const sample = ensureSample();
  const setText = (selector, value) => app.querySelectorAll(`[data-live="${selector}"]`).forEach((node) => { node.textContent = value; });
  setText("tick", sample.tick);
  setText("activeLayer", sample.activeLayer);
  setText("eventCount", sample.events.length);
  setText("phaseShort", sample.phase.short);
  setText("phaseLabel", sample.phase.label);
  setText("phaseNote", sample.phase.note);
  setText("phaseConfidence", round(0.55 + Math.abs(Math.sin(sample.tick * .2)) * .33));
  setText("timestamp", `${sample.timestamp.slice(11, 19)}Z`);
  setText("token", sample.token);
  setText("modelName", sample.model_id || "nemotron_h / local");
  setText("layerCount", sample.layers.length);
  setText("layerFieldLabel", `Layer field / ${sample.layers.length} channels`);
  setText("sourceLabel", `source = ${sample.source}`);
  setText("selectedLayerState", `energy ${round(sample.metrics.residualEnergy)} / salience ${round(layerSignal(selectedLayer(sample)))}`);
  setText("salienceModeLabel", salienceMode().label);
  setText("divergenceLabel", Number.isFinite(sample.metrics.actorObserverDivergence) ? sample.metrics.actorObserverDivergence > .62 ? "diverging" : "coupled" : "not captured");
  const age = app.querySelector('[data-live="sampleAge"]');
  if (age) age.textContent = appState.source === "live" || appState.source === "adapter" ? "live" : "sim";
  const layers = app.querySelector('[data-live-container="layers"]');
  if (layers) layers.innerHTML = sample.layers.map((layer) => `<button class="layer-cell ${layer.layer === sample.activeLayer ? "selected" : ""}" title="Layer ${layer.layer}: ${salienceMode().label} ${round(layerSignal(layer))}" style="--intensity:${layerSignal(layer)}" data-action="select-layer" data-layer="${layer.layer}"><span>${layer.layer}</span></button>`).join("");
  app.querySelectorAll("[data-action=salience-mode]").forEach((button) => {
    const active = button.dataset.mode === appState.salienceMode;
    button.classList.toggle("selected", active);
    button.setAttribute("aria-pressed", String(active));
  });
  drawSignalCanvas();
  drawSalienceCanvas();
  updateSalienceTooltip();
  setText("graphPhase", `${sample.phase.short} / LIVE`);
  setText("graphStageLabel", sample.phase.label);
  const graphSvg = app.querySelector('[data-live-container="graphSvg"]');
  if (graphSvg) graphSvg.innerHTML = networkGraphSvg(sample);
  const stageHistory = app.querySelector('[data-live-container="stageHistory"]');
  if (stageHistory) stageHistory.innerHTML = graphStageHistory(sample);
  const graphDetailNode = app.querySelector('[data-live-container="graphDetail"]');
  if (graphDetailNode) graphDetailNode.innerHTML = graphDetail(sample);
  const rows = app.querySelectorAll('[data-live-container="metricRows"]');
  rows.forEach((node) => { node.innerHTML = metricRows(sample); });
  const rank = app.querySelector('[data-live-container="salienceRank"]');
  if (rank) rank.innerHTML = salienceRanking(sample);
  const events = app.querySelectorAll('[data-live-container="events"]');
  events.forEach((node) => { node.innerHTML = sample.events.map((event, index) => `<div class="event-row"><span>0${index + 1}</span><p>${escapeHtml(event)}</p></div>`).join(""); });
  const selfMetrics = app.querySelector('[data-live-container="selfMetrics"]');
  if (selfMetrics) selfMetrics.innerHTML = selfModelMetrics(sample);
  const actorPulse = app.querySelector('[data-live="actorPulse"]');
  if (actorPulse) actorPulse.style.setProperty("--pulse", `${30 + (Number.isFinite(sample.metrics.residualEnergy) ? sample.metrics.residualEnergy * 70 : 0)}%`);
  const observerPulse = app.querySelector('[data-live="observerPulse"]');
  if (observerPulse) observerPulse.style.setProperty("--pulse", `${30 + (Number.isFinite(sample.metrics.selfModelCoherence) ? sample.metrics.selfModelCoherence * 70 : 0)}%`);
  const channel = app.querySelector('[data-live-style="telemetryChannel"]');
  if (channel) channel.style.width = `${32 + (Number.isFinite(sample.metrics.interventionDelta) ? sample.metrics.interventionDelta * 58 : 0)}%`;
  app.querySelectorAll('[data-live="phaseLabel"]').forEach((node) => node.closest(".phase-card")?.classList.add(`tone-${sample.phase.tone}`));
  const layerState = app.querySelector('[data-live="selectedLayerState"]');
  if (layerState) layerState.textContent = `energy ${round(sample.metrics.residualEnergy)} / salience ${round(layerSignal(selectedLayer(sample)))}`;
}

function drawSignalCanvas() {
  const canvas = app.querySelector('[data-live-canvas="chart"]');
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(320, Math.floor(rect.width * ratio));
  const height = Math.max(140, Math.floor((rect.height || 150) * ratio));
  if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
  const context = canvas.getContext("2d");
  if (!context) return;
  context.clearRect(0, 0, width, height);
  context.save();
  context.scale(ratio, ratio);
  const viewWidth = width / ratio;
  const viewHeight = height / ratio;
  context.strokeStyle = "rgba(225,239,231,.09)";
  context.lineWidth = 1;
  for (let row = 1; row < 4; row += 1) {
    const y = (viewHeight / 4) * row;
    context.beginPath(); context.moveTo(0, y); context.lineTo(viewWidth, y); context.stroke();
  }
  const series = (appState.series || []).slice(-36);
  const line = (values, color, dash = []) => {
    if (!values.length) return;
    context.beginPath(); context.setLineDash(dash); context.strokeStyle = color; context.lineWidth = 1.7;
    values.forEach((value, index) => {
      const x = values.length === 1 ? viewWidth : (index / (values.length - 1)) * viewWidth;
      const y = viewHeight - (clamp(value) * (viewHeight - 10)) - 5;
      if (index === 0) context.moveTo(x, y); else context.lineTo(x, y);
    });
    context.stroke(); context.setLineDash([]);
  };
  line(series.map((item) => (item.metrics.residualEnergy + item.metrics.attentionEntropy) / 2), "#c9ef68");
  const divergenceValues = series.map((item) => item.metrics.actorObserverDivergence);
  if (divergenceValues.some((value) => Number.isFinite(value))) line(divergenceValues, "rgba(225,239,231,.62)", [5, 5]);
  context.fillStyle = "#c9ef68";
  context.fillRect(viewWidth - 2, 0, 2, viewHeight);
  context.restore();
}

function drawSalienceCanvas() {
  const canvas = app.querySelector('[data-live-canvas="salience"]');
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(420, Math.floor(rect.width * ratio));
  const height = Math.max(210, Math.floor((rect.height || 270) * ratio));
  if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
  const context = canvas.getContext("2d");
  if (!context) return;
  context.clearRect(0, 0, width, height);
  context.save();
  context.scale(ratio, ratio);
  const viewWidth = width / ratio;
  const viewHeight = height / ratio;
  const plot = { left: 35, top: 18, right: 8, bottom: 24 };
  const plotWidth = Math.max(1, viewWidth - plot.left - plot.right);
  const plotHeight = Math.max(1, viewHeight - plot.top - plot.bottom);
  const series = (appState.series || []).slice(-36);
  const layerCount = Math.max(1, appState.sample?.layers?.length || 1);
  const cellWidth = plotWidth / Math.max(1, series.length);
  const cellHeight = plotHeight / layerCount;
  const mode = salienceMode();

  context.font = '9px SFMono-Regular, Consolas, monospace';
  context.textBaseline = "middle";
  context.fillStyle = "rgba(147,160,159,.78)";
  context.textAlign = "right";
  [1, Math.ceil(layerCount / 2), layerCount].forEach((layerNumber) => {
    const y = plot.top + ((layerNumber - 0.5) * cellHeight);
    context.fillText(`L${layerNumber}`, plot.left - 7, y);
  });
  context.textAlign = "left";
  context.fillStyle = "rgba(147,160,159,.66)";
  context.fillText(mode.short, plot.left, plot.top - 9);
  context.textAlign = "right";
  context.fillText("live", viewWidth - plot.right, viewHeight - 7);

  series.forEach((sample, column) => {
    sample.layers.forEach((layer, row) => {
      const value = layerSignal(layer);
      const x = plot.left + (column * cellWidth);
      const y = plot.top + (row * cellHeight);
      context.fillStyle = `rgba(201,239,104,${0.045 + (value * 0.78)})`;
      context.fillRect(x + 0.5, y + 0.5, Math.max(1, cellWidth - 1), Math.max(1, cellHeight - 1));
    });
    if (sample.phase?.id === "projection") {
      context.fillStyle = "rgba(219,116,116,.13)";
      context.fillRect(plot.left + (column * cellWidth), plot.top, Math.max(1, cellWidth), plotHeight);
    }
  });

  context.strokeStyle = "rgba(232,238,233,.85)";
  context.lineWidth = 1;
  if (appState.sample?.activeLayer) {
    const selectedRow = Math.max(0, appState.sample.layers.findIndex((layer) => layer.layer === appState.sample.activeLayer));
    const y = plot.top + ((selectedRow + 0.5) * cellHeight);
    context.beginPath(); context.moveTo(plot.left, y); context.lineTo(viewWidth - plot.right, y); context.stroke();
  }
  if (appState.hover && appState.hover.seriesIndex < series.length) {
    const x = plot.left + ((appState.hover.seriesIndex + 0.5) * cellWidth);
    const y = plot.top + ((appState.hover.layerIndex + 0.5) * cellHeight);
    context.strokeStyle = "rgba(232,238,233,.92)";
    context.setLineDash([3, 3]);
    context.beginPath(); context.moveTo(x, plot.top); context.lineTo(x, viewHeight - plot.bottom); context.stroke();
    context.setLineDash([]);
    context.beginPath(); context.arc(x, y, 3, 0, Math.PI * 2); context.stroke();
  }
  context.strokeStyle = "rgba(226,237,230,.14)";
  context.strokeRect(plot.left, plot.top, plotWidth, plotHeight);
  context.restore();
}

function updateSalienceTooltip() {
  const tooltip = app.querySelector('[data-live-tooltip="salience"]');
  if (!tooltip) return;
  const series = (appState.series || []).slice(-36);
  const hover = appState.hover;
  if (!hover || !series[hover.seriesIndex]) { tooltip.hidden = true; return; }
  const sample = series[hover.seriesIndex];
  const layer = sample.layers[hover.layerIndex];
  if (!layer) { tooltip.hidden = true; return; }
  const mode = salienceMode();
  tooltip.innerHTML = `<strong>tick ${sample.tick}</strong><span>layer ${layer.layer} / ${escapeHtml(mode.label)} ${round(layerSignal(layer))}</span><span>energy ${round(layer.energy)} · Δ ${round(layer.delta)}</span>`;
  tooltip.style.left = `${clamp(hover.xPercent, 12, 88)}%`;
  tooltip.style.top = `${clamp(hover.yPercent, 15, 82)}%`;
  tooltip.hidden = false;
}

function setSalienceHover(event) {
  const canvas = event.currentTarget;
  const rect = canvas.getBoundingClientRect();
  const series = (appState.series || []).slice(-36);
  if (!series.length) return;
  const layerCount = Math.max(1, appState.sample?.layers?.length || 1);
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const plot = { left: 35, top: 18, right: 8, bottom: 24 };
  const plotWidth = Math.max(1, rect.width - plot.left - plot.right);
  const plotHeight = Math.max(1, rect.height - plot.top - plot.bottom);
  appState.hover = {
    seriesIndex: Math.max(0, Math.min(series.length - 1, Math.floor(((x - plot.left) / plotWidth) * series.length))),
    layerIndex: Math.max(0, Math.min(layerCount - 1, Math.floor(((y - plot.top) / plotHeight) * layerCount))),
    xPercent: (x / Math.max(1, rect.width)) * 100,
    yPercent: (y / Math.max(1, rect.height)) * 100,
  };
  drawSalienceCanvas();
  updateSalienceTooltip();
}

function selectLayer(layerNumber) {
  const sample = ensureSample();
  const selected = sample.layers.find((item) => item.layer === layerNumber) || sample.layers[0];
  appState.sample = { ...sample, activeLayer: selected.layer, metrics: { ...sample.metrics, residualEnergy: selected.energy, attentionEntropy: selected.entropy, activationSparsity: selected.sparsity, interventionDelta: selected.delta } };
  appState.hover = null;
  updateLiveDOM();
}

function setVariant(id) {
  const url = new URL(window.location.href);
  url.searchParams.set("variant", id);
  window.history.replaceState({}, "", url);
  render();
}

function validateAdapterSample(sample) {
  const errors = [];
  if (!sample || typeof sample !== "object") errors.push("sample must be an object");
  if (!sample?.timestamp || !Number.isFinite(Date.parse(sample.timestamp))) errors.push("timestamp must be ISO-8601");
  if (!sample?.model_id) errors.push("model_id is required");
  if (!sample?.run_id) errors.push("run_id is required");
  if (!Array.isArray(sample?.layers) || sample.layers.length === 0) errors.push("layers must be a non-empty array");
  if (!Number.isInteger(sample?.activeLayer)) errors.push("activeLayer must be an integer");
  ["residualEnergy", "activationSparsity"].forEach((key) => {
    if (!Number.isFinite(sample?.metrics?.[key])) errors.push(`metrics.${key} must be numeric`);
  });
  ["attentionEntropy", "interventionDelta", "selfModelCoherence", "actorObserverDivergence", "retrospectionProxy", "counterfactualConsistency"].forEach((key) => {
    if (sample?.metrics?.[key] !== null && sample?.metrics?.[key] !== undefined && !Number.isFinite(sample.metrics[key])) errors.push(`metrics.${key} must be numeric or null`);
  });
  sample?.layers?.forEach((layer, index) => {
    if (!Number.isInteger(layer?.layer)) errors.push(`layers[${index}].layer must be an integer`);
    ["energy", "entropy", "sparsity", "delta"].forEach((key) => { if (!Number.isFinite(layer?.[key])) errors.push(`layers[${index}].${key} must be numeric`); });
    if (layer?.nodes !== undefined && (!Array.isArray(layer.nodes) || layer.nodes.some((value) => !Number.isFinite(value)))) errors.push(`layers[${index}].nodes must be numeric when present`);
  });
  return errors;
}

function ingest(sample, source = "adapter") {
  const errors = validateAdapterSample(sample);
  if (errors.length) {
    if (source === "live") { appState.liveStatus = "error"; appState.liveError = errors.slice(0, 2).join("; "); }
    else appState.adapterError = errors.slice(0, 2).join("; ");
    render();
    return false;
  }
  const phase = normalizePhase(sample.phase);
  const normalized = { ...makeSample(appState.sample?.tick || 0), ...sample, phase, source, layers: sample.layers };
  appState.source = source;
  appState.adapterError = null;
  appState.liveError = null;
  appState.liveStatus = source === "live" ? "connected" : appState.liveStatus;
  appState.running = source === "live" ? !appState.livePaused : false;
  appState.sample = normalized;
  const resetSeries = source === "live" && appState.series?.some((item) => item.source !== "live");
  appState.series = [...(resetSeries ? [] : (appState.series || [])), normalized].slice(-36);
  render();
  return true;
}

async function fetchLiveSample() {
  if (requestedSource() !== "live" || appState.source !== "live" || appState.livePaused || liveInFlight) return;
  liveInFlight = true;
  try {
    const response = await fetch(LIVE_ENDPOINT, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const sample = await response.json();
    ingest(sample, "live");
  } catch (error) {
    appState.liveStatus = "error";
    appState.liveError = error instanceof Error ? error.message : "request failed";
    updateLiveDOM();
  } finally {
    liveInFlight = false;
  }
}

function startLiveBridge() {
  if (requestedSource() !== "live" || liveTimer) return;
  fetchLiveSample();
  liveTimer = window.setInterval(fetchLiveSample, 1300);
}

window.pushAstralTelemetry = ingest;
window.addEventListener("astral-telemetry", (event) => ingest(event.detail));

function logSnapshot() {
  const sample = ensureSample();
  appState.journal.push({
    id: `j-${Date.now()}`, period: "present", status: `${appState.source} snapshot`, date: new Date().toISOString().slice(0, 10),
    title: `${sample.phase.label} / tick ${sample.tick}`,
    note: `Layer ${sample.activeLayer} energy ${metricText(sample.metrics.residualEnergy)}; self-model coherence proxy ${metricText(sample.metrics.selfModelCoherence)}; actor-observer divergence ${metricText(sample.metrics.actorObserverDivergence)}.`,
    next: "Compare the observed stream with a locked causal target before interpreting the phase.",
  });
  saveState();
  render();
}

function exportMarkdown() {
  const lines = ["# Astral Model Observatory — Local Journal", "", `Exported: ${new Date().toISOString()}`, "", "## Stream boundary", `Source: ${appState.source || "simulated"}`, "The default stream is simulated. This export is not evidence of sleep, astral projection, consciousness, introspection, or faithful computation.", "", "## Journal", ""];
  (appState.journal || []).forEach((entry) => lines.push(`### ${entry.date} — ${entry.title}`, `- Horizon: ${entry.period}`, `- Status: ${entry.status}`, `- Observation: ${entry.note}`, `- Next gate: ${entry.next}`, ""));
  downloadFile("astral-observatory-journal.md", lines.join("\n"), "text/markdown");
}

function downloadFile(name, content, type) {
  const blob = new Blob([content], { type });
  const anchor = document.createElement("a");
  anchor.href = URL.createObjectURL(blob);
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(anchor.href);
}

function bindInteractions() {
  if (!app.dataset.layerDelegationBound) {
    app.addEventListener("click", (event) => {
      const button = event.target.closest("[data-action=select-layer]");
      if (button && app.contains(button)) { selectLayer(Number(button.dataset.layer)); return; }
      const node = event.target.closest("[data-action=inspect-node]");
      if (node && app.contains(node)) {
        appState.graphFocus = { layer: Number(node.dataset.layer), node: Number(node.dataset.node) };
        updateLiveDOM();
      }
    });
    app.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      const node = event.target.closest?.("[data-action=inspect-node]");
      if (!node || !app.contains(node)) return;
      event.preventDefault();
      appState.graphFocus = { layer: Number(node.dataset.layer), node: Number(node.dataset.node) };
      updateLiveDOM();
    });
    app.dataset.layerDelegationBound = "true";
  }
  if (!app.dataset.resizeBound) {
    window.addEventListener("resize", () => { drawSignalCanvas(); drawSalienceCanvas(); updateSalienceTooltip(); });
    app.dataset.resizeBound = "true";
  }
  app.querySelectorAll("[data-action=variant]").forEach((button) => button.addEventListener("click", () => setVariant(button.dataset.variant)));
  app.querySelectorAll("[data-action=toggle-stream]").forEach((button) => button.addEventListener("click", () => {
    if (appState.source === "live") { appState.livePaused = !appState.livePaused; appState.running = !appState.livePaused; }
    else appState.running = !appState.running;
    render();
  }));
  app.querySelectorAll("[data-action=resume-sim]").forEach((button) => button.addEventListener("click", () => { const url = new URL(window.location.href); url.searchParams.delete("source"); window.history.replaceState({}, "", url); appState.source = "simulated"; appState.adapterError = null; appState.liveError = null; appState.liveStatus = "offline"; appState.livePaused = false; appState.running = true; render(); }));
  app.querySelectorAll("[data-action=salience-mode]").forEach((button) => button.addEventListener("click", () => { appState.salienceMode = button.dataset.mode; appState.hover = null; saveState(); updateLiveDOM(); }));
  app.querySelectorAll("[data-action=log-snapshot]").forEach((button) => button.addEventListener("click", logSnapshot));
  app.querySelectorAll("[data-action=export-markdown]").forEach((button) => button.addEventListener("click", exportMarkdown));
  const salienceCanvas = app.querySelector('[data-live-canvas="salience"]');
  if (salienceCanvas) {
    salienceCanvas.addEventListener("pointermove", setSalienceHover);
    salienceCanvas.addEventListener("pointerleave", () => { appState.hover = null; drawSalienceCanvas(); updateSalienceTooltip(); });
    salienceCanvas.addEventListener("click", () => {
      const series = (appState.series || []).slice(-36);
      const hoveredSample = appState.hover && series[appState.hover.seriesIndex];
      const layer = hoveredSample?.layers?.[appState.hover.layerIndex];
      if (layer) selectLayer(layer.layer);
    });
  }
  app.querySelectorAll("[data-action=delete-entry]").forEach((button) => button.addEventListener("click", () => { appState.journal = appState.journal.filter((entry) => entry.id !== button.dataset.id); saveState(); render(); }));
  const form = document.getElementById("journal-form");
  if (form) form.addEventListener("submit", (event) => { event.preventDefault(); const data = new FormData(form); appState.journal.push({ id: `j-${Date.now()}`, date: new Date().toISOString().slice(0, 10), title: data.get("title"), status: data.get("status"), period: data.get("period"), note: data.get("note"), next: data.get("next") }); saveState(); render(); });
}

document.addEventListener("keydown", (event) => {
  if (event.target.matches("input, textarea, select, [contenteditable]")) return;
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
  const index = variants.findIndex((item) => item.id === loadVariant());
  const nextIndex = event.key === "ArrowLeft" ? (index - 1 + variants.length) % variants.length : (index + 1) % variants.length;
  setVariant(variants[nextIndex].id);
});

render();
startSimulation();
startLiveBridge();
