const REQUIRED_PER_SET = 20;
const DRAFT_KEY = "glyph-study-selection-five-sets-20-v1";
let catalog = null;
let activeSetId = null;
let selected = {};
let selectionDisplayMode = "grid";
let mapViewRevision = 0;

const byId = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[ch]));

function loadDraft() {
  try {
    const draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || "{}");
    selected = Object.fromEntries(catalog.sets.map((set) => [set.set_id, new Set(draft.selections?.[set.set_id] || [])]));
    byId("reviewerCode").value = draft.reviewer_code || "";
  } catch (_) {
    selected = Object.fromEntries(catalog.sets.map((set) => [set.set_id, new Set()]));
  }
}

function saveDraft() {
  localStorage.setItem(DRAFT_KEY, JSON.stringify({
    reviewer_code: byId("reviewerCode").value,
    selections: Object.fromEntries(Object.entries(selected).map(([setId, ids]) => [setId, [...ids]])),
  }));
}

function totalSelected() { return Object.values(selected).reduce((sum, ids) => sum + ids.size, 0); }
function complete() { return catalog.sets.every((set) => selected[set.set_id].size === REQUIRED_PER_SET); }

function renderDatasetSelect() {
  const select = byId("datasetSelect");
  select.innerHTML = catalog.sets.map((set) => {
    const count = selected[set.set_id].size;
    return `<option value="${escapeHtml(set.set_id)}">${escapeHtml(set.set_name)} · ${count}/${REQUIRED_PER_SET}</option>`;
  }).join("");
  select.value = activeSetId;
}

function renderGrid() {
  const set = catalog.sets.find((item) => item.set_id === activeSetId);
  const query = byId("searchInput").value.trim().toLowerCase();
  const selectedOnly = byId("selectedOnly").checked;
  const ids = selected[activeSetId];
  const icons = set.icons.filter((icon) => (!query || `${icon.label} ${icon.icon_id}`.toLowerCase().includes(query)) && (!selectedOnly || ids.has(icon.icon_id)));
  byId("datasetHeading").innerHTML = `<h2>${escapeHtml(set.set_name)} <small>(${set.icons.length} available)</small></h2><strong>${ids.size} / ${REQUIRED_PER_SET} selected</strong>`;
  byId("iconGrid").innerHTML = icons.map((icon) => {
    const chosen = ids.has(icon.icon_id);
    const order = chosen ? [...ids].indexOf(icon.icon_id) + 1 : "";
    return `<button type="button" class="icon-card" aria-pressed="${chosen}" data-icon-id="${escapeHtml(icon.icon_id)}" title="${escapeHtml(icon.label || icon.icon_id)}">
      ${chosen ? `<span class="selection-number">${order}</span>` : ""}
      <img src="${escapeHtml(icon.normalized_path)}" alt="" loading="lazy">
      <span class="label">${escapeHtml(icon.label || icon.icon_id)}</span>
    </button>`;
  }).join("") || '<p>No icons match the current filter.</p>';
  byId("iconGrid").querySelectorAll(".icon-card").forEach((card) => card.addEventListener("click", () => toggleIcon(card.dataset.iconId)));
}

function toggleIcon(iconId) {
  const ids = selected[activeSetId];
  if (ids.has(iconId)) ids.delete(iconId);
  else if (ids.size < REQUIRED_PER_SET) ids.add(iconId);
  else {
    byId("submitStatus").textContent = "This dataset already has 20 selections. Remove one before adding another.";
    byId("submitStatus").className = "status error";
    return;
  }
  byId("submitStatus").textContent = "";
  saveDraft();
  render();
}

function renderProgress() {
  const total = totalSelected();
  byId("overallCount").textContent = `${total} / 100`;
  byId("completionMessage").textContent = complete()
    ? "All five datasets are complete. Review your choices, then submit."
    : total
      ? `${total} icon${total === 1 ? "" : "s"} selected. You can submit now or continue selecting.`
      : "Select at least one icon to submit.";
}

function render() {
  renderDatasetSelect();
  renderGrid();
  renderProgress();
  renderSelectionView();
}

function renderSelectionView() {
  const showMap = selectionDisplayMode === "map";
  byId("gridViewButton").classList.toggle("active", !showMap);
  byId("mapViewButton").classList.toggle("active", showMap);
  byId("gridViewButton").setAttribute("aria-pressed", String(!showMap));
  byId("mapViewButton").setAttribute("aria-pressed", String(showMap));
  byId("gridToolbar").hidden = showMap;
  byId("iconGrid").hidden = showMap;
  byId("mapPanel").hidden = !showMap;
  byId("mapActions").hidden = !showMap;
  if (showMap) renderSmartMap();
}

