/*
 * Astral Research Atlas — long-form research surface.
 * State slice: astral-research-atlas-accessible-tabs-v5.
 * This page is a documentation and visualization surface. It does not
 * create evidence, authorize execution, or promote any research claim.
 */

const phases = [
  { id: "v1-v10", label: "V1–V10", date: "setup", title: "Build the measurement boundary", summary: "The early phases established the actor, tracer, attribution methods, training qualifications, and the local Rust protocol boundary. The learned-model result remained exploratory.", established: "A staged local measurement program", unopened: "A validated cross-actor causal target", source: "/docs/research/astral-self-modeling/19-evidence-synthesis-and-research-reset-v11.md" },
  { id: "v12-v16", label: "V12–V16", date: "effect target", title: "Try the causal target", summary: "The project moved the endpoint from explanation quality to directly measured intervention effects. Leave-one-actor-out, prediction-locked, transport, actor-specific, and structured probes all kept the gate explicit.", established: "A sharper falsification target", unopened: "Uniform validity across actors and effects", source: "/docs/research/astral-self-modeling/29-stage0c-v16-execution-record.md" },
  { id: "v17-v21", label: "V17–V21", date: "trained models", title: "Test effect explainers", summary: "Pretrained and trained language-model pilots tested residual interventions, input ablations, opaque preferences, continuous margins, and heterogeneous text. The local results stayed development-only.", established: "A family of negative and bounded feasibility results", unopened: "A same-model advantage that survives held-out controls", source: "/docs/research/astral-self-modeling/39-v21-execution-record.md" },
  { id: "v22–V24", label: "V22–V24", date: "instrument", title: "Separate activation from input", summary: "Three-way construction-controlled protocols and a hybrid instrument seam tested whether a local observer could distinguish activation intervention from matched input controls.", established: "A certified local seam and qualification stops", unopened: "A qualified assessment that opens the next scientific gate", source: "/docs/research/astral-self-modeling/45-v24-execution-record.md" },
  { id: "v25", label: "V25", date: "latest executed", title: "Observe a narrow report gap", summary: "On identical assessment trials, a closed-form probe decoded activation-versus-none while the model report did not. The result is information-presence evidence on one local setup, not introspection or causal fidelity.", established: "Probe accuracy 1.0; report accuracy 0.34375; observed margin 0.65625", unopened: "Confirmation, Stage 0C, Stage 1, and any claim above the local ceiling", source: "/docs/research/astral-self-modeling/47-v25-execution-record.md" },
];

const evidenceSteps = [
  { index: "01", title: "Information presence", status: "current", label: "current ceiling", detail: "A captured channel can contain a decodable distinction under a frozen local protocol. This is the narrow result V25 is allowed to carry." },
  { index: "02", title: "Causal effect prediction", status: "held", label: "held", detail: "The observer must predict directly measured intervention effects on held-out actors and families before seeing the assessment effects." },
  { index: "03", title: "Instrumental improvement", status: "blocked", label: "blocked", detail: "Only after causal validity can the project test whether observer predictions improve behavior, calibration, or safety." },
  { index: "04", title: "General self-model claim", status: "blocked", label: "not permitted", detail: "No local visualization or report establishes consciousness, subjective experience, global introspection, semantic correctness, or complete internal access." },
];

const stackDetails = {
  benchmark: { title: "benchmark OS", body: "The custody and validation substrate: replayable bundles, quarantine, provenance, local gates, and evidence-boundary types. It makes a result inspectable without making it true." },
  astral: { title: "Astral", body: "The actor–observer research lane: measure hidden state, predict held-out intervention effects, and only then ask whether observer value or correction survives controls." },
  hsai: { title: "HSAI", body: "The claim and authority lane: envelope what is known, preserve provenance, and keep identity, economy, attestation, and external rails from being smuggled in as scientific evidence." },
};

const rail = document.querySelector("[data-record-rail]");
const detail = document.querySelector("[data-record-detail]");
const ladder = document.querySelector("[data-evidence-ladder]");
const evidenceReadout = document.querySelector("[data-evidence-readout]");
const stackDetail = document.querySelector("[data-stack-detail]");
const architectureFigure = document.querySelector("[data-architecture-figure]");
const architectureStatus = document.querySelector("[data-architecture-status]");

const architectureModes = {
  report: "visible report / approximate observable",
  telemetry: "privileged telemetry / approximate state measurement",
  effect: "held-out effect / directly measured target",
};

const urlStateKeys = {
  architecture: "view",
  phase: "phase",
  evidence: "rung",
  stack: "lane",
};

function syncUrlState(state, value) {
  const url = new URL(window.location.href);
  const key = urlStateKeys[state];
  if (!key || url.searchParams.get(key) === value) return;
  url.searchParams.set(key, value);
  window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
}

function bindKeyboardActivation(container, selector) {
  container.addEventListener("keydown", (event) => {
    const button = event.target.closest(selector);
    if (!button || !container.contains(button)) return;
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    button.click();
  });
}

