/* Loaded only by the reviewer page; every API request requires the admin key. */
async function pilotAdminApi(path, data, key = byId('pilotAccessKey').value) {
  const response = await fetch('/api/' + path, { method:data ? 'POST':'GET', cache:'no-store', headers:{Authorization:`Bearer ${key}`, ...(data ? {'Content-Type':'application/json'} : {})}, ...(data ? {body:JSON.stringify(data)} : {}) });
  if (!response.ok) { const error = await response.json(); throw new Error(error.error); } return response;
}
function pilotError(error) { byId('pilotStatus').className = 'results-status error'; byId('pilotStatus').textContent = error.message; }
function renderPilotCreateButtons(data) {
  byId('resultsList').querySelectorAll('.result-card').forEach((card, index) => {
    const submission = data.submissions[index]; if (!submission) return;
    card.querySelectorAll('.result-set').forEach((section, setIndex) => {
      const set = catalog.sets[setIndex], rows = submission.selections[set.set_id] || [];
      if (rows.length !== 20 || new Set(rows.map(r => r.icon_id)).size !== 20 || rows.some(r => !set.icons.some(i => i.icon_id === r.icon_id))) return;
      const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Create pilot'; section.querySelector('h4').append(' ', button);
      button.onclick = () => createPilotDialog(submission, set, rows);
    });
  });
}
function pilotDialog(title) {
  byId('pilotDialog')?.remove(); const dialog = document.createElement('dialog'); dialog.id = 'pilotDialog'; dialog.className = 'pilot-dialog';
  dialog.innerHTML = `<div class="pilot-dialog-head"><h2>${escapeHtml(title)}</h2><button id="closePilotDialog" type="button">Close</button></div><div id="pilotDialogBody"></div><p id="pilotDialogStatus" role="status"></p>`;
  document.body.append(dialog); byId('closePilotDialog').onclick = () => dialog.close(); dialog.showModal(); return dialog;
}
function createPilotDialog(submission, set, rows) {
  const dialog = pilotDialog('Create frozen pilot');
  byId('pilotDialogBody').innerHTML = `<p>${escapeHtml(submission.reviewer_code)} · ${escapeHtml(set.set_name)} · 20 icons</p><div class="pilot-icon-preview">${rows.map(r => `<img src="${escapeHtml(set.icons.find(i => i.icon_id === r.icon_id).normalized_path)}" alt="">`).join('')}</div><form id="pilotCreateForm"><label>Pilot title<input id="pilotTitle" required maxlength="120" value="${escapeHtml(set.set_name)} — controlled pilot"></label><p>Assigned sizes: <strong>6, 8, 10, 12, 14 CSS pixels</strong>.</p><p>Three practice trials, 100 randomized recorded trials, 1.5-second exposure, 128-pixel target. Five numbered options per trial: target, two nearest and two farthest alternatives by the seven computed features. Keyboard and mouse answers; confidence after selection.</p><p>No full-set preview or screen calibration. Frozen settings cannot be edited.</p><button id="pilotCreateSubmit" type="submit">Create pilot</button></form>`;
  byId('pilotCreateForm').onsubmit = async event => {
    event.preventDefault(); const button = byId('pilotCreateSubmit'); button.disabled = true;
    try {
      const response = await pilotAdminApi('pilots', {action:'create',title:byId('pilotTitle').value,size_levels:[6,8,10,12,14],protocol_version:'icon-recognition-controlled-v2',submission_id:submission.submission_id,set_id:set.set_id,updated_at:submission.updated_at,icon_ids:rows.map(r => r.icon_id)}, byId('resultsAccessKey').value);
      const result = await response.json(); dialog.close(); byId('pilotAccessKey').value = byId('resultsAccessKey').value; setActiveView('pilots'); await refreshPilots(); byId('pilotStatus').textContent = `Pilot created. Private link: ${location.origin}/pilot.html?pilot=${result.invitation}`;
    } catch (error) { byId('pilotDialogStatus').textContent = error.message; } finally { button.disabled = false; }
  };
}
async function refreshPilots(propagate = false) {
  const button = byId('refreshPilotsButton'); button.disabled = true;
  byId('pilotStatus').className = 'results-status'; byId('pilotStatus').textContent = 'Loading pilots…';
  try {
    const data = await (await pilotAdminApi('pilots')).json();
    const panel = byId('pilotAdminPanel');
    panel.innerHTML = `<h3>Recognition pilots</h3><p>Unlisted links permit participation only. New pilots use five choices and assigned sizes. Retired invitations cannot accept participation; their saved records remain exportable. Close a pilot before deleting it.</p>${data.pilots.map((p,i) => `<article class="pilot-admin-row"><strong>${escapeHtml(p.title)}</strong><span>${p.protocol_version !== 'icon-recognition-controlled-v2' ? 'Retired' : p.closed_at ? 'Closed':'Open'}</span><button ${p.protocol_version !== 'icon-recognition-controlled-v2' ? 'disabled' : ''} data-copy="${i}">Copy participant link</button><button data-inspect="${i}">View configuration</button><button data-summary="${i}">View results</button><button data-export="${i}" data-format="csv">Trial CSV</button><button data-export="${i}" data-format="full">Full JSON</button>${p.closed_at ? `<button type="button" class="danger" data-delete="${i}">Delete pilot and results</button>` : `<button data-close="${i}">Close pilot</button>`}</article>`).join('') || '<p>No pilots yet. Create one from a reviewer dataset with 20 valid icons.</p>'}`;
    panel.querySelectorAll('[data-copy]').forEach(b => b.onclick = async () => { const link = `${location.origin}/pilot.html?pilot=${data.pilots[Number(b.dataset.copy)].invitation}`; try { await navigator.clipboard.writeText(link); b.textContent = 'Copied'; } catch { pilotDialog('Participant link'); byId('pilotDialogBody').textContent = link; } });
    panel.querySelectorAll('[data-close]').forEach(b => b.onclick = async () => { b.disabled = true; try { await pilotAdminApi('pilots', {action:'close',pilot_id:data.pilots[Number(b.dataset.close)].pilot_id}); await refreshPilots(); } catch(error) { pilotError(error); b.disabled = false; } });
    panel.querySelectorAll('[data-delete]').forEach(b => b.onclick = async () => {
      const p = data.pilots[Number(b.dataset.delete)];
      if (!confirm(`Permanently delete pilot “${p.title}”, its invitation, all sessions, and all responses? This cannot be undone. Any in-progress session will stop. Reviewer icon submissions will remain.`)) return;
      b.disabled = true;
      try { await pilotAdminApi('pilots', { action:'delete', pilot_id:p.pilot_id }); await refreshPilots(); byId('pilotStatus').textContent = `Deleted pilot “${p.title}” and its results.`; }
      catch(error) { pilotError(error); b.disabled = false; }
    });
    panel.querySelectorAll('[data-inspect]').forEach(b => b.onclick = async () => { try { const p = await (await pilotAdminApi(`pilots?pilot_id=${data.pilots[Number(b.dataset.inspect)].pilot_id}`)).json(); pilotDialog(p.title); const pre = document.createElement('pre'); pre.textContent = JSON.stringify(p.config,null,2); byId('pilotDialogBody').append(pre); } catch(error) { pilotError(error); } });
    panel.querySelectorAll('[data-summary]').forEach(b => b.onclick = async () => { try {
      const p = data.pilots[Number(b.dataset.summary)], result = await (await pilotAdminApi(`pilot-results?pilot_id=${p.pilot_id}`)).json(), s = result.summary;
      pilotDialog(p.title + ' — results'); byId('pilotDialogBody').innerHTML = `<p>${s.sessions} sessions · ${s.session_status.completed || 0} completed · ${s.session_status.ended || 0} ended early · ${s.session_status.active || 0} active</p><p>${s.practice_answers} practice answers · ${s.recorded_answers} recorded answers · ${s.interrupted_attempts} interrupted attempts</p><p>Default summaries exclude ${s.excluded_repeated_exposure} recorded responses with repeated exposure. Eligible recorded responses: ${s.eligible_recorded_answers}.</p><p>Accuracy: ${s.accuracy === null ? 'No eligible responses' : (s.accuracy*100).toFixed(1)+'%'} · Unidentified: ${s.unidentified}</p>${s.by_size ? '<h3>Accuracy by assigned size</h3><ul>' + Object.entries(s.by_size).map(([size,v]) => `<li>${escapeHtml(size)} px: ${v.correct}/${v.n} correct (${v.accuracy === null ? '—' : (v.accuracy*100).toFixed(1)}%); median response ${v.median_response_time_ms === null ? '—' : v.median_response_time_ms.toFixed(0)} ms</li>`).join('') + '</ul>' : ''}${[[s.size_label,s.chosen_sizes],['Confidence',s.confidence],['Target → choice confusion counts',s.confusion]].map(([label,values]) => `<h3>${label}</h3><ul>${Object.entries(values).map(([key,count]) => `<li>${escapeHtml(key)}: ${count}</li>`).join('') || '<li>No responses</li>'}</ul>`).join('')}`;
    } catch(error) { pilotError(error); } });
    panel.querySelectorAll('[data-export]').forEach(b => b.onclick = async () => { try { const response = await pilotAdminApi(`pilot-results?pilot_id=${data.pilots[Number(b.dataset.export)].pilot_id}&format=${b.dataset.format}`); const url = URL.createObjectURL(await response.blob()), a = document.createElement('a'); a.href = url; a.download = b.dataset.format === 'csv' ? 'pilot-trials.csv':'pilot-full.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); } catch(error) { pilotError(error); } });
    byId('pilotStatus').textContent = `Loaded ${data.pilots.length} pilots.`;
  } catch(error) { pilotError(error); if (propagate) throw error; } finally { button.disabled = false; }
}
