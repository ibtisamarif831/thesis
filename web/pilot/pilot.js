/* Monotonic times are relative to the current exposure, never wall-clock dates. */
const $ = id => document.getElementById(id);
const invitation = new URLSearchParams(location.search).get('pilot');
const storageKey = `recognition-pilot:${invitation}`;
let local = {}, view, config, images = new Map(), mode = 'loading', timer, started = 0, enlargements = [], chosen, answerAt, busy = false, paused = false;
let choiceOnset = 0, inputMethod = 'mouse', confidenceAt = 0;
const heldKeys = new Set();
const isMac = /mac/i.test(navigator.userAgentData?.platform || navigator.platform || '');
const enterKey = isMac ? 'Return ↵' : 'Enter ↵';
const finishKeys = isMac ? '⌘ ↵' : 'Ctrl ↵';
const badge = key => `<kbd aria-hidden="true">${key}</kbd>`;
function keyboardHints() {
  const hints = {begin:['Enter',enterKey], ready:['Enter',enterKey], next:['Enter',enterKey], retry:['Enter',enterKey],
    unknown:['0','0'], finish:[isMac ? 'Meta+Enter' : 'Control+Enter',finishKeys], end:[isMac ? 'Meta+Shift+X' : 'Control+Shift+X',isMac ? '⌘ ⇧ X' : 'Ctrl Shift X'], endPaused:[isMac ? 'Meta+Shift+X' : 'Control+Shift+X',isMac ? '⌘ ⇧ X' : 'Ctrl Shift X']};
  for (const [id,[shortcut,label]] of Object.entries(hints)) {
    const button = $(id); if (!button || button.querySelector('kbd')) continue;
    button.setAttribute('aria-keyshortcuts',shortcut); button.insertAdjacentHTML('beforeend',' '+badge(label));
  }
  document.querySelectorAll('[data-confidence]').forEach(button => { if (!button.querySelector('kbd')) { button.setAttribute('aria-keyshortcuts',button.dataset.confidence); button.setAttribute('aria-label',button.dataset.confidence); button.innerHTML = badge(button.dataset.confidence); } });
}
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
function persist() { sessionStorage.setItem(storageKey, JSON.stringify(local)); }
function elapsed() { return started ? Math.min(86400000, Math.max(0, performance.now() - started)) : 0; }
function status(text, error = false) { $('status').textContent = text; $('status').className = error ? 'error' : ''; }
async function api(path, data) {
  const response = await fetch('/api/' + path, { method: data ? 'POST' : 'GET', cache:'no-store', headers: { ...(data ? { 'Content-Type':'application/json' } : {}), ...(local.credential ? { Authorization:`Bearer ${local.credential}` } : {}) }, ...(data ? { body:JSON.stringify(data) } : {}) });
  const result = await response.json(); if (!response.ok) throw new Error(result.error || 'Request failed.'); return result;
}
async function preload() {
  await Promise.all(config.icons.map(async icon => { const image = new Image(); image.src = icon.image; await image.decode(); if (!image.naturalWidth) throw new Error('Missing image'); images.set(icon.icon_id, image); }));
}
async function loadView() { view = await api(`pilot-sessions?session_id=${encodeURIComponent(local.session_id)}`); config = view.config; document.body.classList.add("controlled"); }
function next() { return view.schedule[view.next_trial]; }
function errorScreen(error, retry) {
  mode = 'retry';
  status(error.message, true); $('content').innerHTML = '<p>Your acknowledged responses remain saved. Keep this tab open to retry.</p><button id="retry">Retry</button>';
  $('retry').onclick = retry; keyboardHints();
}
async function boot() {
  try {
    local = JSON.parse(sessionStorage.getItem(storageKey) || '{}');
    if (local.session_id) {
      await loadView(); await preload();
      if (local.pending) { await sendPending(); return; }
      const active = view.attempts.find(a => a.state === 'active');
      if (active && view.status === 'active') {
        local.pending = { endpoint:'pilot-trials', data:{ action:'interrupt', session_id:local.session_id, attempt_id:active.attempt_id, reason:'refresh', at_ms:local.elapsed || 0, enlargements:local.enlargements || [] } }; persist();
        await sendPending(); return;
      }
      resume(); return;
    }
    const info = await api(`pilot-sessions?pilot=${encodeURIComponent(invitation || '')}`); config = info.config;
    if (!info.open) { status('This invitation is closed to new sessions.'); return; }
    status('Preparing all 20 stimulus images…'); await preload();
    mode = 'intro'; document.body.classList.add('controlled'); status('All images are ready.');
    $('content').innerHTML = `<h2>${esc(info.title)}</h2><p>You will see one icon for 1.5 seconds, then find it in a row of five icons. Click an option or press its number (1–5). After choosing, rate your confidence from 1 to 5. You can also choose “I cannot identify it”.</p><p>There are three practice trials and 100 recorded trials. Please use a desktop window large enough to show the complete row. Practice gives feedback; recorded trials do not.</p><p>Participation is voluntary. You can end at any time. We save an anonymous session, choices, confidence, assigned sizes, timings, input method, interruptions, and initial viewport/device-pixel ratio. We ask for no name or email. Optional comments follow the trials.</p><p class="muted">Each of the 20 targets appears at five assigned sizes (6–14 pixels). There are no enlargement controls. Press ${isMac ? 'Return' : 'Enter'} ↵ to begin, start each trial, or continue after practice. Use 0 if you cannot identify the icon. Press ${isMac ? 'Command' : 'Ctrl'} + Shift + X to end the session. Press Ready when you want to continue; you can take a break between trials. This is a visual-matching pilot.</p><button class="primary" id="begin">Begin anonymous session</button>`;
    keyboardHints();
    $('begin').onclick = async () => { if (busy) return; busy = true; $('begin').disabled = true; try {
      const result = await api('pilot-sessions', { pilot:invitation, viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio} });
      local = { ...result }; persist(); await loadView(); resume();
    } catch (error) { errorScreen(error, boot); } finally { busy = false; } };
  } catch (error) { errorScreen(new Error('Could not prepare the pilot: ' + error.message), boot); }
}
function resume() {
  local.active = null; local.elapsed = 0; persist();
  if (view.status !== 'active') { done(view.status); return; }
  if (!next()) { debrief(); return; }
  mode = 'ready'; draw(); checkSpace();
}
function draw() {
  const trial = next(); if (!trial) return;
  const progress = trial.phase === 'practice' ? `Practice ${trial.trial_index + 1} of ${config.practice_count}` : `Recorded trial ${trial.trial_index - config.practice_count + 1} of ${config.recorded_count}`;
  status(progress);
  let stage = '<p>When you are ready, press Ready.</p>';
  if (mode === 'target') stage = `<img class="target" src="${esc(images.get(trial.target_id).src)}" alt="Target icon">`;
  if (['grid','confidence'].includes(mode)) stage = `<div class="grid">${trial.grid.map((id, i) => `<button type="button" data-id="${id}" aria-label="Candidate ${i+1}" aria-keyshortcuts="${i+1}" ${mode === 'confidence' ? 'disabled' : ''} class="${id === chosen ? 'chosen' : ''}"><img src="${esc(images.get(id).src)}" alt="" style="width:${trial.assigned_size}px;height:${trial.assigned_size}px"><span class="option-number">${badge(i+1)}</span></button>`).join('')}</div>`;
  let controls = '';
  if (mode === 'ready') controls = '<button class="primary" id="ready">Ready</button>';
  if (mode === 'target') controls = '<p>Remember this icon.</p>';
  if (mode === 'grid') controls = `<div class="buttons"><p>Choose 1–5, using the keyboard or mouse.</p><button id="unknown">I cannot identify it</button></div><p class="muted">Assigned icon size: ${trial.assigned_size} pixels</p>`;
  if (mode === 'confidence') controls = '<p>How confident are you? 1 = least, 5 = most</p><div class="confidence">' + [1,2,3,4,5].map(n => `<button data-confidence="${n}">${n}</button>`).join('') + '</div>';
  if (mode === 'feedback') { stage = `<p>${local.feedback ? 'Correct.' : 'That was not the target.'}</p>`; controls = '<button class="primary" id="next">Next trial</button>'; }
  $('content').innerHTML = `<div id="trial"><div class="stage">${stage}</div><div class="controls">${controls}</div><div class="buttons"><span class="muted">You may stop at any time.</span><button id="end">End session</button></div></div>`;
  if ($('ready')) $('ready').onclick = ready;
  if ($('next')) $('next').onclick = resume;
  if ($('unknown')) $('unknown').onclick = event => choose(null, event.detail === 0 ? 'keyboard' : 'mouse');
  document.querySelectorAll('[data-id]').forEach(button => button.onclick = event => choose(button.dataset.id, event.detail === 0 ? 'keyboard' : 'mouse'));
  document.querySelectorAll('[data-confidence]').forEach(button => button.onclick = () => { if (mode !== 'confidence' || paused || performance.now() - confidenceAt < 150) return; submit(Number(button.dataset.confidence)); });
  $('end').onclick = end; keyboardHints();
}
async function ready() {
  if (busy || paused || mode !== 'ready' || !fits()) return;
  busy = true; mode = 'starting'; $('ready').disabled = true;
  local.active = crypto.randomUUID();
  local.pending = {endpoint:'pilot-trials',data:{action:'start',session_id:local.session_id,attempt_id:local.active,trial_index:view.next_trial}}; persist();
  await sendPending(); busy = false;
}
function expose() {
  mode = 'target'; choiceOnset = 0; enlargements = []; chosen = null; started = 0; local.elapsed = 0; local.enlargements = []; persist(); draw();
  if (!fits() || document.hidden || !document.hasFocus()) { interrupt(document.hidden ? 'hidden' : !document.hasFocus() ? 'blur' : 'space'); checkSpace(); return; }
  requestAnimationFrame(() => { if (mode !== 'target') return; started = performance.now(); const reveal = () => { if (mode !== 'target') return; const remaining = config.exposure_ms - elapsed(); if (remaining > 0) { timer = setTimeout(reveal, Math.ceil(remaining)); return; } mode = 'grid'; draw(); choiceOnset = elapsed(); checkSpace(); }; timer = setTimeout(reveal, config.exposure_ms); });
}
async function submit(confidence) {
  clearTimeout(timer); mode = 'saving';
  local.pending = { endpoint:'pilot-trials', data:{action:'answer',session_id:local.session_id,attempt_id:local.active,response:{category:chosen ? 'selected':'unidentified',selected_id:chosen,confidence,final_size:next().assigned_size,duration_ms:answerAt,choice_onset_ms:choiceOnset,input_method:inputMethod,enlargements}} }; persist();
  await sendPending();
}
async function sendPending() {
  const pending = local.pending; if (!pending) return;
  $('content').innerHTML = '<p>Saving…</p>'; status('Please wait for the save confirmation.');
  try {
    const result = await api(pending.endpoint, pending.data);
    delete local.pending; persist();
    if (pending.data.action === 'start') { local.active = pending.data.attempt_id; persist(); expose(); }
    else if (pending.data.action === 'answer') {
      const practice = (view.attempts.find(a => a.attempt_id === pending.data.attempt_id)?.phase || next()?.phase) === 'practice'; local.feedback = result.correct; local.active = null; persist(); await loadView();
      if (practice) { mode = 'feedback'; drawFeedback(); } else resume();
    } else if (['complete','end'].includes(pending.data.action)) done(result.status);
    else { await loadView(); resume(); status('Attempt interrupted. Press Ready to restart the same target and grid.'); }
  } catch (error) { mode = 'retry'; errorScreen(error, sendPending); }
}
function drawFeedback() {
  status('Practice response saved.'); $('content').innerHTML = `<div class="stage"><p>${local.feedback ? 'Correct.' : 'That was not the target.'}</p></div><button id="next" class="primary">Continue</button><button id="end">End session</button>`;
  $('next').onclick = resume; $('end').onclick = end; keyboardHints();
}
function interrupt(reason) {
  if (!['target','grid','confidence'].includes(mode)) return;
  clearTimeout(timer); local.elapsed = elapsed();
  local.pending = {endpoint:'pilot-trials',data:{action:'interrupt',session_id:local.session_id,attempt_id:local.active,reason,at_ms:local.elapsed,enlargements}}; persist(); mode = 'interrupted';
  sendPending();
}
function fits() { return innerWidth >= 680 && innerHeight >= 560 && (!$('trial') || $('trial').getBoundingClientRect().bottom <= innerHeight); }
function checkSpace() {
  if (!['ready','target','grid','confidence','interrupted','retry'].includes(mode)) return;
  paused = !fits() || document.hidden || !document.hasFocus();
  if (paused) {
    const reason = document.hidden ? 'hidden' : !document.hasFocus() ? 'blur':'space'; interrupt(reason);
    if (!$('pause')) { const overlay = document.createElement('div'); overlay.id = 'pause'; overlay.className = 'overlay'; overlay.innerHTML = '<h2>Pilot paused</h2><p>Return to this tab and use a desktop window of at least 680 × 560 pixels so the complete row and controls fit without scrolling.</p><button id="endPaused">End session</button>'; document.body.append(overlay); $('endPaused').onclick = end; }
    $('endPaused').disabled = Boolean(local.pending); keyboardHints();
  } else $('pause')?.remove();
}
function debrief() {
  mode = 'debrief'; $('pause')?.remove(); status('All trial responses are saved.');
  $('content').innerHTML = '<h2>Optional reflections</h2><label>How did you find the task and the pace?<textarea id="difficulty" maxlength="1000"></textarea></label><label>Did you forget any targets?<textarea id="forgot" maxlength="1000"></textarea></label><label>Which visual details helped you?<textarea id="details" maxlength="1000"></textarea></label><button class="primary" id="finish">Save and finish</button><button id="end">End session</button>';
  $('finish').onclick = () => complete('complete'); $('end').onclick = end; keyboardHints();
}
async function end() { if (local.pending || mode === 'starting' || mode === 'saving') return; clearTimeout(timer); await complete('end'); }
async function complete(action) {
  mode = 'saving'; $('pause')?.remove(); local.pending = {endpoint:'pilot-completion',data:{action,session_id:local.session_id,at_ms:elapsed(),enlargements,debrief:Object.fromEntries(['difficulty','forgot','details'].map(id => [id,$(id)?.value || '']))}}; persist(); await sendPending();
}
function done(state) { mode = 'done'; $('pause')?.remove(); status(state === 'completed' ? 'Session completed and saved.' : 'Session ended. Completed responses are saved.'); $('content').innerHTML = '<p>Thank you. You may close this tab.</p>'; }
function choose(id, method) {
  if (mode !== 'grid' || paused || !choiceOnset) return;
  chosen = id; inputMethod = method; answerAt = elapsed();
  if (!id) { submit(null); return; }
  mode = 'confidence'; confidenceAt = performance.now(); draw();
}
document.addEventListener('keydown', event => {
  const editing = /^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName) || event.target.isContentEditable;
  const modifier = isMac ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey;
  const finishShortcut = modifier && event.key === 'Enter' && !event.shiftKey && !event.altKey;
  const endShortcut = modifier && event.shiftKey && event.key.toLowerCase() === 'x' && !event.altKey;
  const plain = !event.ctrlKey && !event.metaKey && !event.altKey && !event.shiftKey;
  const advance = plain && event.key === 'Enter' && !editing;
  const numeric = plain && /^[0-5]$/.test(event.key) && !editing;
  if (!finishShortcut && !endShortcut && !advance && !numeric) return;
  event.preventDefault();
  const key = event.code || event.key;
  if (event.repeat || heldKeys.has(key)) return;
  heldKeys.add(key);
  if (endShortcut) {
    const button = $('pause') ? $('endPaused') : $('end');
    if (button && !button.disabled && !['saving','starting','done'].includes(mode)) button.click();
    return;
  }
  if (finishShortcut) { if (mode === 'debrief' && !local.pending) $('finish')?.click(); return; }
  if (advance) {
    // Respect Tab navigation: Enter activates the focused button, otherwise the current primary action.
    const focused = event.target.closest('button');
    const button = $('pause') ? (focused?.id === 'endPaused' ? focused : null) : focused || ({intro:$('begin'),ready:$('ready'),feedback:$('next'),retry:$('retry'),debrief:$('finish')})[mode];
    if (button && !button.disabled) button.click();
    return;
  }
  if (paused) return;
  if (mode === 'grid') choose(event.key === '0' ? null : next().grid[Number(event.key)-1], 'keyboard');
  else if (mode === 'confidence' && event.key !== '0' && performance.now()-confidenceAt >= 150) submit(Number(event.key));
});
document.addEventListener('keyup', event => heldKeys.delete(event.code || event.key));
window.addEventListener('blur', () => heldKeys.clear());
document.addEventListener('visibilitychange', checkSpace);
window.addEventListener('blur', checkSpace); window.addEventListener('focus', checkSpace); window.addEventListener('resize', checkSpace);
window.addEventListener('pagehide', () => { if (['target','grid','confidence'].includes(mode)) { local.elapsed = elapsed(); persist(); } });
setInterval(() => { if (['target','grid','confidence'].includes(mode)) { local.elapsed = elapsed(); persist(); } }, 1000);
boot();
