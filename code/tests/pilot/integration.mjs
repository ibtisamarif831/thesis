// Executes real Pages Functions against Wrangler's isolated local D1.
import assert from 'node:assert/strict';
import { spawn, execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, symlinkSync, existsSync, cpSync, lstatSync, unlinkSync } from 'node:fs';
const port = process.env.PILOT_TEST_PORT || '8799';
const root = process.cwd(), base = process.env.PILOT_TEST_URL || `http://127.0.0.1:${port}`;
const args = ['--config','wrangler.pilot-test.jsonc'];
const persist = root + '/tmp/controlled-pilot-integration-d1-' + crypto.randomUUID(); mkdirSync(root+'/tmp',{recursive:true});
const wrangler = (...commands) => execFileSync(root+'/node_modules/.bin/wrangler',[...commands,...args],{cwd:root,encoding:'utf8',stdio:['ignore','pipe','pipe']});
const sql = text => wrangler('d1','execute','STUDY_SELECTION_DB','--local','--persist-to',persist,'--command',text);
const catalog = JSON.parse(readFileSync('dist/dashboard/study_selection_data.json'));
const set = catalog.sets[0], ids = set.icons.slice(0,20).map(i => i.icon_id), submission = 'pilot-fixture';
wrangler('d1','execute','STUDY_SELECTION_DB','--local','--persist-to',persist,'--file','migrations/0001_study_icon_selection.sql');
sql(set.icons.map(icon => `INSERT OR IGNORE INTO study_icons VALUES('${icon.icon_id}','${set.set_id}','fixture');`).join(''));
sql(`INSERT OR IGNORE INTO study_submissions(submission_id,reviewer_code,selection_version,created_at,updated_at) VALUES('${submission}','pilot_fixture','five-sets-up-to-20-v2','fixture','fixture'); DELETE FROM study_selections WHERE submission_id='${submission}';`);
sql(ids.map((id,i) => `INSERT INTO study_selections VALUES('${submission}','${set.set_id}','${id}',${i+1});`).join(''));
const before = sql(`SELECT * FROM study_selections WHERE submission_id='${submission}' ORDER BY selection_order;`);
wrangler('d1','execute','STUDY_SELECTION_DB','--local','--persist-to',persist,'--file','migrations/0002_icon_recognition_pilot.sql');
const after = sql(`SELECT * FROM study_selections WHERE submission_id='${submission}' ORDER BY selection_order;`);
assert.deepEqual(JSON.parse(before.slice(before.indexOf('[')))[0].results, JSON.parse(after.slice(after.indexOf('[')))[0].results);
sql(`INSERT OR REPLACE INTO recognition_pilots VALUES('legacy-preserved','${'1'.repeat(64)}','legacy fixture','{"protocol_version":"icon-recognition-usability-v1","icons":[],"source":{"set_id":"fixture"}}','fixture',NULL);
INSERT OR REPLACE INTO recognition_sessions(session_id,pilot_id,credential_hash,schedule_json,viewport_json,started_at,last_activity_at) VALUES('legacy-session','legacy-preserved','fixture','[]','{}','fixture','fixture');
INSERT OR REPLACE INTO recognition_attempts(attempt_id,session_id,trial_index,phase,target_id,grid_json,state,response_json,correct,started_at) VALUES('legacy-attempt','legacy-session',0,'recorded','fixture','[]','answered','{"category":"selected","selected_id":"fixture","final_size":4,"enlargements":[],"confidence":3}',1,'fixture');`);
wrangler('d1','execute','STUDY_SELECTION_DB','--local','--persist-to',persist,'--file','migrations/0003_controlled_pilot_trials.sql');
const legacyRows=sql("SELECT COUNT(*) AS n FROM recognition_attempts WHERE attempt_id='legacy-attempt';");assert.equal(JSON.parse(legacyRows.slice(legacyRows.indexOf('[')))[0].results[0].n,1);
const appDir = root + '/tmp/controlled-pilot-local-app'; mkdirSync(appDir,{recursive:true});
const cfg = JSON.parse(readFileSync(root + '/wrangler.pilot-test.jsonc')); cfg.pages_build_output_dir = './public'; cpSync(root + '/dist/dashboard',appDir + '/public',{recursive:true});
writeFileSync(appDir + '/wrangler.jsonc',JSON.stringify(cfg));
if (existsSync(appDir + '/functions') && lstatSync(appDir + '/functions').isSymbolicLink()) unlinkSync(appDir + '/functions');
cpSync(root + '/functions',appDir + '/functions',{recursive:true});
const server = process.env.PILOT_TEST_URL ? null : spawn(root+'/node_modules/.bin/wrangler',['pages','dev','--cwd',appDir,'--d1','STUDY_SELECTION_DB=STUDY_SELECTION_DB','--port',port,'--persist-to',persist,'--binding','STUDY_ADMIN_KEY=local-admin','--binding','STUDY_SUBMIT_KEY=local-submit'],{cwd:appDir,stdio:['ignore','pipe','pipe']});
let serverOutput = ''; server?.stdout.on('data',b => {serverOutput+=b;}); server?.stderr.on('data',b=>{serverOutput+=b;});
const sleep = ms => new Promise(r => setTimeout(r,ms));
async function call(path, data, credential, status=200, origin=base) {
  const response = await fetch(base+'/api/'+path,{method:data?'POST':'GET',headers:{...(data?{'Content-Type':'application/json',Origin:origin}:{}),...(credential?{Authorization:`Bearer ${credential}`}:{})},...(data?{body:JSON.stringify(data)}:{})});
  assert.equal(response.status,status,`${path}: ${await response.clone().text()}`); assert.equal(response.headers.get('cache-control'),'no-store');
  return response.headers.get('content-type').includes('json') ? response.json() : response.text();
}
try {
  for(let i=0;i<100;i++) {try {await fetch(base+'/pilot.html');break;} catch {if(i===99) throw new Error(serverOutput);await sleep(200);}}
  const source={action:'create',title:'LOCAL TEST — icon recognition',submission_id:submission,set_id:set.set_id,updated_at:'fixture',icon_ids:ids,size_levels:[6,8,10,12,14],protocol_version:'icon-recognition-controlled-v2'};
  await call('pilots',source,null,401); await call('pilots',source,'local-admin',403,'https://elsewhere.test');
  await call('pilots',{...source,icon_ids:ids.slice(1)},'local-admin',400);
  await call('pilots',{...source,icon_ids:Array(20).fill(ids[0])},'local-admin',400);
  await call('pilots',{...source,size_levels:[24,16]},'local-admin',400);
  await call('pilots',{...source,updated_at:'stale'},'local-admin',409);
  await call('pilot-sessions?pilot='+'1'.repeat(64),null,null,410);
  await call('pilots',{...source,protocol_version:'icon-recognition-usability-v1'},'local-admin',400);
  const pilot=await call('pilots',source,'local-admin',201);
  assert.equal(pilot.config.selection_rule_version,'near-distinct-band-12-16-sha256-v1');
  for(const v of Object.values(pilot.config.alternatives)) assert.ok(v.selected_ranks.dissimilar.every(r=>r>=12&&r<=16));
  const legacyResult=await call('pilot-results?pilot_id=legacy-preserved',null,'local-admin'); assert.equal(legacyResult.summary.collision_check_status,'not checked');
  if(process.env.PILOT_BROWSER_CHECKS) await new Promise((resolve,reject) => {
    const browser = spawn(process.execPath,['code/tests/pilot/refinement-browser.mjs',base],{cwd:root,stdio:'inherit'});
    browser.on('error',reject); browser.on('exit',code => code === 0 ? resolve() : reject(new Error('Browser checks failed: '+code)));
  });
  const invite=await call('pilot-sessions?pilot='+pilot.invitation); assert.equal(invite.config.icons.length,20); assert.equal(invite.config.icons[0].label,undefined);
  sql(`UPDATE study_submissions SET updated_at='edited' WHERE submission_id='${submission}'; DELETE FROM study_selections WHERE submission_id='${submission}' AND selection_order=20;`);
  const frozen=await call('pilots?pilot_id='+pilot.pilot_id,null,'local-admin'); assert.equal(frozen.config.icons.length,20);
  await call('pilots',source,'local-admin',409);
  const s=await call('pilot-sessions',{pilot:pilot.invitation,viewport:{width:1280,height:900,dpr:2}},null,201);
  await call('pilot-sessions?session_id='+s.session_id,null,'wrong',401);
  let view=await call('pilot-sessions?session_id='+s.session_id,null,s.credential);
  assert.equal(new Set(view.schedule.slice(3).map(t=>t.target_id)).size,20); assert.equal(new Set(view.schedule.slice(0,3).map(t=>t.target_id)).size,3);
  assert.equal(view.schedule.length,103); assert.equal(new Set(view.schedule.slice(3).map(t=>t.target_id+':'+t.assigned_size)).size,100);
  for (const t of view.schedule) { assert.equal(t.grid.length,5); assert.equal(new Set(t.grid).size,5); assert.ok(t.grid.includes(t.target_id)); }
  for(const id of ids) assert.deepEqual(view.schedule.slice(3).filter(t=>t.target_id===id).map(t=>t.grid.indexOf(id)).sort(),[0,1,2,3,4]);
  const resumed=await call('pilot-sessions?session_id='+s.session_id,null,s.credential); assert.deepEqual(resumed.schedule,view.schedule);
  await call('pilots',{action:'close',pilot_id:pilot.pilot_id},'local-admin');
  await call('pilot-sessions',{pilot:pilot.invitation,viewport:{width:1280,height:900,dpr:2}},null,410);
  await call('pilot-completion',{action:'complete',session_id:s.session_id},s.credential,409);
  let lastAttempt;
  for (const trial of view.schedule) {
    const attempt_id=crypto.randomUUID(), req={action:'start',session_id:s.session_id,trial_index:trial.trial_index,attempt_id};
    await call('pilot-trials',req,s.credential); await call('pilot-trials',req,s.credential);
    let answerId=attempt_id;
    if (trial.trial_index === 3) {
      await call('pilot-trials',{action:'interrupt',session_id:s.session_id,attempt_id,reason:'refresh',at_ms:3500},s.credential);
      answerId=crypto.randomUUID(); await call('pilot-trials',{...req,attempt_id:answerId},s.credential);
    }
    const response={category:trial.trial_index===4?'unidentified':'selected',selected_id:trial.trial_index===4?null:trial.target_id,confidence:trial.trial_index===4?null:4,final_size:trial.assigned_size,duration_ms:2200,choice_onset_ms:1550,input_method:'keyboard',enlargements:[]};
    await call('pilot-trials',{action:'answer',session_id:s.session_id,attempt_id:answerId,response:{...response,final_size:96}},s.credential,400);
    await call('pilot-trials',{action:'answer',session_id:s.session_id,attempt_id:answerId,response:{...response,selected_id:'outside-frozen-set'}},s.credential,400);
    const answer={action:'answer',session_id:s.session_id,attempt_id:answerId,response};
    const result=await call('pilot-trials',answer,s.credential);
    if (trial.phase === 'recorded') assert.equal(result.correct,undefined); else assert.equal(result.correct,true);
    await call('pilot-trials',answer,s.credential); // lost acknowledgement/retry
    await call('pilot-trials',{...answer,response:{...response,duration_ms:6000}},s.credential,409);
    lastAttempt=answer;
  }
  view=await call('pilot-sessions?session_id='+s.session_id,null,s.credential); assert.equal(view.next_trial,103);
  assert.equal(view.attempts.find(a=>a.phase==='recorded').correct,undefined);
  await call('pilot-completion',{action:'complete',session_id:s.session_id,debrief:{details:'x'.repeat(1001)}},s.credential,400);
  await call('pilot-completion',{action:'complete',session_id:s.session_id,debrief:{details:'=HYPERLINK("unsafe")\nquoted,"text"'}},s.credential);
  await call('pilot-completion',{action:'complete',session_id:s.session_id},s.credential); await call('pilot-trials',lastAttempt,s.credential);
  await call('pilot-results?pilot_id='+pilot.pilot_id,null,s.credential,401);
  const full=await call('pilot-results?pilot_id='+pilot.pilot_id+'&format=full',null,'local-admin');
  assert.equal(full.summary.recorded_answers,100); assert.equal(full.summary.eligible_recorded_answers,99); assert.equal(full.summary.excluded_repeated_exposure,1); assert.equal(full.summary.unidentified,1); assert.equal(full.summary.session_status.completed,1);
  assert.equal(full.attempts.length,104); assert.equal(full.sessions[0].credential_hash,undefined); assert.equal(full.summary.correct,98);
  assert.equal(Object.values(full.summary.by_size).reduce((n,v)=>n+v.n,0),99);
  assert.equal(full.summary.by_size[6].median_response_time_ms,650);
  const csv=await call('pilot-results?pilot_id='+pilot.pilot_id+'&format=csv',null,'local-admin'); assert.equal(csv.split('\r\n').length,106);assert.ok(csv.includes('collision_check_status'));assert.ok(csv.includes(pilot.config.selection_rule_version));
  // Early end, independent credential boundary, and concurrent duplicate delivery.
  sql(`UPDATE study_submissions SET updated_at='fixture' WHERE submission_id='${submission}'; INSERT INTO study_selections VALUES('${submission}','${set.set_id}','${ids[19]}',20);`);
  const p2=await call('pilots',source,'local-admin',201);
  const early=await call('pilot-sessions',{pilot:p2.invitation,viewport:{width:1280,height:900,dpr:1}},null,201);
  await call('pilot-sessions?session_id='+early.session_id,null,s.credential,401);
  const ev=await call('pilot-sessions?session_id='+early.session_id,null,early.credential), eid=crypto.randomUUID();
  await call('pilot-trials',{action:'start',session_id:early.session_id,attempt_id:eid,trial_index:0},early.credential);
  const er={action:'answer',session_id:early.session_id,attempt_id:eid,response:{category:'selected',selected_id:ev.schedule[0].target_id,confidence:5,final_size:ev.schedule[0].assigned_size,duration_ms:2200,choice_onset_ms:1550,input_method:'mouse',enlargements:[]}};
  const race=await Promise.all([call('pilot-trials',er,early.credential),call('pilot-trials',er,early.credential).catch(e=>e)]);
  assert.ok(race.some(r=>r.ok)); await call('pilot-trials',er,early.credential);
  await call('pilot-trials',{action:'start',session_id:early.session_id,attempt_id:crypto.randomUUID(),trial_index:1},early.credential);
  await call('pilot-completion',{action:'end',session_id:early.session_id,at_ms:1200},early.credential);
  const earlyResult=await call('pilot-results?pilot_id='+p2.pilot_id+'&format=full',null,'local-admin');
  assert.equal(earlyResult.summary.session_status.ended,1); assert.equal(earlyResult.summary.practice_answers,1); assert.equal(earlyResult.summary.interrupted_attempts,1);
  const stillFrozen=await call('pilots?pilot_id='+pilot.pilot_id,null,'local-admin'); assert.equal(stillFrozen.config.icons.length,20);
  for (const path of ['/','/study-selection.html','/study_selection_data.json',invite.config.icons[0].image]) assert.equal((await fetch(base+path)).status,200);
  const selections=Object.fromEntries(catalog.sets.map(s=>[s.set_id,[]]));selections[set.set_id]=[ids[0]];
  const nomination={reviewer_code:'pilot_selection_regression',selection_version:'five-sets-up-to-20-v2',selections};
  const nominate=async data=>{const r=await fetch(base+'/api/study-selections',{method:'POST',headers:{Origin:base,'Content-Type':'application/json','X-Study-Key':'local-submit'},body:JSON.stringify(data)});assert.equal(r.status,200,await r.clone().text());return r.json();};
  assert.equal((await nominate(nomination)).selected_icon_count,1);
  selections[set.set_id].push(ids[1]);assert.equal((await nominate(nomination)).selected_icon_count,2);
  const rr=await fetch(base+'/api/study-results',{headers:{Authorization:'Bearer local-admin',Accept:'application/json'}});assert.equal(rr.status,200);
  const savedNomination=(await rr.json()).submissions.find(r=>r.reviewer_code===nomination.reviewer_code);assert.equal(savedNomination.selections[set.set_id].length,2);
  // Delete only the source nomination; frozen pilots and participant records survive.
  const deletion={action:'delete',submission_id:submission,updated_at:'fixture'};
  await call('study-results',deletion,null,401);
  await call('study-results',deletion,'local-submit',401);
  await call('study-results',deletion,'local-admin',403,'https://elsewhere.test');
  await call('study-results',{...deletion,submission_id:[]},'local-admin',400);
  await call('study-results',{...deletion,updated_at:'stale'},'local-admin',409);
  assert.equal((await call('pilots?pilot_id='+p2.pilot_id,null,'local-admin')).config.icons.length,20);
  await call('study-results',deletion,'local-admin');
  await call('study-results',deletion,'local-admin',409);
  const remainingOutput=sql(`SELECT COUNT(*) AS n FROM study_selections WHERE submission_id='${submission}';`);
  const remaining=JSON.parse(remainingOutput.slice(remainingOutput.indexOf('[')))[0].results;
  assert.equal(remaining[0].n,0);
  const afterDelete=await call('pilots?pilot_id='+p2.pilot_id,null,'local-admin');
  assert.equal(afterDelete.config.icons.length,20);assert.equal(afterDelete.config.source.submission_id,submission);
  const retained=await call('pilot-results?pilot_id='+p2.pilot_id+'&format=full',null,'local-admin');
  assert.deepEqual(retained.summary,earlyResult.summary);
  await call('pilots',source,'local-admin',409);
  // A pilot can be deleted only after closure, including abandoned active sessions.
  const activeForDeletion=await call('pilot-sessions',{pilot:p2.invitation,viewport:{width:1280,height:900,dpr:1}},null,201);
  const deletePilot={action:'delete',pilot_id:p2.pilot_id};
  await call('pilots',deletePilot,null,401);
  await call('pilots',deletePilot,'local-submit',401);
  await call('pilots',deletePilot,'local-admin',403,'https://elsewhere.test');
  await call('pilots',{action:'delete',pilot_id:[]},'local-admin',400);
  await call('pilots',deletePilot,'local-admin',409);
  await call('pilots',{action:'close',pilot_id:p2.pilot_id},'local-admin');
  assert.equal((await call('pilot-results?pilot_id='+p2.pilot_id,null,'local-admin')).summary.sessions,2);
  await call('pilots',deletePilot,'local-admin');
  await call('pilots',deletePilot,'local-admin',404);
  await call('pilots?pilot_id='+p2.pilot_id,null,'local-admin',404);
  await call('pilot-results?pilot_id='+p2.pilot_id,null,'local-admin',404);
  await call('pilot-sessions?pilot='+p2.invitation,null,null,404);
  await call('pilot-sessions?session_id='+early.session_id,null,early.credential,401);
  await call('pilot-sessions?session_id='+activeForDeletion.session_id,null,activeForDeletion.credential,401);
  const countsOutput=sql(`SELECT (SELECT COUNT(*) FROM recognition_pilots WHERE pilot_id='${p2.pilot_id}') AS pilots, (SELECT COUNT(*) FROM recognition_sessions WHERE pilot_id='${p2.pilot_id}') AS sessions, (SELECT COUNT(*) FROM recognition_attempts a JOIN recognition_sessions s USING(session_id) WHERE s.pilot_id='${p2.pilot_id}') AS attempts;`);
  const counts=JSON.parse(countsOutput.slice(countsOutput.indexOf('[')))[0].results[0];
  assert.deepEqual({pilots:counts.pilots,sessions:counts.sessions,attempts:counts.attempts},{pilots:0,sessions:0,attempts:0});
  assert.equal((await call('pilots?pilot_id='+pilot.pilot_id,null,'local-admin')).config.icons.length,20);
  assert.equal((await call('study-results',null,'local-admin')).includes('pilot_selection_regression'),true);

  console.log('PASS: local D1 migration preservation, frozen snapshots, randomized schedules, auth, validation, interruption, idempotency, progressive completion, summaries, exports, nomination submission/replacement, guarded deletion/cascade, 103-trial controlled completion, fixed-size validation, retired invitations, migration record retention and size-specific accuracy/latency, retained pilot results, guarded pilot deletion and existing routes.');
} catch(error) { console.error(serverOutput); throw error; } finally { server?.kill('SIGTERM'); }
