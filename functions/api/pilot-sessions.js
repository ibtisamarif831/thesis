import { body, fail, handle, hash, json, participantConfig, requireControlled, schedule, session, sessionView, token } from '../lib/pilot.js';
export function onRequestGet({ request, env }) { return handle(async () => {
  const query = new URL(request.url).searchParams;
  if (query.has('session_id')) return json(await sessionView(env.STUDY_SELECTION_DB, await session(request, env, query.get('session_id'))));
  const row = await env.STUDY_SELECTION_DB.prepare('SELECT config_json,title,closed_at FROM recognition_pilots WHERE invitation=?').bind(query.get('pilot') || '').first();
  if (!row) fail('Invitation not found.', 404);
  requireControlled(JSON.parse(row.config_json));
  return json({ title: row.title, open: !row.closed_at, config: participantConfig(JSON.parse(row.config_json)) });
}); }
export function onRequestPost({ request, env }) { return handle(async () => {
  const data = await body(request); const db = env.STUDY_SELECTION_DB;
  if (typeof data.pilot !== 'string' || !/^[a-f0-9]{64}$/.test(data.pilot)) fail('Invalid invitation.');
  const row = await db.prepare('SELECT * FROM recognition_pilots WHERE invitation=?').bind(data.pilot || '').first();
  if (!row) fail('Invitation not found.', 404);
  requireControlled(JSON.parse(row.config_json)); if (row.closed_at) fail('This pilot is closed to new sessions.', 410);
  const v = data.viewport;
  if (!v || ![v.width, v.height].every(n => Number.isInteger(n) && n > 0 && n <= 20000) || typeof v.dpr !== 'number' || !Number.isFinite(v.dpr) || v.dpr <= 0 || v.dpr > 20) fail('Invalid viewport.');
  const session_id = crypto.randomUUID(), credential = token(), now = new Date().toISOString();
  const config = JSON.parse(row.config_json);
  const result = await db.prepare(`INSERT INTO recognition_sessions(session_id,pilot_id,credential_hash,schedule_json,viewport_json,started_at,last_activity_at)
    SELECT ?,?,?,?,?,?,? WHERE EXISTS(SELECT 1 FROM recognition_pilots WHERE pilot_id=? AND closed_at IS NULL)`)
    .bind(session_id, row.pilot_id, await hash(credential), JSON.stringify(schedule(config.icons.map(i => i.icon_id), config)), JSON.stringify({ width: v.width, height: v.height, dpr: v.dpr }), now, now, row.pilot_id).run();
  if (!result.meta.changes) fail('This pilot is closed.', 410);
  return json({ session_id, credential }, 201);
}); }
