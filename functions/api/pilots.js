import { selectAlternatives } from '../lib/controlled-pilot.js';
import { admin, body, fail, handle, json, PROTOCOL, token, validLevels } from '../lib/pilot.js';
export function onRequestGet({ request, env }) { return handle(async () => {
  admin(request, env); const id = new URL(request.url).searchParams.get('pilot_id');
  if (id) { const row = await env.STUDY_SELECTION_DB.prepare('SELECT * FROM recognition_pilots WHERE pilot_id=?').bind(id).first(); if (!row) fail('Pilot not found.', 404); return json({ ...row, config: JSON.parse(row.config_json) }); }
  const rows = await env.STUDY_SELECTION_DB.prepare("SELECT pilot_id,invitation,title,created_at,closed_at,json_extract(config_json, '$.protocol_version') AS protocol_version FROM recognition_pilots ORDER BY created_at DESC LIMIT 1000").all();
  return json({ pilots: rows.results });
}); }
export function onRequestPost({ request, env }) { return handle(async () => {
  admin(request, env); const data = await body(request); const db = env.STUDY_SELECTION_DB;
  if (data.action === 'close') {
    if (typeof data.pilot_id !== 'string' || data.pilot_id.length > 100) fail('Invalid pilot ID.');
    const result = await db.prepare('UPDATE recognition_pilots SET closed_at=COALESCE(closed_at,?) WHERE pilot_id=?').bind(new Date().toISOString(), data.pilot_id || '').run();
    if (!result.meta.changes) fail('Pilot not found.', 404); return json({ ok: true });
  }
  if (data.action === 'delete') {
    if (typeof data.pilot_id !== 'string' || data.pilot_id.length === 0 || data.pilot_id.length > 100) fail('Invalid pilot ID.');
    const pilot = await db.prepare('SELECT closed_at FROM recognition_pilots WHERE pilot_id=?').bind(data.pilot_id).first();
    if (!pilot) fail('Pilot not found.', 404);
    if (!pilot.closed_at) fail('Close the pilot before deleting it.', 409);
    // D1 batch is one transaction. Delete children first because the existing schema
    // deliberately has foreign keys without ON DELETE CASCADE.
    const results = await db.batch([
      db.prepare('DELETE FROM recognition_attempts WHERE session_id IN (SELECT session_id FROM recognition_sessions WHERE pilot_id=?)').bind(data.pilot_id),
      db.prepare('DELETE FROM recognition_sessions WHERE pilot_id=?').bind(data.pilot_id),
      db.prepare('DELETE FROM recognition_pilots WHERE pilot_id=? AND closed_at IS NOT NULL').bind(data.pilot_id),
    ]);
    if (!results[2].meta.changes) fail('Pilot not found. Refresh pilots and try again.', 404);
    return json({ ok: true, pilot_id: data.pilot_id });
  }
  if (data.protocol_version && data.protocol_version !== PROTOCOL) fail('Only the controlled protocol is available.');
  if (data.action !== 'create' || typeof data.title !== 'string' || !data.title.trim() || data.title.length > 120 || !validLevels(data.size_levels)) fail('Use a title and fixed sizes 6, 8, 10, 12, 14.');
  if (!Array.isArray(data.icon_ids) || data.icon_ids.length !== 20 || new Set(data.icon_ids).size !== 20 || !data.icon_ids.every(id => typeof id === 'string' && /^[a-f0-9]{16}$/.test(id))) fail('Exactly 20 unique valid icons are required.');
  if (![data.submission_id, data.set_id, data.updated_at].every(v => typeof v === 'string' && v.length > 0 && v.length <= 100)) fail('Invalid source provenance.');
  const source = await db.prepare('SELECT * FROM study_submissions WHERE submission_id=?').bind(data.submission_id || '').first();
  const rows = (await db.prepare('SELECT c.icon_id,i.label FROM study_selections c JOIN study_icons i ON i.icon_id=c.icon_id AND i.set_id=c.set_id WHERE c.submission_id=? AND c.set_id=? ORDER BY c.selection_order').bind(data.submission_id || '', data.set_id || '').all()).results;
  const signature = JSON.stringify(rows.map(r => r.icon_id));
  if (!source || source.updated_at !== data.updated_at || rows.length !== 20 || signature !== JSON.stringify(data.icon_ids)) fail('Selection changed. Refresh Results and reopen the dialog.', 409);
  const assets = await env.ASSETS.fetch(new URL('/study_selection_data.json', request.url));
  if (!assets.ok) fail('Stimulus catalog unavailable.', 503);
  const catalog = await assets.json(); const set = catalog.sets.find(s => s.set_id === data.set_id);
  const icons = rows.map(row => { const icon = set?.icons.find(i => i.icon_id === row.icon_id); if (!icon || !/^normalized_256\/[a-z0-9_]+\/[^/]+\.png$/.test(icon.normalized_path)) fail('Stimulus image missing from published catalog.'); return { ...row, features: icon.features, image: '/' + icon.normalized_path }; });
  const selectedCatalogIcons = rows.map(row => set.icons.find(i => i.icon_id === row.icon_id));
  const selection = selectAlternatives(selectedCatalogIcons, catalog.layout?.feature_ids);
  const config = { ...selection, familiarity: "no-full-set-preview", protocol_version: PROTOCOL, icons, size_levels: data.size_levels, exposure_ms: 1500, target_px: 128,
    source: { set_id: data.set_id, submission_id: source.submission_id, reviewer_code: source.reviewer_code, selection_version: source.selection_version, updated_at: source.updated_at } };
  const pilot_id = crypto.randomUUID(), invitation = token(), created_at = new Date().toISOString();
  // Snapshot check and insertion are a single statement: a concurrent reviewer edit cannot slip between them.
  const result = await db.prepare(`INSERT INTO recognition_pilots(pilot_id,invitation,title,config_json,created_at)
    SELECT ?,?,?,?,? WHERE EXISTS(SELECT 1 FROM study_submissions WHERE submission_id=? AND updated_at=? AND selection_version=?)
    AND (SELECT json_group_array(icon_id) FROM (SELECT icon_id FROM study_selections WHERE submission_id=? AND set_id=? ORDER BY selection_order))=?`)
    .bind(pilot_id, invitation, data.title.trim(), JSON.stringify(config), created_at, source.submission_id, source.updated_at, source.selection_version, source.submission_id, data.set_id, signature).run();
  if (!result.meta.changes) fail('Selection changed. Refresh Results.', 409);
  return json({ pilot_id, invitation, title: data.title.trim(), created_at, config }, 201);
}); }