function bindTabListKeyboard(list, selector) {
  list.addEventListener("keydown", (event) => {
    const tabs = [...list.querySelectorAll(selector)];
    const current = tabs.indexOf(event.target.closest(selector));
    if (current < 0) return;
    let next = current;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") next = (current + 1) % tabs.length;
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = (current - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = tabs.length - 1;
    if (next === current) return;
    event.preventDefault();
    tabs[next].focus();
    tabs[next].click();
  });
}

function renderPhaseDetail(phase) {
  detail.setAttribute("aria-labelledby", `phase-tab-${phase.id}`);
  detail.innerHTML = `<div class="detail-top"><span>${phase.date}</span><strong>${phase.label}</strong></div><h3>${phase.title}</h3><p>${phase.summary}</p><div class="detail-bottom"><div><span>established</span><strong>${phase.established}</strong></div><div><span>still unopened</span><strong>${phase.unopened}</strong></div></div><a class="text-link" href="${phase.source}">open phase record ↗</a>`;
}

function renderPhases() {
  rail.innerHTML = phases.map((phase, index) => `<button class="record-step ${index === phases.length - 1 ? "active" : ""}" id="phase-tab-${phase.id}" data-phase="${phase.id}" role="tab" aria-controls="phase-detail" aria-selected="${index === phases.length - 1}" tabindex="${index === phases.length - 1 ? "0" : "-1"}"><strong>${phase.label}</strong><small>${phase.date}</small></button>`).join("");
  renderPhaseDetail(phases[phases.length - 1]);
  rail.addEventListener("click", (event) => {
    const button = event.target.closest("[data-phase]");
    if (!button) return;
    const phase = phases.find((item) => item.id === button.dataset.phase);
    if (!phase) return;
    rail.querySelectorAll("[data-phase]").forEach((item) => { const active = item === button; item.classList.toggle("active", active); item.setAttribute("aria-selected", active); item.tabIndex = active ? 0 : -1; });
    renderPhaseDetail(phase);
    syncUrlState("phase", phase.id);
  });
  bindKeyboardActivation(rail, "[data-phase]");
  bindTabListKeyboard(rail, "[data-phase]");
}

function renderEvidence() {
  ladder.innerHTML = evidenceSteps.map((step, index) => `<button class="evidence-step ${step.status} ${index === 0 ? "active" : ""}" data-evidence="${step.index}" aria-controls="evidence-readout" aria-pressed="${index === 0}"><span class="step-index">${step.index}</span><strong>${step.title}</strong><small>${step.label}</small></button>`).join("");
  renderEvidenceReadout(evidenceSteps[0]);
  ladder.addEventListener("click", (event) => {
    const button = event.target.closest("[data-evidence]");
    if (!button) return;
    const step = evidenceSteps.find((item) => item.index === button.dataset.evidence);
    if (!step) return;
    ladder.querySelectorAll("[data-evidence]").forEach((item) => { item.classList.toggle("active", item === button); item.setAttribute("aria-pressed", item === button); });
    renderEvidenceReadout(step);
    syncUrlState("evidence", step.index);
  });
  bindKeyboardActivation(ladder, "[data-evidence]");
}

function renderEvidenceReadout(step) {
  evidenceReadout.innerHTML = `<strong>${step.title} / ${step.label}</strong><br />${step.detail}`;
}

function renderStack(key = "benchmark") {
  const item = stackDetails[key];
  stackDetail.innerHTML = `<strong>${item.title}</strong><p>${item.body}</p>`;
  document.querySelectorAll("[data-stack]").forEach((button) => { const active = button.dataset.stack === key; button.classList.toggle("active", active); button.setAttribute("aria-pressed", active); });
}

function bindStack() {
  document.querySelectorAll("[data-stack]").forEach((button) => button.addEventListener("click", () => {
    renderStack(button.dataset.stack);
    syncUrlState("stack", button.dataset.stack);
  }));
  bindKeyboardActivation(document, "[data-stack]");
  renderStack();
}

function bindScrollState() {
  const progress = document.querySelector(".site-progress span");
  const links = [...document.querySelectorAll("[data-section]")];
  const sections = [...document.querySelectorAll("[data-observe-section]")];
  const updateProgress = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    progress.style.setProperty("--progress", max > 0 ? window.scrollY / max : 0);
  };
  window.addEventListener("scroll", updateProgress, { passive: true });
  updateProgress();
  const observer = new IntersectionObserver((entries) => {
    const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    links.forEach((link) => {
      const active = link.dataset.section === visible.target.id;
      link.classList.toggle("active", active);
      if (active) link.setAttribute("aria-current", "location"); else link.removeAttribute("aria-current");
    });
  }, { rootMargin: "-18% 0px -63% 0px", threshold: [0, .2, .6] });
  sections.forEach((section) => observer.observe(section));
}

function bindArchitecture() {
  document.querySelectorAll("[data-architecture]").forEach((button) => button.addEventListener("click", () => {
    const mode = button.dataset.architecture;
    if (!architectureModes[mode]) return;
    architectureFigure.dataset.mode = mode;
    architectureStatus.textContent = architectureModes[mode];
    document.querySelectorAll("[data-architecture]").forEach((item) => {
      const active = item === button;
      item.classList.toggle("active", active);
      item.setAttribute("aria-selected", active);
      item.tabIndex = active ? 0 : -1;
    });
    architectureFigure.setAttribute("aria-labelledby", button.id);
    syncUrlState("architecture", mode);
  }));
  bindKeyboardActivation(document, "[data-architecture]");
  bindTabListKeyboard(document.querySelector("[data-architecture-tabs]"), "[data-architecture]");
  architectureFigure.dataset.mode = "report";
}

function applyUrlState() {
  const params = new URLSearchParams(window.location.search);
  const controls = [
    ["architecture", "[data-architecture]", "view"],
    ["phase", "[data-phase]", "phase"],
    ["evidence", "[data-evidence]", "rung"],
    ["stack", "[data-stack]", "lane"],
  ];
  controls.forEach(([, selector, key]) => {
    const value = params.get(key);
    if (!value) return;
    const button = [...document.querySelectorAll(selector)].find((item) => {
      const attribute = item.dataset.architecture || item.dataset.phase || item.dataset.evidence || item.dataset.stack;
      return attribute === value;
    });
    if (button) button.click();
  });
}

renderPhases();
renderEvidence();
bindStack();
bindArchitecture();
bindScrollState();
applyUrlState();
