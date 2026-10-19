// Renders /api/quote, which prices everything with BlackScholes.py on Vercel.
"use strict";

const form = document.getElementById("inputs");
const main = document.getElementById("main");
const statusLine = document.getElementById("status");
const phone = window.matchMedia("(max-width: 720px)");
// Cell text is pure black or white: one of the two clears 4.5:1 on any fill.
const CELL_LIGHT = [255, 255, 255], CELL_DARK = [0, 0, 0];

const PAIRED = [
  ["Price", "c, p", "price", 4, "per share"],
  ["Delta", "Δ", "delta", 4, "per 1.00 of S"],
  ["Theta", "Θ", "theta", 4, "per calendar day"],
  ["Rho", "ρ", "rho", 4, "per 1% of r"],
];
const SHARED = [
  ["Gamma", "Γ", "gamma", 5, "per 1.00 of S"],
  ["Vega", "ν", "vega", 4, "per vol point"],
  ["Vanna", "", "vanna", 5, "Δ per vol point"],
  ["Volga", "", "volga", 6, "ν per vol point"],
  ["Charm", "", "charm", 6, "Δ per calendar day"],
];
// Heatmap ramp from the black ground up to pale spot blue.
const RAMP = [[15, 21, 32], [28, 53, 97], [61, 107, 192], [159, 192, 245], [232, 240, 255]];

const minus = (text) => text.replace(/-/g, "−");

function number(value, decimals) {
  if (value === "inf") return '<span class="inf">∞</span>';
  if (value === "-inf") return '−<span class="inf">∞</span>';
  if (value === undefined || value === null) return "—";
  return minus(value.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals }));
}

function difference(value) {
  if (value === null) return "limit, not bumped";
  if (value === 0) return "0";
  const [mantissa, exponent] = value.toExponential(1).split("e");
  return minus(`${mantissa}×10<sup>${Number(exponent)}</sup>`);
}

function row(name, symbol, unit, cells, check, extraClass = "") {
  const upright = /^[ΔΘΓ]$/.test(symbol) ? " upright" : "";  // capital Greek is set upright
  return `<tr${extraClass}><td class="quantity">${name}<span class="symbol${upright}">${symbol}</span>` +
    `<span class="unit-inline">${unit}</span></td>${cells}<td class="unit">${unit}</td>` +
    `<td class="check">${check}</td></tr>`;
}

function renderTable(quote) {
  const rows = PAIRED.map(([name, symbol, key, decimals, unit]) => {
    const call = quote ? (key === "price" ? quote.prices.call : quote.greeks[`call_${key}`]) : null;
    const put = quote ? (key === "price" ? quote.prices.put : quote.greeks[`put_${key}`]) : null;
    const dagger = key === "price" ? " †" : "";  // the price row is a parity residual, not a bump
    return row(name, symbol, unit, `<td>${number(call, decimals)}</td><td>${number(put, decimals)}</td>`,
      quote ? difference(quote.checks[key]) + dagger : "—");
  });
  SHARED.forEach(([name, symbol, key, decimals, unit], i) => {
    const value = quote ? quote.greeks[key] : null;
    rows.push(row(name, symbol, unit, `<td class="shared" colspan="2">${number(value, decimals)}</td>`,
      quote ? difference(quote.checks[key]) : "—", i === 0 ? ' class="midrule"' : ""));
  });
  document.getElementById("greeks").innerHTML = rows.join("");
}

function renderEquations(quote) {
  if (!window.katex) return;
  const { S, K, T, sigma, r } = quote.inputs;
  const c = quote.prices.call.toFixed(4), p = quote.prices.put.toFixed(4);
  const show = (id, tex) => katex.render(tex, document.getElementById(id), { displayMode: true, throwOnError: false });
  const d = document.getElementById("eq-d");
  if (quote.degenerate) {
    show("eq-call", String.raw`c = \max(S - K e^{-rT}, 0) = ${c} \tag{1}`);
    show("eq-put", String.raw`p = \max(K e^{-rT} - S, 0) = ${p} \tag{2}`);
    d.hidden = true;
  } else {
    show("eq-call", String.raw`c = S\,N(d_1) - K e^{-rT} N(d_2) = ${c} \tag{1}`);
    show("eq-put", String.raw`p = K e^{-rT} N(-d_2) - S\,N(-d_1) = ${p} \tag{2}`);
    show("eq-d", String.raw`d_{1,2} = \frac{\ln(S/K) + \left(r \pm \tfrac{1}{2}\sigma^2\right)T}{\sigma\sqrt{T}} \tag{3}`);
    d.hidden = false;
  }
  const lead = quote.degenerate
    ? "With σ√T = 0 the payoff is certain, so each option is worth its discounted intrinsic value and Table 1 reports each Greek's limit. Here"
    : "where";
  document.getElementById("where").textContent = minus(
    `${lead} S = ${S.toFixed(2)}, K = ${K.toFixed(2)}, T = ${T.toFixed(2)}, σ = ${sigma.toFixed(2)} and r = ${r.toFixed(2)}.`);
}

