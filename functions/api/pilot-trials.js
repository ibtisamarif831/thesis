import { body, fail, handle, json, interruption, session, sessionView, validateResponse } from '../lib/pilot.js';
export function onRequestPost({ request, env }) { return handle(async () => {
  const data = await body(request), db = env.STUDY_SELECTION_DB, row = await session(request, env, data.session_id);
  if (!/^[a-f0-9-]{36}$/.test(data.attempt_id || '')) fail('Invalid attempt ID.');
  const view = await sessionView(db, row), assigned = view.schedule[view.next_trial], now = new Date().toISOString();
  const prior = await db.prepare('SELECT * FROM recognition_attempts WHERE attempt_id=? AND session_id=?').bind(data.attempt_id, row.session_id).first();
  if (data.action === 'answer' && prior?.state === 'answered') {
    const saved = validateResponse(data.response || {}, view.schedule[prior.trial_index], view.config);
    if (JSON.stringify(saved) !== prior.response_json) fail('An accepted answer cannot be changed.', 409);
    return json({ ok: true, correct: prior.phase === 'practice' ? Boolean(prior.correct) : undefined });
  }
  if (data.action === 'interrupt' && prior?.state === 'interrupted') return json({ ok: true });
  if (row.status !== 'active') fail('Session has ended.', 409);
  if (data.action === 'start') {
    if (!assigned || data.trial_index !== view.next_trial) fail('Unexpected trial.', 409);
    if (prior) { if (prior.state !== 'active' || prior.trial_index !== assigned.trial_index) fail('Attempt already used.', 409); return json({ ok: true, attempt_id: prior.attempt_id }); }
    if (view.attempts.some(a => a.state === 'active')) fail('Restart the interrupted attempt first.', 409);
    const repeated = view.attempts.some(a => a.trial_index === assigned.trial_index);
    const result = await db.prepare(`INSERT INTO recognition_attempts(attempt_id,session_id,trial_index,phase,target_id,grid_json,repeated_exposure,started_at)
      SELECT ?,?,?,?,?,?,?,? WHERE EXISTS(SELECT 1 FROM recognition_sessions WHERE session_id=? AND status='active')
      AND (SELECT COUNT(*) FROM recognition_attempts WHERE session_id=? AND state='answered')=?`)
      .bind(data.attempt_id, row.session_id, assigned.trial_index, assigned.phase, assigned.target_id, JSON.stringify(assigned.grid), Number(repeated), now, row.session_id, row.session_id, assigned.trial_index).run();
    if (!result.meta.changes) fail('Session state changed. Resume.', 409);
    return json({ ok: true, attempt_id: data.attempt_id });
  }
  if (!prior || prior.state !== 'active' || prior.trial_index !== view.next_trial) fail('Attempt is not active.', 409);
  let statement;
  if (data.action === 'interrupt') {
    const history = interruption(data.reason, data.at_ms, data.enlargements || [], view.config, assigned);
    statement = db.prepare("UPDATE recognition_attempts SET state='interrupted',interruption_json=?,received_at=? WHERE attempt_id=? AND state='active'").bind(JSON.stringify(history), now, prior.attempt_id);
  } else if (data.action === 'answer') {
    const response = validateResponse(data.response || {}, assigned, view.config);
    const correct = response.category === 'selected' && response.selected_id === assigned.target_id;
    statement = db.prepare("UPDATE recognition_attempts SET state='answered',response_json=?,correct=?,received_at=? WHERE attempt_id=? AND state='active' AND EXISTS(SELECT 1 FROM recognition_sessions WHERE session_id=? AND status='active')")
      .bind(JSON.stringify(response), Number(correct), now, prior.attempt_id, row.session_id);
  } else fail('Unknown trial action.');
  const results = await db.batch([statement, db.prepare('UPDATE recognition_sessions SET last_activity_at=? WHERE session_id=?').bind(now, row.session_id)]);
  if (!results[0].meta.changes) fail('Attempt state changed. Resume.', 409);
  return json({ ok: true, correct: data.action === 'answer' && assigned.phase === 'practice' ? data.response.category === 'selected' && data.response.selected_id === assigned.target_id : undefined });
}); }
