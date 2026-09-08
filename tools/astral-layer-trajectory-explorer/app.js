/* State slice: astral-layer-trajectory-explorer-prototype-v1. */

const PATH_COUNT = 255;
const LAYER_COUNT = 78;
const DEFAULT_LAYER = 41;
const canvas = document.getElementById("trajectoryCanvas");
const context = canvas.getContext("2d");
const slider = document.getElementById("layerSlider");
const layerValue = document.getElementById("layerValue");
const selectedToken = document.getElementById("selectedToken");
const selectedPosition = document.getElementById("selectedPosition");
const selectedNorm = document.getElementById("selectedNorm");
const selectedTrajectory = document.getElementById("selectedTrajectory");
const selectionState = document.getElementById("selectionState");
const selectionCopy = document.getElementById("selectionCopy");
const canvasStatus = document.getElementById("canvasStatus");
const sweepTrack = document.getElementById("sweepTrack");
const sweepValue = document.getElementById("sweepValue");
const sweepState = document.getElementById("sweepState");
const commitButton = document.getElementById("commitButton");
const playButton = document.getElementById("playButton");
const timelinePlay = document.getElementById("timelinePlay");

const state = {
  mode: "direction",
  layer: DEFAULT_LAYER,
  selectedPath: 183,
  playing: false,
  dragging: false,
  proposedOffset: { x: 0, y: 0 },
  committedPushes: [],
  zoom: 1,
  pan: { x: 0, y: 0 },
};