function rampColor(t) {
  const scaled = Math.min(Math.max(t, 0), 1) * (RAMP.length - 1);
  const i = Math.min(Math.floor(scaled), RAMP.length - 2), f = scaled - i;
  return RAMP[i].map((channel, k) => Math.round(channel + (RAMP[i + 1][k] - channel) * f));
}

// WCAG relative luminance, used to pick whichever text color contrasts more with a cell.
function luminance(rgb) {
  const [r, g, b] = rgb.map((c) => {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
const contrast = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);

function textOn(rgb) {
  const l = luminance(rgb);
  return contrast(l, 1) >= contrast(l, 0) ? CELL_LIGHT : CELL_DARK;
}

function position(value, axis) {
  const n = axis.length, step = (axis[n - 1] - axis[0]) / (n - 1);
  return ((value - axis[0]) / step + 0.5) / n * 100;
}

function renderHeatmap(id, grid, values, quote) {
  const flat = values.flat(), low = Math.min(...flat), high = Math.max(...flat);
  const n = grid.spots.length;
  const decimals = phone.matches ? 1 : 2;  // narrow cells get one decimal
  let cells = "";
  for (let row = n - 1; row >= 0; row--) {  // volatility increases upward
    for (let col = 0; col < n; col++) {
      const value = values[row][col];
      const fill = rampColor(high > low ? (value - low) / (high - low) : 0);
      cells += `<div class="cell" style="background:rgb(${fill.join(",")});color:rgb(${textOn(fill).join(",")})">${value.toFixed(decimals)}</div>`;
    }
  }
  const { S, sigma } = quote.inputs;
  let marker = "";
  if (S >= grid.spots[0] && S <= grid.spots[n - 1] && sigma >= grid.vols[0] && sigma <= grid.vols[n - 1]) {
    marker = `<span class="marker" style="left:${position(S, grid.spots)}%;top:${100 - position(sigma, grid.vols)}%"></span>`;
  }
  const yLabels = grid.vols.slice().reverse().map((v) => `<span>${v.toFixed(2)}</span>`).join("");
  const xLabels = grid.spots.map((s) => `<span>${s.toFixed(0)}</span>`).join("");
  const stops = RAMP.slice().reverse().map((c) => `rgb(${c.join(",")})`).join(",");
  document.getElementById(id).innerHTML =
    `<span class="y-title">σ</span>` +
    `<div class="y-axis">${yLabels}</div>` +
    `<div class="cells">${cells}${marker}</div>` +
    `<div class="legend" style="background:linear-gradient(${stops})"></div>` +
    `<div class="legend-labels"><span>${high.toFixed(1)}</span><span>${low.toFixed(1)}</span></div>` +
    `<div class="x-axis">${xLabels}</div><span class="x-title">Spot S</span>`;
}

function render(quote) {
  renderEquations(quote);
  renderTable(quote);
  renderHeatmap("heat-call", quote.heatmap, quote.heatmap.call, quote);
  renderHeatmap("heat-put", quote.heatmap, quote.heatmap.put, quote);
  const { K, T, r } = quote.inputs;
  document.querySelectorAll(".conditions").forEach((el) => {
    el.textContent = minus(`K = ${K.toFixed(2)}, T = ${T.toFixed(2)} and r = ${r.toFixed(2)}`);
  });
  const infinite = Object.values(quote.greeks).some((v) => typeof v === "string");
  document.getElementById("limits-note").hidden = !(quote.degenerate || infinite);
}

let pending = null;
let timer = null;

async function update() {
  const params = new URLSearchParams();
  let missing = null;
  for (const input of form.elements) {
    if (!input.name) continue;
    const empty = input.value.trim() === "";
    input.setAttribute("aria-invalid", String(empty));
    if (empty && !missing) missing = input.closest("label").querySelector("span").textContent.trim();
    params.set(input.name, input.value);
  }
  if (missing) {
    statusLine.textContent = `Enter a number for ${missing}.`;
    statusLine.classList.add("error");
    return;
  }
  pending?.abort();
  pending = new AbortController();
  main.classList.add("stale");
  main.setAttribute("aria-busy", "true");
  try {
    const response = await fetch(`/api/quote?${params}`, { signal: pending.signal });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error || `the pricing service returned ${response.status}`);
    render(body);
    statusLine.textContent = "";
    statusLine.classList.remove("error");
  } catch (error) {
    if (error.name === "AbortError") return;
    statusLine.textContent = `Could not price these inputs: ${error.message}.`;
    statusLine.classList.add("error");
  }
  main.classList.remove("stale");
  main.setAttribute("aria-busy", "false");
}

form.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(update, 250);
});
form.addEventListener("submit", (event) => event.preventDefault());

// On phones the heatmap ranges start folded behind a toggle; wider screens always show them.
const ranges = document.getElementById("ranges");
const toggle = document.querySelector(".ranges-toggle");
function setRanges(open) {
  ranges.hidden = !open;
  toggle.setAttribute("aria-expanded", String(open));
}
toggle.addEventListener("click", () => setRanges(ranges.hidden));
phone.addEventListener("change", () => setRanges(!phone.matches));
setRanges(!phone.matches);

renderTable(null);
update();
