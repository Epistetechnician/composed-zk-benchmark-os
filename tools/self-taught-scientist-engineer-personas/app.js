/*
 * State slice: self-taught-scientist-engineer-persona-site-v1.
 * This is a conceptual, local-only interaction surface. It does not read or
 * write research artifacts, run models, or create evidence.
 */

const personaData = {
  calculated: {
    kicker: "CALCULATED SELF-TAUGHT",
    status: "DEFAULT INSTINCT / REDUCE UNKNOWN",
    title: "Borrow the hard-won map.",
    description: "Find practitioners who have already paid the cost of the mistake. Follow a coherent path long enough to absorb its language, habits, and constraints. Consistency becomes your unfair advantage.",
    strength: "Drop-in fluency",
    question: "What does the precedent protect?",
    risk: "Autopilot disguised as rigor",
    prompt: "The cost of repeating an old mistake is higher than the cost of inheriting an old constraint."
  },
  unhinged: {
    kicker: "UNHINGED SELF-TAUGHT",
    status: "DEFAULT INSTINCT / EXPAND UNKNOWN",
    title: "Treat the map as a hypothesis.",
    description: "Read widely, collect incompatible viewpoints, and refuse to let one school of thought decide what is possible before you test it. Novelty becomes your unfair advantage.",
    strength: "Fast reframing",
    question: "Which rule is still true?",
    risk: "Ego disguised as originality",
    prompt: "The cost of inheriting a dead constraint is higher than the cost of a small, reversible experiment."
  }
};

const caseData = {
  handoff: {
    label: "CASE 01 / THE HANDOFF",
    signal: "LEARN BEFORE YOU REWRITE",
    title: "Absorb the system before you improve it.",
    summary: "The calculated move is to trace the conventions, failure history, and vocabulary of the codebase before proposing a new shape.",
    calculated: "Map the seams. Copy the local grammar. Earn the right to make a change that feels native.",
    unhinged: "Ask which conventions are load-bearing and which are just fossils. Prototype a smaller alternative beside the old path.",
    synthesis: "First understand the constraint. Then test whether it still exists."
  },
  deadline: {
    label: "CASE 02 / THE CONSTRAINT",
    signal: "OUTPUT BEFORE ORTHODOXY",
    title: "Let the deadline expose the real trade.",
    summary: "A perfect architecture that misses the window is not a perfect result. But a shortcut without an exit plan is just deferred cost.",
    calculated: "Name the standard path, its safety margin, and the smallest deviation that keeps the system legible.",
    unhinged: "Delete ceremony that does not change the outcome. Build the ugly version that tells you what matters.",
    synthesis: "Spend rigor where failure is expensive. Make the rest reversible."
  },
  unknown: {
    label: "CASE 03 / THE FRONTIER",
    signal: "BORROW ACROSS BOUNDARIES",
    title: "Use unfamiliarity as a research instrument.",
    summary: "When the problem has no obvious category, a single canonical source can become a blindfold. Cross-pollination is the point.",
    calculated: "Find the nearest mature field and learn the constraints it has already made explicit.",
    unhinged: "Steal metaphors from distant disciplines before anyone explains why they do not belong here.",
    synthesis: "Import the question, not the answer. Re-earn the assumptions locally."
  },
  standard: {
    label: "CASE 04 / THE REFLEX",
    signal: "REASON BEFORE RITUAL",
    title: "Ask what the standard is buying.",
    summary: "“That is how it is done” is a useful starting point and a terrible stopping point. The reason matters more than the ritual.",
    calculated: "Reconstruct the original failure that made the standard necessary.",
    unhinged: "Run the counterfactual without asking permission from the habit.",
    synthesis: "Respect the lesson. Do not worship the scar."
  }
};

