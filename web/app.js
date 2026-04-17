// CFB → NFL Talent Tracker — client app.
// Views: leaderboard, year, program, compare. Hash-routed.

const METRIC_LABELS = {
  nfl_players: "NFL players",
  pro_bowls: "Pro Bowls",
  pro_bowl_players: "Pro Bowl players",
  all_pros: "All-Pros",
  all_pro_players: "All-Pro players",
};

const state = {
  data: null,            // { leaderboard, byYear, byProgram, meta }
  yearMin: 2000,
  yearMax: 2024,
  rankThreshold: 25,
  metric: "nfl_players",
  sort: { key: "nfl_players", dir: "desc" },
  selectedYear: 2024,
  selectedProgram: null,
  compareList: [],
  charts: {},            // { viewName: Chart }
};

async function loadAll() {
  const [leaderboard, byYear, byProgram, meta] = await Promise.all([
    fetch("data/leaderboard.json").then(r => r.json()),
    fetch("data/by_year.json").then(r => r.json()),
    fetch("data/by_program.json").then(r => r.json()),
    fetch("data/meta.json").then(r => r.json()),
  ]);
  state.data = { leaderboard, byYear, byProgram, meta };
  state.yearMin = meta.year_range[0];
  state.yearMax = meta.year_range[1];
  state.selectedYear = meta.year_range[1];
  document.getElementById("yr-min").min = state.yearMin;
  document.getElementById("yr-min").max = state.yearMax;
  document.getElementById("yr-min").value = state.yearMin;
  document.getElementById("yr-max").min = state.yearMin;
  document.getElementById("yr-max").max = state.yearMax;
  document.getElementById("yr-max").value = state.yearMax;
  document.getElementById("yr-min-lbl").textContent = state.yearMin;
  document.getElementById("yr-max-lbl").textContent = state.yearMax;

  document.getElementById("last-updated").textContent = new Date(meta.last_updated).toLocaleString();
  const ol = document.getElementById("caveats-list");
  ol.innerHTML = "";
  meta.caveats.forEach(c => { const li = document.createElement("li"); li.textContent = c; ol.appendChild(li); });

  document.getElementById("loading").classList.add("hidden");
}

// ────── filter helpers ──────
function yearInRange(y) { return y >= state.yearMin && y <= state.yearMax; }
function rankOk(rank) { return rank != null && rank <= state.rankThreshold; }

function leaderboardFiltered() {
  const rows = [];
  for (const [yStr, progs] of Object.entries(state.data.byYear)) {
    const yr = +yStr;
    if (!yearInRange(yr)) continue;
    for (const r of progs) {
      if (!rankOk(r.ap_rank)) continue;
      rows.push({
        program: r.program,
        season: yr,
        ap_rank: r.ap_rank,
        nfl_players: r.nfl_players,
        pro_bowls: r.pro_bowls,
        pro_bowl_players: r.pro_bowl_players ?? 0,
        all_pros: r.all_pros,
        all_pro_players: r.all_pro_players ?? 0,
      });
    }
  }
  return rows;
}

