// 培養模擬器的計算核心：和 code/dfba.py 的 mode="table" 完全相同的演算法。
// TABLES（pFBA 查表）與 LAYOUT（代謝圖版面）由 build.py 內嵌。
"use strict";

const DEFAULTS = {
  T: 37, pH: 7, G0: 60, X0: 0.05, otr: 30, t_sw: 1e9, t_end: 24, lag: 1, dt: 0.05,
  vmax_glc: 10, km_glc: 0.015, vmax_ac: 4, km_ac: 0.5, vmax_o2: 15,
  Tmin: 5, Topt: 39, Tmax: 47, pHmin: 4, pHopt: 7, pHmax: 9.5, stage2: {},
};

function ctmi(T, Tmin, Topt, Tmax) {
  if (T <= Tmin || T >= Tmax) return 0;
  const num = (T - Tmax) * (T - Tmin) ** 2;
  const den = (Topt - Tmin) * ((Topt - Tmin) * (T - Topt) - (Topt - Tmax) * (Topt + Tmin - 2 * T));
  return Math.max(0, num / den);
}

function cpmi(pH, pHmin, pHopt, pHmax) {
  if (pH <= pHmin || pH >= pHmax) return 0;
  const num = (pH - pHmin) * (pH - pHmax);
  return Math.max(0, num / (num - (pH - pHopt) ** 2));
}

function baranyiAlpha(t, lag, nu = 1) {
  if (lag <= 0) return 1;
  const q0 = 1 / (Math.exp(lag * nu) - 1);
  const q = q0 * Math.exp(nu * t);
  return q / (1 + q);
}

function bilinear(ga, gb, arr, a, b) {
  a = Math.min(Math.max(a, ga[0]), ga[ga.length - 1]);
  b = Math.min(Math.max(b, gb[0]), gb[gb.length - 1]);
  const da = ga[1] - ga[0], db = gb[1] - gb[0];
  const i = Math.min(Math.floor((a - ga[0]) / da), ga.length - 2);
  const j = Math.min(Math.floor((b - gb[0]) / db), gb.length - 2);
  const u = (a - ga[i]) / da, v = (b - gb[j]) / db;
  const at = (x, y) => arr[x][y];
  const mix = (f) => (1 - u) * (1 - v) * f(i, j) + u * (1 - v) * f(i + 1, j) + (1 - u) * v * f(i, j + 1) + u * v * f(i + 1, j + 1);
  return mix(at);
}

function lookup(phase, s, o2) {
  const t = TABLES;
  const ga = phase === "glucose" ? t.glc_grid : t.ac_grid;
  const out = {};
  for (const f of t.fields) out[f] = bilinear(ga, t.o2_grid, t[phase][f], s, o2);
  return out.mu <= 1e-6 ? null : out;
}

function lookupMap(phase, s, o2) {
  const t = TABLES;
  const ga = phase === "glucose" ? t.glc_grid : t.ac_grid;
  const m = t[phase + "_map"];
  const out = {};
  t.map_rxns.forEach((r, k) => {
    out[r] = bilinear(ga, t.o2_grid, m.map((row) => row.map((cell) => cell[k])), s, o2);
  });
  return out;
}

function simulate(params) {
  const p = Object.assign({}, DEFAULTS, params);
  const n = Math.round(p.t_end / p.dt) + 1;
  const q = Object.assign({}, p, p.stage2 || {});
  const env1 = ctmi(p.T, p.Tmin, p.Topt, p.Tmax) * cpmi(p.pH, p.pHmin, p.pHopt, p.pHmax);
  const env2 = ctmi(q.T, p.Tmin, p.Topt, p.Tmax) * cpmi(q.pH, p.pHmin, p.pHopt, p.pHmax);
  const hasOtr2 = p.stage2 && "otr" in p.stage2;
  const out = { t: [], X: [], G: [], A: [], E: [], F: [], mu: [], our: [], cer: [], phase: [], sub: [], s: [], o2cap: [] };
  let X = p.X0, G = p.G0, A = 0, E = 0, F = 0;
  for (let k = 0; k < n; k++) {
    const t = k * p.dt;
    const alpha = baranyiAlpha(t, p.lag);
    const aerobic = t < p.t_sw;
    const fEnv = (aerobic ? env1 : env2) * alpha;
    const otr = aerobic ? p.otr : (hasOtr2 ? q.otr : 0);
    const o2cap = Math.min(p.vmax_o2, otr / Math.max(X, 1e-9));
    let sub = "none", s = 0;
    if (G > 1e-6) {
      sub = "glucose";
      s = Math.min(fEnv * p.vmax_glc * G / (p.km_glc + G), G / (X * p.dt));
    } else if (A > 1e-6) {
      sub = "acetate";
      s = Math.min(fEnv * p.vmax_ac * A / (p.km_ac + A), A / (X * p.dt));
    }
    let r = sub !== "none" && s > 1e-9 ? lookup(sub, s, o2cap) : null;
    if (!r) r = { mu: 0, glc: 0, o2: 0, ac: 0, etoh: 0, for: 0, lac: 0, succ: 0, co2: 0 };
    const mu = r.mu, qo2 = -r.o2;
    const o2lim = otr > 0 && o2cap < p.vmax_o2 - 1e-6 && qo2 >= o2cap - 1e-3 && mu > 0;
    let label;
    if (alpha < 0.5 && mu > 0) label = "遲滯期";
    else if (mu <= 1e-4) label = "停滯期";
    else if (sub === "acetate") label = "回頭吃乙酸";
    else if (otr <= 0) label = "厭氧發酵";
    else if (o2lim) label = "缺氧・溢流代謝";
    else label = "好氧指數生長";
    out.t.push(t); out.X.push(X); out.G.push(G); out.A.push(A); out.E.push(E); out.F.push(F);
    out.mu.push(mu); out.our.push(qo2 * X); out.cer.push(r.co2 * X); out.phase.push(label);
    out.sub.push(r.mu > 0 ? sub : "none"); out.s.push(s); out.o2cap.push(o2cap);
    const dX = mu * X * p.dt;
    G = Math.max(0, G + r.glc * X * p.dt);
    A = Math.max(0, A + r.ac * X * p.dt);
    E += Math.max(0, r.etoh) * X * p.dt;
    F += Math.max(0, r.for) * X * p.dt;
    X += dX;
  }
  out.params = p;
  return out;
}

function summary(sim) {
  const last = sim.t.length - 1;
  const used = sim.params.G0 - sim.G[last];
  let tOut = null;
  for (let k = 0; k < sim.G.length; k++) if (sim.G[k] <= 1) { tOut = sim.t[k]; break; }  // 剩不到 1 mM 視為吃完
  return {
    X_end: sim.X[last], E_end: sim.E[last], A_max: Math.max(...sim.A), A_end: sim.A[last],
    glc_left: sim.G[last], Y_E_G: used > 0 ? sim.E[last] / used : 0, t_glc_out: tOut,
  };
}

if (typeof module !== "undefined") module.exports = { simulate, summary, lookupMap, ctmi, cpmi, setTables: (t) => { globalThis.TABLES = t; } };
