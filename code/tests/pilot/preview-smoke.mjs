import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
const base=process.env.PILOT_PREVIEW_URL || 'https://codex-icon-recognition-pilot.glyph-perception-dashboard.pages.dev';
const secrets=JSON.parse(readFileSync('tmp/pilot-preview-secrets.json')), catalog=JSON.parse(readFileSync('dist/dashboard/study_selection_data.json')), set=catalog.sets[0];
async function call(path,data,credential=secrets.STUDY_ADMIN_KEY,status=200) {
 const response=await fetch(base+'/api/'+path,{method:data?'POST':'GET',headers:{Authorization:`Bearer ${credential}`,Origin:base,...(data?{'Content-Type':'application/json'}:{})},...(data?{body:JSON.stringify(data)}:{})});
 assert.equal(response.status,status,await response.clone().text());return response.json();
}
const p=await call('pilots',{action:'create',title:'PREVIEW TEST — browser usability checks',size_levels:[6,8,10,12,14],protocol_version:"icon-recognition-controlled-v2",submission_id:'preview-pilot-fixture',set_id:set.set_id,updated_at:'preview-fixture',icon_ids:set.icons.slice(0,20).map(i=>i.icon_id)},undefined,201);
const s=await call('pilot-sessions',{pilot:p.invitation,viewport:{width:1280,height:900,dpr:1}},'',201);
const view=await call('pilot-sessions?session_id='+s.session_id,null,s.credential);assert.equal(view.schedule.length,103);
const aid=crypto.randomUUID();await call('pilot-trials',{action:'start',session_id:s.session_id,trial_index:0,attempt_id:aid},s.credential);
const answer={action:'answer',session_id:s.session_id,attempt_id:aid,response:{category:'unidentified',selected_id:null,confidence:null,final_size:view.schedule[0].assigned_size,duration_ms:2200,choice_onset_ms:1550,input_method:"mouse",enlargements:[]}};
await call('pilot-trials',answer,s.credential);await call('pilot-trials',answer,s.credential);
await call('pilot-completion',{action:'end',session_id:s.session_id},s.credential);
const full=await call('pilot-results?pilot_id='+p.pilot_id+'&format=full');assert.equal(full.attempts.length,1);assert.equal(full.sessions[0].status,'ended');
await call('pilot-results?pilot_id='+p.pilot_id,null,s.credential,401);
writeFileSync('tmp/pilot-preview-invitation.json',JSON.stringify({base,pilot_id:p.pilot_id,invitation:p.invitation}));
console.log('PASS: isolated preview invitation, session, trial retry, early end, results and authorization.');
