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
    SELECT s.reviewer_code, s.submission_id, s.selection_version, s.rationale,
           s.created_at, s.updated_at, c.set_id, c.selection_order, c.icon_id, i.label
    FROM study_submissions s
    JOIN study_selections c ON c.submission_id=s.submission_id
    JOIN study_icons i ON i.icon_id=c.icon_id
    ORDER BY s.updated_at, s.reviewer_code, c.set_id, c.selection_order
  `).all();
  const columns = [
    "reviewer_code", "submission_id", "selection_version", "rationale", "created_at",
    "updated_at", "set_id", "selection_order", "icon_id", "label",
  ];
  const lines = [columns.join(",")];
  for (const row of result.results || []) lines.push(columns.map((column) => csvCell(row[column])).join(","));
  return new Response(lines.join("\n") + "\n", {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": 'attachment; filename="glyph-study-selections.csv"',
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

export function onRequestPost() {
  return Response.json({ error: "Method not allowed." }, { status: 405 });
}