function renderSmartMap() {
  const set = catalog.sets.find((item) => item.set_id === activeSetId);
  const ids = selected[activeSetId];
  const xs = set.icons.map((icon) => icon.feature_x);
  const ys = set.icons.map((icon) => icon.feature_y);
  const xSpan = Math.max(...xs) - Math.min(...xs) || 2;
  const ySpan = Math.max(...ys) - Math.min(...ys) || 2;
  const iconFraction = Math.min(0.075, Math.max(0.028, 0.065 * Math.sqrt(80 / set.icons.length)));
  const imageWidth = xSpan * iconFraction;
  const imageHeight = ySpan * iconFraction;
  const chosen = set.icons.filter((icon) => ids.has(icon.icon_id));
  const trace = {
    type: "scatter",
    mode: "markers",
    x: xs,
    y: ys,
    customdata: set.icons.map((icon) => [icon.icon_id, icon.label || icon.icon_id]),
    marker: { size: 34, color: "rgba(49,86,163,0.015)", line: { width: 0 } },
    hovertemplate: `<b>%{customdata[1]}</b><br>${escapeHtml(set.set_name)}<br>Feature PCA: %{x:.2f}, %{y:.2f}<extra></extra>`,
  };
  const layout = {
    margin: { l: 46, r: 24, t: 46, b: 48 },
    title: { text: `${set.set_name} · feature-space map · ${ids.size}/${REQUIRED_PER_SET} selected`, x: 0.02, xanchor: "left", font: { size: 16 } },
    paper_bgcolor: "white",
    plot_bgcolor: "#fbfcfe",
    hovermode: "closest",
    dragmode: "pan",
    uirevision: `${activeSetId}:${mapViewRevision}`,
    xaxis: { title: "Feature PCA 1", showgrid: true, zeroline: false, gridcolor: "#e7eaf0" },
    yaxis: { title: "Feature PCA 2", showgrid: true, zeroline: false, gridcolor: "#e7eaf0", scaleanchor: "x", scaleratio: 1 },
    images: set.icons.map((icon) => ({
      source: icon.normalized_path,
      xref: "x", yref: "y", x: icon.feature_x, y: icon.feature_y,
      sizex: imageWidth, sizey: imageHeight, xanchor: "center", yanchor: "middle",
      sizing: "contain", opacity: ids.has(icon.icon_id) ? 1 : 0.82, layer: "above",
    })),
    shapes: chosen.map((icon) => ({
      type: "circle", xref: "x", yref: "y",
      x0: icon.feature_x - imageWidth * 0.56, x1: icon.feature_x + imageWidth * 0.56,
      y0: icon.feature_y - imageHeight * 0.56, y1: icon.feature_y + imageHeight * 0.56,
      line: { color: "#3156a3", width: 3 }, fillcolor: "rgba(0,0,0,0)", layer: "above",
    })),
    annotations: chosen.map((icon) => ({
      xref: "x", yref: "y", x: icon.feature_x + imageWidth * 0.46, y: icon.feature_y + imageHeight * 0.46,
      text: String([...ids].indexOf(icon.icon_id) + 1), showarrow: false,
      bgcolor: "#3156a3", bordercolor: "#3156a3", borderpad: 4, font: { color: "white", size: 10 },
    })),
  };
  const map = byId("smartMap");
  Plotly.react(map, [trace], layout, {
    responsive: true,
    displaylogo: false,
    scrollZoom: true,
    modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d", "toggleSpikelines"],
  });
  if (typeof map.removeAllListeners === "function") map.removeAllListeners("plotly_click");
  map.on("plotly_click", (event) => {
    const iconId = event.points?.[0]?.customdata?.[0];
    if (iconId) toggleIcon(iconId);
  });
}

function setSelectionDisplayMode(mode) {
  selectionDisplayMode = mode;
  renderSelectionView();
}

function resetSmartMap() {
  mapViewRevision += 1;
  renderSmartMap();
}

function downloadSmartMap() {
  const set = catalog.sets.find((item) => item.set_id === activeSetId);
  const filename = `${set.set_id}-feature-map`;
  Plotly.downloadImage(byId("smartMap"), { format: "png", width: 1800, height: 1200, filename });
}

