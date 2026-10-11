export const CONTROLLED_PROTOCOL = 'icon-recognition-controlled-v2';
export const isControlled = config => config.protocol_version === CONTROLLED_PROTOCOL;
export const PROTOCOL = CONTROLLED_PROTOCOL;
export const FIXED_SIZES = [6, 8, 10, 12, 14];
export function requireControlled(config) { if (!isControlled(config)) fail('This invitation has been retired. Ask the administrator for a new controlled-pilot link.', 410); }
export function json(body, status = 200) {
  return Response.json(body, { status, headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' } });
}
export function fail(message, status = 400) { throw Object.assign(new Error(message), { status }); }
export function admin(request, env) {
  if (!env.STUDY_ADMIN_KEY || request.headers.get('Authorization') !== `Bearer ${env.STUDY_ADMIN_KEY}`) fail('Unauthorized.', 401);
}
export async function body(request) {
  if (request.headers.get('Origin') !== new URL(request.url).origin) fail('Same-origin request required.', 403);
  if (!(request.headers.get('Content-Type') || '').startsWith('application/json')) fail('JSON required.', 415);
  // Bound the actual stream, including chunked requests without Content-Length.
  const reader = request.body?.getReader();
  if (!reader) fail('Missing body.');
  let size = 0; const chunks = [];
  for (;;) { const { done, value } = await reader.read(); if (done) break; size += value.length; if (size > 32000) { await reader.cancel(); fail('Payload too large.', 413); } chunks.push(value); }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  try { const value = JSON.parse(new TextDecoder().decode(bytes)); if (!value || typeof value !== 'object' || Array.isArray(value)) fail('Invalid body.'); return value; }
  catch (error) { fail(error.status ? error.message : 'Invalid JSON.'); }
}
export async function handle(fn) { try { return await fn(); } catch (error) { if (error.status) return json({ error: error.message }, error.status); if (String(error.message).includes('UNIQUE constraint failed: recognition_attempts')) return json({ error: 'Attempt state changed. Retry the same request.' }, 409); console.error('Pilot API failure', error.message); return json({ error: 'Save unavailable. Retry the same request.' }, 503); } }
export function token() { return [...crypto.getRandomValues(new Uint8Array(32))].map(x => x.toString(16).padStart(2, '0')).join(''); }
export async function hash(value) { return [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value)))].map(x => x.toString(16).padStart(2, '0')).join(''); }
export function shuffle(ids) {
  const result = [...ids];
  for (let i = result.length - 1; i > 0; i--) {
    const range = i + 1, limit = Math.floor(0x100000000 / range) * range; let value;
    do { value = crypto.getRandomValues(new Uint32Array(1))[0]; } while (value >= limit);
    const j = value % range; [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
export function schedule(ids, config) {
  requireControlled(config);
  const trial = (target_id, assigned_size, phase) => ({target_id, assigned_size, phase, grid: shuffle([target_id, ...config.alternatives[target_id].similar, ...config.alternatives[target_id].dissimilar])});
  return [...shuffle(ids).slice(0,3).map(id => trial(id, 14, 'practice')), ...shuffle(ids.flatMap(id => config.size_levels.map(size => trial(id, size, 'recorded'))))]
    .map((t, trial_index) => ({...t, trial_index}));
}
export function validLevels(levels) { return JSON.stringify(levels) === JSON.stringify(FIXED_SIZES); }
export async function session(request, env, id) {
  if (typeof id !== 'string' || id.length > 100) fail('Unauthorized.', 401);
  const credential = (request.headers.get('Authorization') || '').replace(/^Bearer /, '');
  if (!/^[a-f0-9]{64}$/.test(credential)) fail('Unauthorized.', 401);
  const row = await env.STUDY_SELECTION_DB.prepare('SELECT s.*,p.config_json,p.closed_at FROM recognition_sessions s JOIN recognition_pilots p USING(pilot_id) WHERE session_id=? AND credential_hash=?').bind(id || '', await hash(credential)).first();
  if (!row) fail('Unauthorized.', 401);
  requireControlled(JSON.parse(row.config_json));
  return row;
}
export async function sessionView(db, row) {
  const attempts = (await db.prepare('SELECT * FROM recognition_attempts WHERE session_id=? ORDER BY trial_index,started_at,attempt_id').bind(row.session_id).all()).results;
  const next = attempts.filter(a => a.state === 'answered').length;
  return { session_id: row.session_id, status: row.status, config: participantConfig(JSON.parse(row.config_json)), schedule: JSON.parse(row.schedule_json), next_trial: next,
    attempts: attempts.map(a => ({ ...a, correct: a.phase === 'practice' ? a.correct : undefined, grid: JSON.parse(a.grid_json), response: a.response_json ? JSON.parse(a.response_json) : null, interruption: a.interruption_json ? JSON.parse(a.interruption_json) : null })) };
}
export function participantConfig(config) {
  const { icons, size_levels, exposure_ms, target_px, protocol_version } = config;
  // Labels and source/reviewer metadata stay in admin responses only.
  return { practice_count: 3, recorded_count: 100, familiarity: config.familiarity, icons: icons.map(({ icon_id, image }) => ({ icon_id, image })), size_levels, exposure_ms, target_px, protocol_version };
}
export function relativeTime(value) { return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 86400000; }
export function validateResponse(payload, assigned, config) {
  requireControlled(config);
  const {category, selected_id, confidence, final_size, duration_ms, enlargements, choice_onset_ms, input_method} = payload;
  if (!['selected', 'unidentified'].includes(category)) fail('Invalid answer category.');
  if (category === 'selected' ? !assigned.grid.includes(selected_id) || !Number.isInteger(confidence) || confidence < 1 || confidence > 5 : selected_id != null || confidence != null) fail('Invalid selection or confidence.');
  if (!relativeTime(duration_ms) || !relativeTime(choice_onset_ms) || choice_onset_ms < config.exposure_ms || duration_ms < choice_onset_ms) fail('Invalid response timing.');
  if (!['mouse','keyboard'].includes(input_method)) fail('Invalid input method.');
  if (!Array.isArray(enlargements) || enlargements.length || final_size !== assigned.assigned_size) fail('Use the assigned size without enlargement.');
  return {category, selected_id: category === 'selected' ? selected_id : null, confidence: category === 'selected' ? confidence : null,
    final_size, assigned_size: assigned.assigned_size, selected_position: category === 'selected' ? assigned.grid.indexOf(selected_id) + 1 : null,
    duration_ms, choice_onset_ms, response_time_ms: duration_ms - choice_onset_ms, input_method, enlargements: []};
}
export function interruption(reason, at_ms, events, config, assigned = {}) {
  requireControlled(config);
  if (!['hidden','blur','space','refresh','end'].includes(reason) || !relativeTime(at_ms)) fail('Invalid interruption.');
  if (!Array.isArray(events) || events.length) fail('Enlargement is disabled.');
  return {reason, at_ms, final_size: assigned.assigned_size ?? null, enlargements: []};
}
