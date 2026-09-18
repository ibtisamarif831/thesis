const REQUIRED_PER_SET = 20;
const DRAFT_KEY = "glyph-study-selection-five-sets-20-v1";
let catalog = null;
let activeSetId = null;
let selected = {};

const byId = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[ch]));

function loadDraft() {
  try {
    const draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || "{}");
    selected = Object.fromEntries(catalog.sets.map((set) => [set.set_id, new Set(draft.selections?.[set.set_id] || [])]));
    byId("reviewerCode").value = draft.reviewer_code || "";
    byId("rationale").value = draft.rationale || "";
  } catch (_) {
    selected = Object.fromEntries(catalog.sets.map((set) => [set.set_id, new Set()]));
  }
}

function saveDraft() {
  localStorage.setItem(DRAFT_KEY, JSON.stringify({
    reviewer_code: byId("reviewerCode").value,
    rationale: byId("rationale").value,
    selections: Object.fromEntries(Object.entries(selected).map(([setId, ids]) => [setId, [...ids]])),
  }));
}

function totalSelected() { return Object.values(selected).reduce((sum, ids) => sum + ids.size, 0); }
function complete() { return catalog.sets.every((set) => selected[set.set_id].size === REQUIRED_PER_SET); }

function renderTabs() {
  byId("datasetTabs").innerHTML = catalog.sets.map((set) => {
    const count = selected[set.set_id].size;
    const classes = [set.set_id === activeSetId ? "active" : "", count === REQUIRED_PER_SET ? "complete" : ""].filter(Boolean).join(" ");
    return `<button type="button" class="${classes}" data-set-id="${escapeHtml(set.set_id)}">${escapeHtml(set.set_name)} · ${count}/${REQUIRED_PER_SET}</button>`;
  }).join("");
  byId("datasetTabs").querySelectorAll("button").forEach((button) => button.addEventListener("click", () => {
    activeSetId = button.dataset.setId;
    byId("searchInput").value = "";
    byId("selectedOnly").checked = false;
    render();
    scrollTo({ top: 0, behavior: "smooth" });
  }));
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
  byId("submitButton").disabled = !complete();
  byId("completionMessage").textContent = complete()
    ? "All five datasets are complete. Review your choices, then submit."
    : `${catalog.sets.filter((set) => selected[set.set_id].size === REQUIRED_PER_SET).length} of 5 datasets complete.`;
}

function render() { renderTabs(); renderGrid(); renderProgress(); }

function renderReview() {
  byId("reviewContent").innerHTML = catalog.sets.map((set) => {
    const iconMap = new Map(set.icons.map((icon) => [icon.icon_id, icon]));
    const cards = [...selected[set.set_id]].map((id) => iconMap.get(id)).filter(Boolean).map((icon) => `<figure><img src="${escapeHtml(icon.normalized_path)}" alt=""><figcaption title="${escapeHtml(icon.label)}">${escapeHtml(icon.label || icon.icon_id)}</figcaption></figure>`).join("");
    return `<section class="review-set"><h3>${escapeHtml(set.set_name)} · ${selected[set.set_id].size}/${REQUIRED_PER_SET}</h3><div class="review-grid">${cards}</div></section>`;
  }).join("");
  byId("reviewDialog").showModal();
}

async function submit(event) {
  event.preventDefault();
  if (!complete()) return;
  const status = byId("submitStatus");
  const button = byId("submitButton");
  status.className = "status";
  status.textContent = "Submitting…";
  button.disabled = true;
  try {
    const response = await fetch("/api/study-selections", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Study-Key": byId("accessCode").value },
      body: JSON.stringify({
        reviewer_code: byId("reviewerCode").value,
        selection_version: "five-sets-20-v1",
        rationale: byId("rationale").value,
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
    button.disabled = !complete();
  }
}

async function initialize() {
  const response = await fetch("study_selection_data.json", { cache: "no-store" });
  if (!response.ok) throw new Error("The study icon catalog could not be loaded.");
  catalog = await response.json();
  activeSetId = catalog.sets[0].set_id;
  loadDraft();
  render();
  byId("searchInput").addEventListener("input", renderGrid);
  byId("selectedOnly").addEventListener("change", renderGrid);
  byId("clearDataset").addEventListener("click", () => { selected[activeSetId].clear(); saveDraft(); render(); });
  byId("reviewButton").addEventListener("click", renderReview);
  byId("closeReview").addEventListener("click", () => byId("reviewDialog").close());
  byId("reviewerCode").addEventListener("input", saveDraft);
  byId("rationale").addEventListener("input", saveDraft);
  byId("submissionForm").addEventListener("submit", submit);
}

initialize().catch((error) => {
  byId("iconGrid").innerHTML = `<p>${escapeHtml(error.message)}</p>`;
});
