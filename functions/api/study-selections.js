const REQUIRED_SETS = [
  "02_aiga_dot_symbol_signs",
  "04_ocha_humanitarian_icons",
  "09_universal_symbols_healthcare_webfont",
  "11_iso_7010_safety_signs",
  "12_iso_15223_medical_device_symbols",
];

function json(body, status = 200) {
  return Response.json(body, {
    status,
    headers: {
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

function sameOrigin(request) {
  const origin = request.headers.get("Origin");
  return !origin || origin === new URL(request.url).origin;
}

function validSelections(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  if (Object.keys(value).sort().join("|") !== [...REQUIRED_SETS].sort().join("|")) return false;
  return REQUIRED_SETS.every((setId) => {
    const ids = value[setId];
    return Array.isArray(ids) && ids.length === 20 && new Set(ids).size === 20
      && ids.every((id) => typeof id === "string" && id.length >= 12 && id.length <= 100);
  });
}

async function validateCatalog(db, selections) {
  const expected = new Map();
  for (const setId of REQUIRED_SETS) {
    for (const iconId of selections[setId]) expected.set(iconId, setId);
  }
  const ids = [...expected.keys()];
  const found = new Map();
  for (let offset = 0; offset < ids.length; offset += 40) {
    const chunk = ids.slice(offset, offset + 40);
    const placeholders = chunk.map(() => "?").join(",");
    const result = await db.prepare(
      `SELECT icon_id, set_id FROM study_icons WHERE icon_id IN (${placeholders})`
    ).bind(...chunk).all();
    for (const row of result.results || []) found.set(row.icon_id, row.set_id);
  }
  return ids.length === 100 && ids.every((id) => found.get(id) === expected.get(id));
}

function selectionInsert(db, submissionId, rows) {
  const values = rows.map(() => "(?,?,?,?)").join(",");
  const bindings = rows.flatMap((row) => [submissionId, row.setId, row.iconId, row.order]);
  return db.prepare(
    `INSERT INTO study_selections (submission_id,set_id,icon_id,selection_order) VALUES ${values}`
  ).bind(...bindings);
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!sameOrigin(request)) return json({ error: "Cross-origin submission is not allowed." }, 403);
  if (!env.STUDY_SUBMIT_KEY || request.headers.get("X-Study-Key") !== env.STUDY_SUBMIT_KEY) {
    return json({ error: "The study access code is incorrect." }, 401);
  }
  const contentLength = Number(request.headers.get("Content-Length") || 0);
  if (contentLength > 64_000) return json({ error: "Submission is too large." }, 413);

  let payload;
  try {
    payload = await request.json();
  } catch (_) {
    return json({ error: "Invalid JSON request." }, 400);
  }
  const reviewerCode = String(payload.reviewer_code || "").trim().toLowerCase();
  const rationale = String(payload.rationale || "").trim();
  if (!/^[a-z0-9][a-z0-9_-]{2,39}$/.test(reviewerCode)) {
    return json({ error: "Use a 3-40 character anonymous reviewer code containing letters, numbers, hyphens, or underscores." }, 400);
  }
  if (rationale.length > 2000) return json({ error: "Rationale must be 2,000 characters or fewer." }, 400);
  if (payload.selection_version !== "five-sets-20-v1" || !validSelections(payload.selections)) {
    return json({ error: "Select exactly 20 unique icons from each of the five datasets." }, 400);
  }
  if (!(await validateCatalog(env.STUDY_SELECTION_DB, payload.selections))) {
    return json({ error: "One or more selected icons are not in the approved five-dataset catalog." }, 400);
  }

  const existing = await env.STUDY_SELECTION_DB.prepare(
    "SELECT submission_id, created_at FROM study_submissions WHERE reviewer_code=?"
  ).bind(reviewerCode).first();
  const submissionId = existing?.submission_id || crypto.randomUUID();
  const now = new Date().toISOString();
  const statements = [
    env.STUDY_SELECTION_DB.prepare(
      "INSERT INTO study_submissions (submission_id,reviewer_code,selection_version,rationale,created_at,updated_at) VALUES (?,?,?,?,?,?) ON CONFLICT(reviewer_code) DO UPDATE SET selection_version=excluded.selection_version,rationale=excluded.rationale,updated_at=excluded.updated_at"
    ).bind(submissionId, reviewerCode, payload.selection_version, rationale, existing?.created_at || now, now),
    env.STUDY_SELECTION_DB.prepare("DELETE FROM study_selections WHERE submission_id=?").bind(submissionId),
  ];
  const rows = [];
  for (const setId of REQUIRED_SETS) {
    payload.selections[setId].forEach((iconId, index) => rows.push({ setId, iconId, order: index + 1 }));
  }
  for (let offset = 0; offset < rows.length; offset += 20) {
    statements.push(selectionInsert(env.STUDY_SELECTION_DB, submissionId, rows.slice(offset, offset + 20)));
  }
  await env.STUDY_SELECTION_DB.batch(statements);
  return json({
    ok: true,
    submission_id: submissionId,
    reviewer_code: reviewerCode,
    selected_icon_count: 100,
    updated_at: now,
    replaced_previous_submission: Boolean(existing),
  });
}

export function onRequestGet() {
  return json({ error: "Submission records are not public." }, 405);
}