const loopData = {
  learn: {
    label: "STEP 01 / LEARN",
    mode: "CALCULATED FIRST",
    title: "Study the people who already paid for the lesson.",
    description: "Choose a small set of trustworthy sources. Learn their language closely enough that you can tell which parts are principles and which parts are personal habit.",
    quote: "Consistency is useful when it is a choice you can still explain."
  },
  inspect: {
    label: "STEP 02 / INSPECT",
    mode: "LOOK FOR THE LOAD-BEARING PART",
    title: "Separate the constraint from the ceremony.",
    description: "Trace the boundary: what breaks if you remove this practice, and what merely looks unfamiliar when you do? This is where respect becomes understanding.",
    quote: "A standard is a compressed history of someone else's failure."
  },
  question: {
    label: "STEP 03 / QUESTION",
    mode: "UNHINGED ON PURPOSE",
    title: "Ask the question the local vocabulary cannot ask.",
    description: "Switch sources. Change the framing. Assume the category may be wrong. Questioning is not rejection; it is how inherited assumptions become visible.",
    quote: "If the only defense is that it is normal, the investigation has just started."
  },
  test: {
    label: "STEP 04 / TEST",
    mode: "MAKE THE STRANGE REVERSIBLE",
    title: "Turn the weird idea into a small observable bet.",
    description: "Keep the experiment bounded, choose the signal before the story, and define the exit. A strange idea earns more freedom when it leaves better evidence.",
    quote: "Creativity gets a budget. The result gets a vote."
  },
  ship: {
    label: "STEP 05 / SHIP",
    mode: "SYNTHESIS / KEEP WHAT SURVIVES",
    title: "Keep the result, not the identity that produced it.",
    description: "The calculated self-taught does not need to be right forever. The unhinged self-taught does not need to be different forever. Ship what works and let the persona change.",
    quote: "The point is not to break rules. The point is to stop being ruled by them."
  }
};

const byId = (id) => document.getElementById(id);

function setPersona(mode) {
  const data = personaData[mode];
  if (!data) return;

  document.body.dataset.mode = mode;
  const panel = byId("mode-panel");
  panel.dataset.mode = mode;
  byId("mode-kicker").textContent = data.kicker;
  byId("mode-status").textContent = data.status;
  byId("mode-title").textContent = data.title;
  byId("mode-description").textContent = data.description;
  byId("mode-strength").textContent = data.strength;
  byId("mode-question").textContent = data.question;
  byId("mode-risk").textContent = data.risk;
  byId("mode-prompt").textContent = data.prompt;

  document.querySelectorAll(".mode-tab").forEach((button) => {
    const isActive = button.dataset.mode === mode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
}

function setCase(caseId) {
  const data = caseData[caseId];
  if (!data) return;

  byId("case-label").textContent = data.label;
  byId("case-signal").textContent = data.signal;
  byId("case-title").textContent = data.title;
  byId("case-summary").textContent = data.summary;
  byId("case-calculated").textContent = data.calculated;
  byId("case-unhinged").textContent = data.unhinged;
  byId("case-synthesis").textContent = data.synthesis;

  document.querySelectorAll(".pressure-tab").forEach((button) => {
    const isActive = button.dataset.case === caseId;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
}

function setLoopStep(stepId) {
  const data = loopData[stepId];
  if (!data) return;

  byId("loop-label").textContent = data.label;
  byId("loop-mode").textContent = data.mode;
  byId("loop-title-detail").textContent = data.title;
  byId("loop-description").textContent = data.description;
  byId("loop-quote").textContent = `“${data.quote}”`;

  document.querySelectorAll(".loop-step").forEach((button) => {
    const isActive = button.dataset.step === stepId;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
}

document.querySelectorAll(".mode-tab").forEach((button) => {
  button.addEventListener("click", () => setPersona(button.dataset.mode));
});

document.querySelectorAll(".pressure-tab").forEach((button) => {
  button.addEventListener("click", () => setCase(button.dataset.case));
});

document.querySelectorAll(".loop-step").forEach((button) => {
  button.addEventListener("click", () => setLoopStep(button.dataset.step));
});

setPersona("calculated");
setCase("handoff");
setLoopStep("learn");
