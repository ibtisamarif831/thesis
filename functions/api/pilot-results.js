import { admin, fail, handle, json, isControlled } from '../lib/pilot.js';
function tally(rows, key) { const result = {}; for (const r of rows) { const v = key(r); result[v] = (result[v] || 0) + 1; } return result; }
export function csvCell(value) {
  let text = typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value ?? '');
  if (/^[\s]*[=+@-]/.test(text) || /^[\t\r\n]/.test(text)) text = "'" + text;
  return '"' + text.replaceAll('"', '""') + '"';
}
export function onRequestGet({ request, env }) { return handle(async () => {
  admin(request, env); const query = new URL(request.url).searchParams, db = env.STUDY_SELECTION_DB;
  const pilot = await db.prepare('SELECT * FROM recognition_pilots WHERE pilot_id=?').bind(query.get('pilot_id') || '').first();
  if (!pilot) fail('Pilot not found.', 404);
  const sessions = (await db.prepare('SELECT session_id,pilot_id,schedule_json,viewport_json,started_at,last_activity_at,completed_at,status,debrief_json FROM recognition_sessions WHERE pilot_id=? ORDER BY started_at').bind(pilot.pilot_id).all()).results
    .map(({ schedule_json, viewport_json, debrief_json, ...row }) => ({ ...row, schedule: JSON.parse(schedule_json), viewport: JSON.parse(viewport_json), debrief: debrief_json ? JSON.parse(debrief_json) : null }));
  const attempts = (await db.prepare('SELECT a.* FROM recognition_attempts a JOIN recognition_sessions s USING(session_id) WHERE s.pilot_id=? ORDER BY a.session_id,a.trial_index,a.started_at,a.attempt_id').bind(pilot.pilot_id).all()).results
    .map(({ grid_json, response_json, interruption_json, ...row }) => ({ ...row, grid: JSON.parse(grid_json), response: response_json ? JSON.parse(response_json) : null, interruption: interruption_json ? JSON.parse(interruption_json) : null }));
  const config = JSON.parse(pilot.config_json), controlled = isControlled(config);
  const collisionsFor = a => {
    const size = a.response?.assigned_size ?? sessions.find(s => s.session_id === a.session_id)?.schedule[a.trial_index]?.assigned_size;
    return config.collision_diagnostics?.filter(c => c.target_id === a.target_id && c.size === size) ?? null;
  };
  const by_size = {};
  const recorded = attempts.filter(a => a.phase === 'recorded' && a.state === 'answered');
  const clean = recorded.filter(a => !a.repeated_exposure);
  const summary = { sessions: sessions.length, session_status: tally(sessions, s => s.status), practice_answers: attempts.filter(a => a.phase === 'practice' && a.state === 'answered').length,
    interrupted_attempts: attempts.filter(a => a.state === 'interrupted').length, recorded_answers: recorded.length, excluded_repeated_exposure: recorded.length - clean.length,
    eligible_recorded_answers: clean.length, correct: clean.filter(a => a.correct).length, accuracy: clean.length ? clean.filter(a => a.correct).length / clean.length : null,
    unidentified: clean.filter(a => a.response.category === 'unidentified').length, size_label: controlled ? 'assigned icon size (CSS pixels)' : 'historical size chosen before answering',
    chosen_sizes: tally(clean, a => a.response.final_size), enlargement_counts: tally(clean, a => a.response.enlargements.length), confidence: tally(clean.filter(a => a.response.confidence !== null), a => a.response.confidence),
    confusion: tally(clean, a => `${a.target_id} → ${a.response.selected_id || '[unidentified]'}`) };
  summary.selection_rule_version = config.selection_rule_version ?? 'legacy';
  summary.schedule_rule_version = config.schedule_rule_version ?? 'legacy';
  summary.collision_check_status = Array.isArray(config.collision_diagnostics) ? 'checked' : 'not checked';
  summary.collision_label = 'standardized rendering collision diagnostics';
  summary.collision_pair_count = config.collision_diagnostics?.length ?? null;
  summary.collision_target_size_count = config.collision_diagnostics ? new Set(config.collision_diagnostics.map(c => `${c.target_id}:${c.size}`)).size : null;
  summary.eligible_collision_answers = config.collision_diagnostics ? clean.filter(a => collisionsFor(a)?.length).length : null;
  if (controlled) {
    for (const size of config.size_levels) {
      const rows = clean.filter(a => a.response.assigned_size === size);
      const times = rows.map(a => a.response.response_time_ms).sort((a,b) => a-b);
      by_size[size] = {n:rows.length, correct:rows.filter(a => a.correct).length, accuracy:rows.length ? rows.filter(a => a.correct).length/rows.length : null,
        unidentified:rows.filter(a => a.response.category === 'unidentified').length,
        median_response_time_ms:times.length ? (times[Math.floor((times.length-1)/2)] + times[Math.floor(times.length/2)])/2 : null};
    }
    summary.by_size = by_size;
    summary.protocol_version = config.protocol_version;
    summary.chance_accuracy = 0.2;
  }
  if (query.get('format') === 'csv') {
    const columns = ['session_id','attempt_id','phase','trial_index','target_id','protocol_version','set_id','selection_rule_version','schedule_rule_version','collision_check_status','collision_pairs','target_collision','assigned_size','selected_position','response_time_ms','choice_onset_ms','input_method','state','repeated_exposure','category','selected_id','correct','confidence','final_size','duration_ms','enlargements','interruption','grid','started_at','received_at'];
    const lines = [columns.map(csvCell).join(',')];
    for (const a of attempts) { const r = { ...a, ...a.response, selection_rule_version:summary.selection_rule_version, schedule_rule_version:summary.schedule_rule_version, collision_check_status:summary.collision_check_status, collision_pairs:collisionsFor(a), target_collision:collisionsFor(a)?.some(c => c.target_involved) ?? null, protocol_version:config.protocol_version, set_id:config.source.set_id, assigned_size: a.response?.assigned_size ?? sessions.find(s => s.session_id === a.session_id)?.schedule[a.trial_index]?.assigned_size };  lines.push(columns.map(c => csvCell(r[c])).join(',')); }
    return new Response(lines.join('\r\n') + '\r\n', { headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'attachment; filename="pilot-trials.csv"', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' } });
  }
  const result = { pilot: { ...pilot, config: JSON.parse(pilot.config_json) }, summary };
  if (query.get('format') === 'full') Object.assign(result, { sessions, attempts });
  return json(result);
}); }
