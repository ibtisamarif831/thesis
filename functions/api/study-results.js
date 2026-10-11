import { admin, body, fail, handle, json } from '../lib/pilot.js';

function csvCell(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export async function onRequestGet({ request, env }) {
  const authorization = request.headers.get("Authorization") || "";
  if (!env.STUDY_ADMIN_KEY || authorization !== `Bearer ${env.STUDY_ADMIN_KEY}`) {
    return Response.json({ error: "Unauthorized." }, { status: 401, headers: { "Cache-Control": "no-store" } });
  }
  const result = await env.STUDY_SELECTION_DB.prepare(`
    SELECT s.reviewer_code, s.submission_id, s.selection_version,
           s.created_at, s.updated_at, c.set_id, c.selection_order, c.icon_id, i.label
    FROM study_submissions s
    JOIN study_selections c ON c.submission_id=s.submission_id
    JOIN study_icons i ON i.icon_id=c.icon_id
    ORDER BY s.updated_at DESC, s.reviewer_code, c.set_id, c.selection_order
  `).all();
  const rows = result.results || [];
  if ((request.headers.get("Accept") || "").includes("application/json")) {
    const submissions = [];
    const bySubmission = new Map();
    for (const row of rows) {
      let submission = bySubmission.get(row.submission_id);
      if (!submission) {
        submission = {
          reviewer_code: row.reviewer_code,
          submission_id: row.submission_id,
          selection_version: row.selection_version,
          created_at: row.created_at,
          updated_at: row.updated_at,
          selections: {},
        };
        bySubmission.set(row.submission_id, submission);
        submissions.push(submission);
      }
      (submission.selections[row.set_id] ||= []).push({
        selection_order: row.selection_order,
        icon_id: row.icon_id,
        label: row.label,
      });
    }
    return Response.json({
      generated_at: new Date().toISOString(),
      submission_count: submissions.length,
      selection_count: rows.length,
      submissions,
    }, { headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });
  }
  const columns = [
    "reviewer_code", "submission_id", "selection_version", "created_at",
    "updated_at", "set_id", "selection_order", "icon_id", "label",
  ];
  const lines = [columns.join(",")];
  for (const row of rows) lines.push(columns.map((column) => csvCell(row[column])).join(","));
  return new Response(lines.join("\n") + "\n", {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": 'attachment; filename="glyph-study-selections.csv"',
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

export function onRequestPost({ request, env }) {
  return handle(async () => {
    admin(request, env);
    const data = await body(request);
    if (data.action !== 'delete' || ![data.submission_id, data.updated_at].every(value => typeof value === 'string' && value.length > 0 && value.length <= 100)) {
      fail('Invalid submission deletion request.');
    }
    // One conditional statement prevents deleting a reviewer update unseen by the admin.
    // study_selections cascade; pilot provenance is an independent frozen JSON snapshot.
    const result = await env.STUDY_SELECTION_DB.prepare(
      'DELETE FROM study_submissions WHERE submission_id=? AND updated_at=?'
    ).bind(data.submission_id, data.updated_at).run();
    if (!result.meta.changes) fail('Submission changed or was already deleted. Refresh submissions before trying again.', 409);
    return json({ ok: true, submission_id: data.submission_id });
  });
}