function setActiveView(view) {
  const showResults = view === "results", showPilots = view === "pilots";
  const showSelection = !showResults && !showPilots;
  for (const [id, active] of [["selectionViewTab", showSelection], ["resultsViewTab", showResults], ["pilotViewTab", showPilots]]) {
    byId(id).classList.toggle("active", active);
    byId(id).setAttribute("aria-selected", String(active));
  }
  byId("selectionNavigation").hidden = !showSelection;
  byId("selectionMain").hidden = !showSelection;
  byId("resultsView").hidden = !showResults;
  byId("pilotView").hidden = !showPilots;
  if (showResults) byId("resultsAccessKey").focus();
  if (showPilots) byId("pilotAccessKey").focus();
  if (showSelection && selectionDisplayMode === "map") {
    requestAnimationFrame(() => Plotly.Plots.resize(byId("smartMap")));
  }
  scrollTo({ top: 0, behavior: "smooth" });
}

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown time" : date.toLocaleString();
}

function renderResults(data) {
  byId("resultsSummary").hidden = false;
  byId("resultsSummary").innerHTML = `
    <div class="summary-card"><strong>${data.submission_count}</strong><span>reviewer submissions</span></div>
    <div class="summary-card"><strong>${data.selection_count}</strong><span>selected-icon rows</span></div>
    <div class="summary-card"><strong>${escapeHtml(formatDate(data.generated_at))}</strong><span>last refreshed</span></div>`;
  if (!data.submissions.length) {
    byId("resultsList").innerHTML = '<section class="result-card"><h3>No submissions yet</h3><p>Refresh again after a reviewer submits one or more selections.</p></section>';
    return;
  }
  const iconMaps = new Map(catalog.sets.map((set) => [set.set_id, new Map(set.icons.map((icon) => [icon.icon_id, icon]))]));
  byId("resultsList").innerHTML = data.submissions.map((submission, index) => {
    const setSections = catalog.sets.map((set) => {
      const rows = submission.selections[set.set_id] || [];
      const cards = rows.map((row) => {
        const icon = iconMaps.get(set.set_id).get(row.icon_id);
        const image = icon ? `<img src="${escapeHtml(icon.normalized_path)}" alt="" loading="lazy">` : '<div class="missing-result-image">Image unavailable</div>';
        return `<figure><span class="result-order">${row.selection_order}</span>${image}<figcaption title="${escapeHtml(row.label || row.icon_id)}">${escapeHtml(row.label || row.icon_id)}</figcaption></figure>`;
      }).join("");
      return `<section class="result-set"><h4>${escapeHtml(set.set_name)} · ${rows.length}/${REQUIRED_PER_SET}</h4><div class="result-grid">${cards}</div></section>`;
    }).join("");
    return `<article class="result-card">
      <header class="result-card-header">
        <div><h3>${escapeHtml(submission.reviewer_code)}</h3><p>Updated ${escapeHtml(formatDate(submission.updated_at))}</p></div>
        <div class="result-receipt">Receipt ${escapeHtml(submission.submission_id.slice(0, 8))}<br>First submitted ${escapeHtml(formatDate(submission.created_at))}<button type="button" class="danger" data-delete-submission="${index}">Delete submission</button></div>
      </header>
      ${setSections}
    </article>`;
  }).join("");
  byId("resultsList").querySelectorAll("[data-delete-submission]").forEach(button => {
    button.addEventListener("click", () => deleteSubmission(data.submissions[Number(button.dataset.deleteSubmission)], button));
  });
}