function seededRandom(seed) {
  let value = seed >>> 0;
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

function makeFixture() {
  const random = seededRandom(18478);
  return Array.from({ length: PATH_COUNT }, (_, pathIndex) => {
    const fan = (pathIndex / PATH_COUNT) - 0.5;
    const phase = random() * Math.PI * 2;
    const bend = 0.72 + random() * 0.42;
    const tilt = (random() - 0.5) * 0.18;
    const points = Array.from({ length: LAYER_COUNT }, (_, layer) => {
      const progress = layer / (LAYER_COUNT - 1);
      const wing = Math.sin(progress * Math.PI);
      const bow = Math.sin(progress * Math.PI * 2 + phase) * 0.07;
      const x = (-0.28 - wing * 0.42 + progress * 0.82 + fan * (0.08 + progress * 0.28) + bow) * bend;
      const y = (Math.cos(progress * Math.PI) * 0.38 + Math.sin(progress * Math.PI * 1.8 + phase) * 0.07 + fan * 0.1 + tilt * progress);
      const norm = 0.26 + progress * 0.72 + Math.sin(phase + progress * 3.1) * 0.025;
      return { x, y, norm };
    });
    return { id: pathIndex, token: pathIndex + 1, points };
  });
}

const fixture = makeFixture();

function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
function lerp(a, b, amount) { return a + (b - a) * amount; }
function selectedPath() { return fixture[state.selectedPath]; }
function currentPoint(path = selectedPath()) { return path.points[state.layer]; }
function projection(point) {
  if (state.mode === "direction") return { x: point.x * 1.15, y: point.y * 1.15, norm: point.norm };
  return { x: point.x * 1.7, y: point.y * 1.7, norm: point.norm };
}

function projectionBounds() {
  const points = fixture.flatMap((path) => path.points.map(projection));
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  return { minX, maxX, minY, maxY, centerX: (minX + maxX) / 2, centerY: (minY + maxY) / 2 };
}

function resizeCanvas() {
  const ratio = window.devicePixelRatio || 1;
  const bounds = canvas.getBoundingClientRect();
  canvas.width = Math.max(1, Math.round(bounds.width * ratio));
  canvas.height = Math.max(1, Math.round(bounds.height * ratio));
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  draw();
}

function screenMap(bounds) {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const plotWidth = width * 0.72 * state.zoom;
  const plotHeight = height * 0.7 * state.zoom;
  const spanX = Math.max(0.8, bounds.maxX - bounds.minX);
  const spanY = Math.max(0.8, bounds.maxY - bounds.minY);
  const scale = Math.min(plotWidth / spanX, plotHeight / spanY);
  const centerX = width / 2 + state.pan.x;
  const centerY = height / 2 + state.pan.y;
  return {
    toScreen(point) { return { x: centerX + (point.x - bounds.centerX) * scale, y: centerY + (point.y - bounds.centerY) * scale }; },
    toData(point) { return { x: (point.x - centerX) / scale + bounds.centerX, y: (point.y - centerY) / scale + bounds.centerY }; },
  };
}

function colorForLayer(layer, alpha = 0.22) {
  const hue = lerp(232, 16, layer / (LAYER_COUNT - 1));
  return `hsla(${hue}, 78%, 69%, ${alpha})`;
}

function drawGrid(width, height) {
  context.save();
  context.strokeStyle = "rgba(185, 190, 225, 0.055)";
  context.lineWidth = 1;
  for (let x = 30; x < width; x += 48) { context.beginPath(); context.moveTo(x, 0); context.lineTo(x, height); context.stroke(); }
  for (let y = 24; y < height; y += 48) { context.beginPath(); context.moveTo(0, y); context.lineTo(width, y); context.stroke(); }
  context.restore();
}

function drawPath(path, map, committed, selected) {
  const points = path.points.map((point, index) => {
    const base = projection(point);
    const push = committed.find((item) => item.pathId === path.id && index >= item.layer);
    return map.toScreen({ x: base.x + (push?.x || 0), y: base.y + (push?.y || 0) });
  });
  context.save();
  context.lineCap = "round";
  context.lineJoin = "round";
  context.lineWidth = selected ? 2.1 : 0.86;
  if (selected && committed.some((item) => item.pathId === path.id)) context.setLineDash([5, 5]);
  for (let index = 1; index < points.length; index += 1) {
    context.strokeStyle = selected ? "rgba(224, 249, 242, 0.92)" : colorForLayer(index, 0.17);
    context.beginPath();
    context.moveTo(points[index - 1].x, points[index - 1].y);
    context.lineTo(points[index].x, points[index].y);
    context.stroke();
  }
  context.setLineDash([]);
  if (selected && committed.length) {
    const after = path.points.map((point, index) => {
      const base = projection(point);
      const push = committed.find((item) => item.pathId === path.id && index >= item.layer);
      return map.toScreen({ x: base.x + (push?.x || 0), y: base.y + (push?.y || 0) });
    });
    context.strokeStyle = "rgba(115, 229, 209, 0.88)";
    context.lineWidth = 2.2;
    context.beginPath();
    after.forEach((point, index) => { if (index === 0) context.moveTo(point.x, point.y); else context.lineTo(point.x, point.y); });
    context.stroke();
  }
  context.restore();
}

function drawBead(map, bounds) {
  const point = projection(currentPoint());
  const screen = map.toScreen({ x: point.x + state.proposedOffset.x, y: point.y + state.proposedOffset.y });
  const pulse = 1 + Math.sin(performance.now() / 270) * 0.12;
  context.save();
  context.beginPath();
  context.arc(screen.x, screen.y, 7 * pulse, 0, Math.PI * 2);
  context.fillStyle = "rgba(115, 229, 209, 0.95)";
  context.shadowColor = "rgba(115, 229, 209, 0.55)";
  context.shadowBlur = 18;
  context.fill();
  context.shadowBlur = 0;
  context.beginPath();
  context.arc(screen.x, screen.y, 3, 0, Math.PI * 2);
  context.fillStyle = "#f5fffb";
  context.fill();
  if (Math.abs(state.proposedOffset.x) + Math.abs(state.proposedOffset.y) > 0.002) {
    const original = map.toScreen(point);
    context.strokeStyle = "rgba(115, 229, 209, 0.7)";
    context.setLineDash([3, 4]);
    context.beginPath(); context.moveTo(original.x, original.y); context.lineTo(screen.x, screen.y); context.stroke();
  }
  context.restore();
  return { screen, bounds };
}

function draw() {
  if (!canvas.clientWidth) return;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  context.clearRect(0, 0, width, height);
  drawGrid(width, height);
  const bounds = projectionBounds();
  const map = screenMap(bounds);
  fixture.forEach((path) => drawPath(path, map, state.committedPushes, path.id === state.selectedPath));
  drawBead(map, bounds);
  context.save();
  context.fillStyle = "rgba(115, 229, 209, 0.42)";
  context.font = "10px SFMono-Regular, monospace";
  context.fillText(`L${String(state.layer).padStart(2, "0")}`, width - 45, 24);
  context.restore();
  if (state.playing || Math.abs(state.proposedOffset.x) + Math.abs(state.proposedOffset.y) > 0.002) requestAnimationFrame(draw);
}

function updateRangeProgress() {
  slider.style.setProperty("--range-progress", `${(state.layer / (LAYER_COUNT - 1)) * 100}%`);
}

function updateReadout() {
  const path = selectedPath();
  const point = currentPoint(path);
  layerValue.textContent = String(state.layer);
  selectedToken.textContent = String(path.token).padStart(3, "0");
  selectedPosition.textContent = `L${state.layer} / ${LAYER_COUNT}`;
  selectedNorm.textContent = point.norm.toFixed(2);
  selectedTrajectory.textContent = state.committedPushes.some((item) => item.pathId === path.id) ? "annotated" : "active";
  updateRangeProgress();
  const proposal = Math.hypot(state.proposedOffset.x, state.proposedOffset.y) * 1.8;
  const dose = clamp(proposal, 0, 1);
  const hasCommittedAnnotation = state.committedPushes.some((item) => item.pathId === path.id);
  sweepTrack.style.width = `${dose * 100}%`;
  sweepValue.textContent = dose.toFixed(2);
  commitButton.disabled = dose < 0.01;
  sweepState.textContent = dose >= 0.01 ? "proposal ready" : hasCommittedAnnotation ? "annotated" : "uncommitted";
  selectionState.textContent = state.dragging ? "steering" : "tracking";
  selectionCopy.textContent = state.dragging ? "Proposal vector is being edited in projection space. Release to stage it for the sweep." : "This highlighted path is a synthetic token residual state. The bead marks the current layer and is the only draggable control in the field.";
}

function pointerPosition(event) {
  const rect = canvas.getBoundingClientRect();
  return { x: event.clientX - rect.left, y: event.clientY - rect.top };
}

function nearestPath(pointer, map, bounds) {
  let best = { id: state.selectedPath, distance: Infinity };
  fixture.forEach((path) => {
    const point = map.toScreen(projection(path.points[state.layer]));
    const distance = Math.hypot(pointer.x - point.x, pointer.y - point.y);
    if (distance < best.distance) best = { id: path.id, distance };
  });
  return best.distance < 28 ? best : null;
}

function getMap() { return screenMap(projectionBounds()); }

canvas.addEventListener("pointerdown", (event) => {
  const map = getMap();
  const pointer = pointerPosition(event);
  const original = map.toScreen(projection(currentPoint()));
  const bead = map.toScreen({ x: projection(currentPoint()).x + state.proposedOffset.x, y: projection(currentPoint()).y + state.proposedOffset.y });
  if (event.shiftKey || Math.hypot(pointer.x - bead.x, pointer.y - bead.y) < 16) {
    state.dragging = true;
    canvas.setPointerCapture(event.pointerId);
    canvas.style.cursor = "grabbing";
    state.proposedOffset = { x: map.toData(pointer).x - projection(currentPoint()).x, y: map.toData(pointer).y - projection(currentPoint()).y };
    updateReadout(); draw();
    return;
  }
  const nearest = nearestPath(pointer, map, projectionBounds());
  if (nearest) {
    state.selectedPath = nearest.id;
    state.proposedOffset = { x: 0, y: 0 };
    canvasStatus.textContent = `Token ${String(selectedPath().token).padStart(3, "0")} selected / L${state.layer}`;
    updateReadout(); draw();
  }
  void original;
});

canvas.addEventListener("pointermove", (event) => {
  if (!state.dragging) return;
  const map = getMap();
  const pointer = pointerPosition(event);
  const base = projection(currentPoint());
  state.proposedOffset = { x: map.toData(pointer).x - base.x, y: map.toData(pointer).y - base.y };
  updateReadout(); draw();
});

function finishDrag(event) {
  if (!state.dragging) return;
  state.dragging = false;
  canvas.releasePointerCapture?.(event.pointerId);
  canvas.style.cursor = "crosshair";
  canvasStatus.textContent = "Proposal staged / commit or reset";
  updateReadout(); draw();
}
canvas.addEventListener("pointerup", finishDrag);
canvas.addEventListener("pointercancel", finishDrag);

canvas.addEventListener("wheel", (event) => {
  event.preventDefault();
  state.zoom = clamp(state.zoom + (event.deltaY > 0 ? -0.08 : 0.08), 0.7, 1.8);
  draw();
}, { passive: false });

document.querySelectorAll("[data-mode]").forEach((button) => button.addEventListener("click", () => {
  state.mode = button.dataset.mode;
  document.querySelectorAll("[data-mode]").forEach((item) => {
    const active = item.dataset.mode === state.mode;
    item.classList.toggle("is-active", active);
    item.setAttribute("aria-pressed", String(active));
  });
  canvasStatus.textContent = `${state.mode} projection / synthetic fixture`;
  draw();
}));

function togglePlaying() {
  state.playing = !state.playing;
  playButton.setAttribute("aria-pressed", String(state.playing));
  playButton.querySelector(".play-icon").textContent = state.playing ? "Ⅱ" : "▶";
  document.getElementById("playLabel").textContent = state.playing ? "pause path" : "replay path";
  timelinePlay.innerHTML = state.playing ? "Ⅱ" : "<span aria-hidden=\"true\">▶</span>";
  if (state.playing) requestAnimationFrame(animate);
}

function animate() {
  if (!state.playing) return;
  state.layer = state.layer >= LAYER_COUNT - 1 ? 0 : state.layer + 1;
  slider.value = String(state.layer);
  updateReadout(); draw();
  window.setTimeout(() => requestAnimationFrame(animate), 52);
}
playButton.addEventListener("click", togglePlaying);
timelinePlay.addEventListener("click", togglePlaying);
slider.addEventListener("input", () => {
  state.layer = Number(slider.value);
  state.proposedOffset = { x: 0, y: 0 };
  canvasStatus.textContent = `Layer ${state.layer} / 77 selected`;
  updateReadout(); draw();
});

commitButton.addEventListener("click", () => {
  const dose = Math.hypot(state.proposedOffset.x, state.proposedOffset.y);
  if (dose < 0.01) return;
  state.committedPushes.push({ pathId: state.selectedPath, layer: state.layer, x: state.proposedOffset.x, y: state.proposedOffset.y });
  state.proposedOffset = { x: 0, y: 0 };
  canvasStatus.textContent = `Committed visual annotation / token ${String(selectedPath().token).padStart(3, "0")}`;
  updateReadout(); draw();
});

document.getElementById("resetButton").addEventListener("click", () => {
  state.proposedOffset = { x: 0, y: 0 };
  state.committedPushes = [];
  state.zoom = 1;
  state.pan = { x: 0, y: 0 };
  canvasStatus.textContent = "Synthetic fixture / select a ribbon";
  updateReadout(); draw();
});

window.addEventListener("resize", resizeCanvas);
updateReadout();
resizeCanvas();