// ────── router ──────
function parseHash() {
  const h = location.hash || "#/leaderboard";
  const [path, query = ""] = h.split("?");
  const parts = path.replace(/^#\//, "").split("/");
  const params = new URLSearchParams(query);
  return { view: parts[0] || "leaderboard", arg: parts[1] || null, params };
}

function go(viewPath) { location.hash = viewPath; }

function render() {
  if (!state.data) return;
  const { view, arg, params } = parseHash();

  // activate nav
  for (const a of document.querySelectorAll(".nav a")) {
    a.classList.toggle("active", a.dataset.nav === view);
  }
  // hide all view containers
  for (const el of document.querySelectorAll(".view")) el.classList.add("hidden");

  // restore filters from query if present
  if (params.has("ymin")) state.yearMin = +params.get("ymin");
  if (params.has("ymax")) state.yearMax = +params.get("ymax");
  if (params.has("rank")) state.rankThreshold = +params.get("rank");
  if (params.has("metric")) state.metric = params.get("metric");
  syncFilterInputs();

  switch (view) {
    case "leaderboard": return renderLeaderboard();
    case "year":        return renderYear(arg ? +arg : state.selectedYear);
    case "program":     return renderProgram(arg ? decodeURIComponent(arg) : null);
    case "compare":     return renderCompare(params.get("p"));
    default:            return renderLeaderboard();
  }
}

function syncFilterInputs() {
  document.getElementById("yr-min").value = state.yearMin;
  document.getElementById("yr-max").value = state.yearMax;
  document.getElementById("yr-min-lbl").textContent = state.yearMin;
  document.getElementById("yr-max-lbl").textContent = state.yearMax;
  document.getElementById("rank-threshold").value = state.rankThreshold;
  for (const b of document.querySelectorAll(".seg-btn")) {
    b.classList.toggle("active", b.dataset.metric === state.metric);
  }
}

// ────── view: LEADERBOARD ──────
function renderLeaderboard() {
  const el = document.getElementById("view-leaderboard");
  el.classList.remove("hidden");
  const rows = leaderboardFiltered();
  const { key, dir } = state.sort;
  rows.sort((a, b) => {
    const av = a[key], bv = b[key];
    if (typeof av === "string") return dir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
    return dir === "asc" ? av - bv : bv - av;
  });

  const metric = state.metric;
  const cols = [
    { key: "program", label: "Program" },
    { key: "season", label: "Season", num: true },
    { key: "ap_rank", label: "AP Rank", num: true },
    { key: "nfl_players", label: "NFL Players", num: true, primary: metric === "nfl_players" },
    { key: "pro_bowls", label: "Pro Bowls", num: true, primary: metric === "pro_bowls", title: "Total Pro Bowl selections (career)" },
    { key: "pro_bowl_players", label: "PB Players", num: true, primary: metric === "pro_bowl_players", title: "Distinct players with ≥1 Pro Bowl selection" },
    { key: "all_pros", label: "All-Pros", num: true, primary: metric === "all_pros", title: "Total All-Pro selections (career)" },
    { key: "all_pro_players", label: "AP Players", num: true, primary: metric === "all_pro_players", title: "Distinct players with ≥1 All-Pro selection" },
  ];

  el.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            ${cols.map(c => {
              const cls = "sortable" + (state.sort.key === c.key ? " sorted-" + state.sort.dir : "");
              const t = c.title ? ` title="${c.title}"` : "";
              return `<th class="${cls}" data-sort="${c.key}"${t}>${c.label}</th>`;
            }).join("")}
          </tr>
        </thead>
        <tbody>
          ${rows.map((r, i) => `
            <tr data-program="${encodeURIComponent(r.program)}" data-season="${r.season}">
              <td class="num">${i + 1}</td>
              <td>${r.program}</td>
              <td class="num">${r.season}</td>
              <td class="num">${r.ap_rank ?? "—"}</td>
              <td class="num${cols[3].primary ? " primary" : ""}">${r.nfl_players}</td>
              <td class="num${cols[4].primary ? " primary" : ""}">${r.pro_bowls}</td>
              <td class="num${cols[5].primary ? " primary" : ""}">${r.pro_bowl_players}</td>
              <td class="num${cols[6].primary ? " primary" : ""}">${r.all_pros}</td>
              <td class="num${cols[7].primary ? " primary" : ""}">${r.all_pro_players}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;

  for (const th of el.querySelectorAll("th[data-sort]")) {
    th.addEventListener("click", () => {
      const k = th.dataset.sort;
      if (state.sort.key === k) state.sort.dir = state.sort.dir === "asc" ? "desc" : "asc";
      else { state.sort.key = k; state.sort.dir = k === "program" ? "asc" : "desc"; }
      renderLeaderboard();
    });
  }
  for (const tr of el.querySelectorAll("tbody tr")) {
    tr.addEventListener("click", () => go(`#/program/${tr.dataset.program}`));
  }
}

// ────── view: YEAR ──────
function renderYear(year) {
  const el = document.getElementById("view-year");
  el.classList.remove("hidden");
  state.selectedYear = year;

  const years = Object.keys(state.data.byYear).map(Number).sort((a, b) => a - b);
  const rows = (state.data.byYear[String(year)] || []).filter(r => rankOk(r.ap_rank));
  const metric = state.metric;

  el.innerHTML = `
    <div class="year-header">
      <h2>${year} AP Top 25</h2>
      <label for="year-pick" class="muted">Season</label>
      <select id="year-pick">
        ${years.map(y => `<option value="${y}" ${y === year ? "selected" : ""}>${y}</option>`).join("")}
      </select>
    </div>
    <div class="chart-wrap">
      <canvas id="year-chart" height="${Math.max(260, rows.length * 22)}"></canvas>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>AP Rank</th>
            <th>Program</th>
            <th>NFL Players</th>
            <th title="Total Pro Bowl selections (career)">Pro Bowls</th>
            <th title="Distinct players with ≥1 Pro Bowl selection">PB Players</th>
            <th title="Total All-Pro selections (career)">All-Pros</th>
            <th title="Distinct players with ≥1 All-Pro selection">AP Players</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(r => `
            <tr data-program="${encodeURIComponent(r.program)}">
              <td class="num">${r.ap_rank ?? "—"}</td>
              <td>${r.program}</td>
              <td class="num">${r.nfl_players}</td>
              <td class="num">${r.pro_bowls}</td>
              <td class="num">${r.pro_bowl_players ?? 0}</td>
              <td class="num">${r.all_pros}</td>
              <td class="num">${r.all_pro_players ?? 0}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;

  document.getElementById("year-pick").addEventListener("change", e => go(`#/year/${e.target.value}`));
  for (const tr of el.querySelectorAll("tbody tr")) {
    tr.addEventListener("click", () => go(`#/program/${tr.dataset.program}`));
  }

  // Bar chart
  const sorted = [...rows].sort((a, b) => (b[metric] || 0) - (a[metric] || 0));
  renderChart("year", document.getElementById("year-chart"), {
    type: "bar",
    data: {
      labels: sorted.map(r => r.program),
      datasets: [{
        label: METRIC_LABELS[metric],
        data: sorted.map(r => r[metric] || 0),
        backgroundColor: "#f97316",
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, title: { display: true, text: `${year}: ${METRIC_LABELS[metric]} by program`, color: "#d7dde4" } },
      scales: {
        x: { ticks: { color: "#8b949e" }, grid: { color: "#2a323d" } },
        y: { ticks: { color: "#d7dde4" }, grid: { display: false } },
      },
    },
  });
}

// ────── view: PROGRAM ──────
function renderProgram(name) {
  const el = document.getElementById("view-program");
  el.classList.remove("hidden");

  const programs = state.data.meta.programs || Object.keys(state.data.byProgram);
  if (!name || !state.data.byProgram[name]) {
    el.innerHTML = `
      <h2>Select a program</h2>
      <p class="status">Pick any program from the list to see year-by-year detail.</p>
      <div class="chips">
        ${programs.map(p => `<button class="chip ghost" data-prog="${encodeURIComponent(p)}">${p}</button>`).join("")}
      </div>
    `;
    for (const b of el.querySelectorAll(".chip")) b.addEventListener("click", () => go(`#/program/${b.dataset.prog}`));
    return;
  }

  state.selectedProgram = name;
  const p = state.data.byProgram[name];
  const yearEntries = Object.entries(p.years)
    .map(([y, v]) => ({ year: +y, ...v }))
    .filter(e => yearInRange(e.year) && rankOk(e.ap_rank))
    .sort((a, b) => a.year - b.year);

  const totalPlayers = yearEntries.reduce((s, e) => s + e.nfl_players, 0);
  const allPlayers = yearEntries.flatMap(e => (e.players || []).map(pl => ({ ...pl, year: e.year })));
  const dedupPlayers = new Map();
  for (const pl of allPlayers) {
    const key = pl.name;
    const prev = dedupPlayers.get(key);
    if (!prev || pl.year < prev.year) dedupPlayers.set(key, pl);
  }
  const playersArr = [...dedupPlayers.values()];
  const totalPB = playersArr.reduce((s, pl) => s + (pl.pro_bowls || 0), 0);
  const totalAP = playersArr.reduce((s, pl) => s + (pl.all_pros || 0), 0);
  const pbPlayers = playersArr.filter(pl => (pl.pro_bowls || 0) > 0).length;
  const apPlayers = playersArr.filter(pl => (pl.all_pros || 0) > 0).length;

  el.innerHTML = `
    <div class="program-header">
      <div>
        <h2>${name}</h2>
        <div class="muted">${yearEntries.length} top-${state.rankThreshold} seasons in range ${state.yearMin}–${state.yearMax}</div>
      </div>
      <div class="stat-row">
        <div class="stat"><span class="label">Unique players</span><span class="value">${dedupPlayers.size}</span></div>
        <div class="stat" title="Distinct players with ≥1 Pro Bowl selection"><span class="label">PB players</span><span class="value">${pbPlayers}</span></div>
        <div class="stat" title="Total Pro Bowl selections (career)"><span class="label">Pro Bowls</span><span class="value">${totalPB}</span></div>
        <div class="stat" title="Distinct players with ≥1 All-Pro selection"><span class="label">AP players</span><span class="value">${apPlayers}</span></div>
        <div class="stat" title="Total All-Pro selections (career)"><span class="label">All-Pros</span><span class="value">${totalAP}</span></div>
      </div>
    </div>
    <div class="chart-wrap">
      <canvas id="program-chart" height="300"></canvas>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Season</th>
            <th>AP Rank</th>
            <th>NFL Players</th>
            <th>Roster</th>
          </tr>
        </thead>
        <tbody>
          ${yearEntries.map(e => `
            <tr>
              <td class="num">${e.year}</td>
              <td class="num">${e.ap_rank ?? "—"}</td>
              <td class="num">${e.nfl_players}</td>
              <td>${(e.players || []).sort((a,b) => (b.pro_bowls||0) - (a.pro_bowls||0) || a.name.localeCompare(b.name)).map(pl => pl.pro_bowls > 0 ? `<strong>${pl.name}</strong> <span class="muted">(${pl.pro_bowls} PB${pl.all_pros ? `, ${pl.all_pros} AP` : ""})</span>` : pl.name).join(", ")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;

  renderChart("program", document.getElementById("program-chart"), {
    type: "line",
    data: {
      labels: yearEntries.map(e => e.year),
      datasets: [{
        label: METRIC_LABELS[state.metric],
        data: yearEntries.map(e => e[state.metric] || 0),
        borderColor: "#f97316",
        backgroundColor: "rgba(249,115,22,0.2)",
        fill: true,
        tension: 0.25,
        pointRadius: 4,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, title: { display: true, text: `${name}: ${METRIC_LABELS[state.metric]} per top-${state.rankThreshold} season`, color: "#d7dde4" } },
      scales: {
        x: { ticks: { color: "#8b949e" }, grid: { color: "#2a323d" } },
        y: { beginAtZero: true, ticks: { color: "#8b949e" }, grid: { color: "#2a323d" } },
      },
    },
  });
}

// ────── view: COMPARE ──────
const COMPARE_COLORS = ["#f97316", "#60a5fa", "#34d399", "#a78bfa"];

function renderCompare(paramList) {
  const el = document.getElementById("view-compare");
  el.classList.remove("hidden");
  if (paramList) state.compareList = paramList.split(",").map(decodeURIComponent).filter(Boolean).slice(0, 4);

  const programs = state.data.meta.programs || Object.keys(state.data.byProgram);

  el.innerHTML = `
    <div class="compare-picker">
      <label>Programs (up to 4):</label>
      <div class="chips" id="compare-selected">
        ${state.compareList.map(p => `<button class="chip" data-rm="${encodeURIComponent(p)}">${p} ×</button>`).join("")}
        ${state.compareList.length === 0 ? `<span class="muted">Select at least 2 programs below.</span>` : ""}
      </div>
      <div class="chips" style="margin-top:10px">
        ${programs.filter(p => !state.compareList.includes(p)).map(p => `<button class="chip ghost" data-add="${encodeURIComponent(p)}">+ ${p}</button>`).join("")}
      </div>
    </div>
    <div class="chart-wrap">
      <canvas id="compare-chart" height="320"></canvas>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Program</th>
            <th>Top-25 Seasons</th>
            <th>NFL Players</th>
            <th title="Total Pro Bowl selections (career)">Pro Bowls</th>
            <th title="Distinct players with ≥1 Pro Bowl selection">PB Players</th>
            <th title="Total All-Pro selections (career)">All-Pros</th>
            <th title="Distinct players with ≥1 All-Pro selection">AP Players</th>
          </tr>
        </thead>
        <tbody id="compare-tbody"></tbody>
      </table>
    </div>
  `;

  for (const b of el.querySelectorAll("[data-add]")) b.addEventListener("click", () => {
    const p = decodeURIComponent(b.dataset.add);
    if (state.compareList.length >= 4) return;
    state.compareList.push(p);
    go(`#/compare?p=${state.compareList.map(encodeURIComponent).join(",")}`);
  });
  for (const b of el.querySelectorAll("[data-rm]")) b.addEventListener("click", () => {
    const p = decodeURIComponent(b.dataset.rm);
    state.compareList = state.compareList.filter(x => x !== p);
    go(`#/compare${state.compareList.length ? "?p=" + state.compareList.map(encodeURIComponent).join(",") : ""}`);
  });

  // Build datasets
  const datasets = state.compareList.map((name, i) => {
    const p = state.data.byProgram[name];
    if (!p) return null;
    const entries = Object.entries(p.years)
      .map(([y, v]) => ({ year: +y, ...v }))
      .filter(e => yearInRange(e.year) && rankOk(e.ap_rank))
      .sort((a, b) => a.year - b.year);
    return {
      label: name,
      data: entries.map(e => ({ x: e.year, y: e[state.metric] || 0 })),
      borderColor: COMPARE_COLORS[i % COMPARE_COLORS.length],
      backgroundColor: COMPARE_COLORS[i % COMPARE_COLORS.length] + "33",
      tension: 0.25,
      pointRadius: 3,
    };
  }).filter(Boolean);

  renderChart("compare", document.getElementById("compare-chart"), {
    type: "line",
    data: { datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: "top", labels: { color: "#d7dde4" } }, title: { display: true, text: `Head-to-head: ${METRIC_LABELS[state.metric]} per top-${state.rankThreshold} season`, color: "#d7dde4" } },
      scales: {
        x: { type: "linear", min: state.yearMin, max: state.yearMax, ticks: { color: "#8b949e", stepSize: 1, callback: v => v }, grid: { color: "#2a323d" } },
        y: { beginAtZero: true, ticks: { color: "#8b949e" }, grid: { color: "#2a323d" } },
      },
    },
  });

  // Summary table
  const tbody = document.getElementById("compare-tbody");
  tbody.innerHTML = state.compareList.map(name => {
    const p = state.data.byProgram[name];
    if (!p) return "";
    let nfl = 0, pb = 0, ap = 0, pbp = 0, app_ = 0, seasons = 0;
    for (const [yStr, y] of Object.entries(p.years)) {
      const yr = +yStr;
      if (!yearInRange(yr) || !rankOk(y.ap_rank)) continue;
      nfl += y.nfl_players; pb += y.pro_bowls || 0; ap += y.all_pros || 0;
      pbp += y.pro_bowl_players || 0; app_ += y.all_pro_players || 0; seasons += 1;
    }
    return `<tr><td>${name}</td><td class="num">${seasons}</td><td class="num">${nfl}</td><td class="num">${pb}</td><td class="num">${pbp}</td><td class="num">${ap}</td><td class="num">${app_}</td></tr>`;
  }).join("");
}

// ────── chart helper ──────
function renderChart(viewName, canvas, config) {
  if (state.charts[viewName]) state.charts[viewName].destroy();
  state.charts[viewName] = new Chart(canvas.getContext("2d"), config);
}

// ────── wiring ──────
function wireFilters() {
  const yMin = document.getElementById("yr-min");
  const yMax = document.getElementById("yr-max");
  function onYr() {
    let a = +yMin.value, b = +yMax.value;
    if (a > b) { if (event && event.target === yMin) yMax.value = a; else yMin.value = b; a = +yMin.value; b = +yMax.value; }
    state.yearMin = a; state.yearMax = b;
    document.getElementById("yr-min-lbl").textContent = a;
    document.getElementById("yr-max-lbl").textContent = b;
    render();
  }
  yMin.addEventListener("input", onYr);
  yMax.addEventListener("input", onYr);

  document.getElementById("rank-threshold").addEventListener("change", e => {
    state.rankThreshold = +e.target.value;
    render();
  });

  for (const b of document.querySelectorAll(".seg-btn")) {
    b.addEventListener("click", () => {
      state.metric = b.dataset.metric;
      for (const x of document.querySelectorAll(".seg-btn")) x.classList.toggle("active", x === b);
      render();
    });
  }
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", async () => {
  wireFilters();
  try {
    await loadAll();
  } catch (e) {
    document.getElementById("loading").textContent = "Failed to load data — run `python -m pipeline.cli` first. " + e;
    return;
  }
  render();
});
