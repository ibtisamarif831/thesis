import { body, fail, handle, json, interruption, session } from '../lib/pilot.js';
export function onRequestPost({ request, env }) { return handle(async () => {
  const data = await body(request), row = await session(request, env, data.session_id), db = env.STUDY_SELECTION_DB;
  if (!['complete','end'].includes(data.action)) fail('Invalid completion action.');
  const debrief = {};
  for (const key of ['difficulty','forgot','details']) { const value = data.debrief?.[key] ?? ''; if (typeof value !== 'string' || value.length > 1000) fail('Debrief answers must be at most 1,000 characters.'); debrief[key] = value; }
  if (row.status !== 'active') return json({ ok: true, status: row.status });
  const active = await db.prepare("SELECT attempt_id,trial_index FROM recognition_attempts WHERE session_id=? AND state='active'").bind(row.session_id).first();
  const history = active ? interruption('end', data.at_ms ?? 0, data.enlargements || [], JSON.parse(row.config_json), JSON.parse(row.schedule_json)[active.trial_index]) : {reason:'end',at_ms:0,enlargements:[]};
  const now = new Date().toISOString(), status = data.action === 'complete' ? 'completed' : 'ended';
  const results = await db.batch([
    db.prepare(`UPDATE recognition_sessions SET status=?,completed_at=?,last_activity_at=?,debrief_json=? WHERE session_id=? AND status='active'
      AND (?='ended' OR (SELECT COUNT(*) FROM recognition_attempts WHERE session_id=? AND state='answered')=?)`)
      .bind(status, now, now, JSON.stringify(debrief), row.session_id, status, row.session_id, JSON.parse(row.schedule_json).length),
    db.prepare(`UPDATE recognition_attempts SET state='interrupted',interruption_json=?,received_at=? WHERE session_id=? AND state='active'
      AND EXISTS(SELECT 1 FROM recognition_sessions WHERE session_id=? AND status='ended')`).bind(JSON.stringify(history), now, row.session_id, row.session_id),
  ]);
  if (!results[0].meta.changes) fail('Finish all trials before completion.', 409);
  return json({ ok: true, status });
}); }