async function deleteSubmission(submission, button) {
  const count = Object.values(submission.selections).reduce((sum, rows) => sum + rows.length, 0);
  if (!confirm(`Delete submission from ${submission.reviewer_code} (${count} selected icons across all datasets)? This cannot be undone. Existing saved pilots and participant responses will be kept.`)) return;
  button.disabled = true;
  const status = byId("resultsStatus");
  try {
    const response = await fetch("/api/study-results", {
      method: "POST", cache: "no-store",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${byId("resultsAccessKey").value}` },
      body: JSON.stringify({ action: "delete", submission_id: submission.submission_id, updated_at: submission.updated_at }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Submission could not be deleted.");
    await refreshResults({ preventDefault() {} });
  } catch (error) {
    status.className = "results-status error";
    status.textContent = error.message;
  } finally { button.disabled = false; }
}

async function refreshResults(event) {
  event.preventDefault();
  const status = byId("resultsStatus");
  const button = byId("refreshResultsButton");
  status.className = "results-status";
  status.textContent = "Loading the latest submissions…";
  button.disabled = true;
  try {
    const response = await fetch("/api/study-results", {
      cache: "no-store",
      headers: {
        "Accept": "application/json",
        "Authorization": `Bearer ${byId("resultsAccessKey").value}`,
      },
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Results could not be loaded.");
    renderResults(result);
    renderPilotCreateButtons(result);
    status.className = "results-status success";
    status.textContent = `Loaded ${result.submission_count} current submission${result.submission_count === 1 ? "" : "s"}.`;
  } catch (error) {
    status.className = "results-status error";
    status.textContent = error.message === "Unauthorized." ? "The results access key is incorrect." : error.message;
  } finally {
    button.disabled = false;
  }
}

function renderReview() {
  byId("reviewContent").innerHTML = catalog.sets.map((set) => {
    const iconMap = new Map(set.icons.map((icon) => [icon.icon_id, icon]));
    const cards = [...selected[set.set_id]].map((id) => iconMap.get(id)).filter(Boolean).map((icon) => `<figure><img src="${escapeHtml(icon.normalized_path)}" alt=""><figcaption title="${escapeHtml(icon.label)}">${escapeHtml(icon.label || icon.icon_id)}</figcaption></figure>`).join("");
    return `<section class="review-set"><h3>${escapeHtml(set.set_name)} · ${selected[set.set_id].size}/${REQUIRED_PER_SET}</h3><div class="review-grid">${cards}</div></section>`;
  }).join("");
  byId("reviewDialog").showModal();
  requestAnimationFrame(() => byId("reviewerCode").focus());
}

async function submit(event) {
  event.preventDefault();
  const status = byId("submitStatus");
  const button = byId("submitButton");
  if (totalSelected() < 1) {
    status.className = "status error";
    status.textContent = "Select at least one icon before submitting.";
    return;
  }
  status.className = "status";
  status.textContent = "Submitting…";
  button.disabled = true;
  try {
    const response = await fetch("/api/study-selections", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Study-Key": byId("accessCode").value },
      body: JSON.stringify({
        reviewer_code: byId("reviewerCode").value,
        selection_version: "five-sets-up-to-20-v2",
        selections: Object.fromEntries(Object.entries(selected).map(([setId, ids]) => [setId, [...ids]])),
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Submission failed.");
    status.className = "status success";
    status.textContent = `${result.replaced_previous_submission ? "Updated" : "Submitted"} successfully. Receipt: ${result.submission_id.slice(0, 8)}.`;
    byId("accessCode").value = "";
  } catch (error) {
    status.className = "status error";
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function initialize() {
  const response = await fetch("study_selection_data.json", { cache: "no-store" });
  if (!response.ok) throw new Error("The study icon catalog could not be loaded.");
  catalog = await response.json();
  activeSetId = catalog.sets[0].set_id;
  loadDraft();
  render();
  byId("datasetSelect").addEventListener("change", (event) => {
    activeSetId = event.target.value;
    byId("searchInput").value = "";
    byId("selectedOnly").checked = false;
    render();
    scrollTo({ top: 0, behavior: "smooth" });
  });
  byId("searchInput").addEventListener("input", renderGrid);
  byId("selectedOnly").addEventListener("change", renderGrid);
  byId("clearDataset").addEventListener("click", () => { selected[activeSetId].clear(); saveDraft(); render(); });
  byId("reviewButton").addEventListener("click", renderReview);
  byId("closeReview").addEventListener("click", () => byId("reviewDialog").close());
  byId("reviewerCode").addEventListener("input", saveDraft);
  byId("submissionForm").addEventListener("submit", submit);
  byId("selectionViewTab").addEventListener("click", () => setActiveView("selection"));
  byId("resultsViewTab").addEventListener("click", () => setActiveView("results"));
  byId("resultsAccessForm").addEventListener("submit", refreshResults);
  byId("pilotViewTab").addEventListener("click", () => {
    if (!byId("pilotAccessKey").value) byId("pilotAccessKey").value = byId("resultsAccessKey").value;
    setActiveView("pilots");
  });
  byId("pilotAccessForm").addEventListener("submit", event => { event.preventDefault(); refreshPilots(); });
  byId("gridViewButton").addEventListener("click", () => setSelectionDisplayMode("grid"));
  byId("mapViewButton").addEventListener("click", () => setSelectionDisplayMode("map"));
  byId("resetMapButton").addEventListener("click", resetSmartMap);
  byId("downloadMapButton").addEventListener("click", downloadSmartMap);
  const initialView = new URLSearchParams(location.search).get("view");
  if (["results", "pilots"].includes(initialView)) setActiveView(initialView);
}

initialize().catch((error) => {
  byId("iconGrid").innerHTML = `<p>${escapeHtml(error.message)}</p>`;
});
