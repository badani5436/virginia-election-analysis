/* Independent election-analysis data display. Calculations originate in analyze.py. */
(() => {
  "use strict";
  const data = window.ELECTION_ANALYSIS;
  const $ = (id) => document.getElementById(id);
  if (!data || !Array.isArray(data.localities)) {
    document.querySelector("main").insertAdjacentHTML("afterbegin", '<p style="padding:20px;background:#fee">Election data could not be loaded. Please refresh or use the downloaded data file.</p>');
    return;
  }
  const state = data.state;
  const localityMap = new Map(data.localities.map((x) => [x.locality, x]));
  const fmt = (v) => Math.abs(v).toLocaleString("en-US");
  const signed = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + fmt(v);
  const pct = (v, digits = 1) => Number(v).toFixed(digits) + "%";
  const points = (v, digits = 1) => Number(v).toFixed(digits) + " pts";
  const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (x) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[x]);
  const shares = (rec) => ({ d: 100 * rec.dem / rec.total, r: 100 * rec.rep / rec.total, o: 100 * rec.other / rec.total });

  function voteBar(year, rec, margin) {
    const sh = shares(rec);
    return `<div class="vote-row"><span class="vote-year">${year}</span><div class="stack" role="img" aria-label="${year}: Democratic ${pct(sh.d)}, Republican ${pct(sh.r)}, other ${pct(sh.o)}"><span class="d" style="width:${sh.d}%"></span><span class="r" style="width:${sh.r}%"></span><span class="o" style="width:${sh.o}%"></span></div><div class="vote-margin"><strong>D+${Number(margin).toFixed(1)}</strong><small>statewide margin</small></div></div>`;
  }
  $("voteBars").innerHTML = voteBar(2020, state.year2020, state.margin20pp) + voteBar(2024, state.year2024, state.margin24pp);
  $("demLead").textContent = `${fmt(state.margin20votes)} → ${fmt(state.margin24votes)}`;
  $("stateSwing").textContent = points(state.swingToRpp, 2);
  $("ballotChange").textContent = signed(state.presVoteChangeVotes);
  $("erosionShare").textContent = pct(state.novaMarginErosionSharePct);
  $("ballotShare").textContent = pct(state.nova2024VoteSharePct);
  $("ballotShareText").textContent = pct(state.nova2024VoteSharePct);
  $("novaVotes").textContent = fmt(state.novaMarginErosion) + " votes";
  $("erosionRing").style.background = `conic-gradient(#c9684b 0% ${state.novaMarginErosionSharePct}%,#d8dede ${state.novaMarginErosionSharePct}% 100%)`;
  $("ballotRing").style.background = `conic-gradient(#18334b 0% ${state.nova2024VoteSharePct}%,#d8dede ${state.nova2024VoteSharePct}% 100%)`;

  const ranked = [...data.localities].sort((a, b) => b.marginErosionVotes - a.marginErosionVotes).slice(0, 8);
  const high = Math.max(...ranked.map((x) => x.marginErosionVotes));
  $("rankingChart").innerHTML = ranked.map((r) => `<div class="rank-row"><div class="rank-name">${escapeHtml(r.locality)}</div><div class="rank-bar-track"><div class="rank-bar" style="width:${Math.max(0, 100 * r.marginErosionVotes / high)}%"></div></div><div class="rank-value">${fmt(r.marginErosionVotes)}</div></div>`).join("");

  const search = $("localitySearch");
  const sort = $("sortMetric");
  const filter = $("regionFilter");
  const showMore = $("showMore");
  let visibleCount = 15;
  let selected = localityMap.get("Fairfax County") || data.localities[0];

  function getFiltered() {
    const q = search.value.trim().toLocaleLowerCase("en-US");
    const region = filter.value;
    const rows = data.localities.filter((r) => {
      if (q && !r.locality.toLocaleLowerCase("en-US").includes(q)) return false;
      if (region === "nova" && !r.novaCore) return false;
      if (region === "other" && r.novaCore) return false;
      return true;
    });
    const metric = sort.value;
    rows.sort((a, b) => {
      if (metric === "alpha") return a.locality.localeCompare(b.locality);
      const key = metric === "swing" ? "swingToRpp" : metric === "votechange" ? "presVoteChangeVotes" : "marginErosionVotes";
      return b[key] - a[key] || a.locality.localeCompare(b.locality);
    });
    return rows;
  }
  function deltaClass(v) { return v > 0 ? "value-positive" : v < 0 ? "value-negative" : ""; }
  function drawRows() {
    const list = getFiltered();
    $("localityTable").innerHTML = list.slice(0, visibleCount).map((r) => `<tr tabindex="0" role="button" aria-label="View ${escapeHtml(r.locality)} results" class="${r.locality === selected.locality ? "selected" : ""}" data-name="${escapeHtml(r.locality)}"><td>${escapeHtml(r.locality)}</td><td class="numeric ${deltaClass(r.swingToRpp)}">${Number(r.swingToRpp).toFixed(1)} pts</td><td class="numeric ${deltaClass(r.marginErosionVotes)}">${signed(r.marginErosionVotes)}</td><td class="numeric">${signed(r.presVoteChangeVotes)}</td></tr>`).join("") || '<tr><td colspan="4">No localities match. Try a different search.</td></tr>';
    $("rowCount").textContent = `Showing ${Math.min(visibleCount, list.length)} of ${list.length} localities`;
    showMore.disabled = visibleCount >= list.length;
    showMore.hidden = visibleCount >= list.length;
    $("localityTable").querySelectorAll("tr[data-name]").forEach((row) => {
      const activate = () => {
        selected = localityMap.get(row.dataset.name);
        drawDetail();
        drawRows();
      };
      row.addEventListener("click", activate);
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); activate(); }
      });
    });
  }
  function detailBar(year, votes, margin) {
    const sh = shares(votes);
    return `<div class="detail-compare"><div class="detail-compare-header"><span>${year}</span><span>${margin >= 0 ? "D+" : "R+"}${Math.abs(margin).toFixed(1)} points</span></div><div class="mini-track" role="img" aria-label="${year} Democratic share ${pct(sh.d)}, Republican share ${pct(sh.r)}"><span class="d" style="width:${sh.d}%"></span><span class="r" style="width:${sh.r}%"></span><span class="o" style="width:${sh.o}%"></span></div></div>`;
  }
  function drawDetail() {
    const r = selected;
    $("detailName").textContent = r.locality;
    $("detailSubtitle").textContent = r.novaCore ? "One of the five selected Northern Virginia localities" : "Virginia county or independent city";
    $("detailBars").innerHTML = detailBar(2020, r.year2020, r.margin20pp) + detailBar(2024, r.year2024, r.margin24pp);
    $("detailMetrics").innerHTML = `<div><span>R-ward D–R margin shift</span><strong>${points(r.swingToRpp)}</strong></div><div><span>D–R margin reduction</span><strong>${signed(r.marginErosionVotes)}</strong></div><div><span>Presidential votes, 2024</span><strong>${fmt(r.year2024.total)}</strong></div><div><span>Presidential votes change</span><strong>${signed(r.presVoteChangeVotes)}</strong></div>`;
  }
  for (const control of [search, sort, filter]) {
    control.addEventListener(control === search ? "input" : "change", () => {
      visibleCount = 15;
      drawRows();
    });
  }
  showMore.addEventListener("click", () => { visibleCount += 30; drawRows(); });
  drawRows();
  drawDetail();
})();
