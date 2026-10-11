import {test} from 'node:test';
import assert from 'node:assert/strict';
import {schedule,validLevels,validateResponse,participantConfig,body,interruption,PROTOCOL} from '../../../functions/lib/pilot.js';
import {selectAlternatives, sampleIndex} from '../../../functions/lib/controlled-pilot.js';
import {csvCell,onRequestGet} from '../../../functions/api/pilot-results.js';
const featureIds=['a','b','c','d','e','f','principal_axis_orientation_v2'];
const imageSpec={version:'white-rgb-lanczos-v1',source_size:[256,256],sizes:[6,8,10,12,14],pillow_version:'test',rendering:'white RGB LANCZOS'};
const checks=i=>({source_sha256:i.toString(16).padStart(64,'0'),size_sha256:Object.fromEntries(imageSpec.sizes.map(s=>[s,i.toString(16).padStart(64,'0')]))});
const seed='a'.repeat(64);
const icons=Array.from({length:20},(_,i)=>({icon_id:String(i).padStart(2,'0'),image_checks:checks(i),features:Object.fromEntries(featureIds.map((f,j)=>[f,j===6?i*9:i*(j+1)]))}));
const config={protocol_version:PROTOCOL,size_levels:[6,8,10,12,14],exposure_ms:1500,...await selectAlternatives(icons,featureIds,imageSpec,seed)};
test('100 target-size combinations, 3 distinct practice targets, five distinct candidates including target',()=>{
 for(let i=0;i<50;i++){
  const s=schedule(icons.map(x=>x.icon_id),config);assert.equal(s.length,103);
  assert.equal(new Set(s.slice(0,3).map(t=>t.target_id)).size,3);
  for(const id of icons.map(i=>i.icon_id))assert.deepEqual(s.slice(3).filter(t=>t.target_id===id).map(t=>t.grid.indexOf(id)).sort(),[0,1,2,3,4]);
  assert.equal(new Set(s.slice(3).map(t=>`${t.target_id}:${t.assigned_size}`)).size,100);
  for(const t of s){assert.equal(t.grid.length,5);assert.equal(new Set(t.grid).size,5);assert.ok(t.grid.includes(t.target_id));assert.deepEqual(t.grid.filter(id=>id!==t.target_id).sort(),[...config.alternatives[t.target_id].similar,...config.alternatives[t.target_id].dissimilar].sort());}
 }
});
test('only fixed controlled sizes and protocol are runnable',()=>{
 assert.ok(validLevels([6,8,10,12,14]));for(const v of [[4,6,8],[],[14,12,10,8,6],[6,8,10,12],null])assert.equal(validLevels(v),false);
 assert.throws(()=>schedule(icons.map(i=>i.icon_id),{protocol_version:'icon-recognition-usability-v1'}),e=>e.status===410);
});
test('seeded band selection is stable with ties, finite and does not use labels',async()=>{
 const same=icons.map(icon=>({...icon,features:Object.fromEntries(featureIds.map(f=>[f,0]))}));
 const r=await selectAlternatives(same,featureIds,imageSpec,seed);assert.deepEqual(r.alternatives['00'].similar,['01','02']);assert.ok(r.alternatives['00'].selected_ranks.dissimilar.every(r=>r>=12&&r<=16));assert.equal(r.alternatives['00'].diagnostics.near_distant_overlap,true);assert.deepEqual(r,await selectAlternatives(same,featureIds,imageSpec,seed));
 assert.ok(r.distance_spec.scales.every(Number.isFinite));
 await assert.rejects(selectAlternatives([{icon_id:'bad',features:{}}],featureIds,imageSpec,seed));
});
test('axial orientation treats 0 and 180 as identical and 179 as near 0',async()=>{
 const angles=[0,180,179,90,70,...Array.from({length:15},(_,i)=>40+i)];const points=angles.map((angle,i)=>({icon_id:String(i),image_checks:checks(i),features:Object.fromEntries(featureIds.map(f=>[f,f==='principal_axis_orientation_v2'?angle:0]))}));
 const r=(await selectAlternatives(points,featureIds,imageSpec,seed)).alternatives['0'];assert.equal(r.ranked[0].distance,0);assert.deepEqual(r.similar,['1','2']);assert.equal(r.ranked.at(-1).id,'3');
});
test('assigned-size responses validate timing, membership, input and no enlargement',()=>{
 const assigned={grid:['a','b','c','d','e'],assigned_size:8};
 const response={category:'selected',selected_id:'b',confidence:3,final_size:8,duration_ms:2200,choice_onset_ms:1550,input_method:'keyboard',enlargements:[]};
 const saved=validateResponse(response,assigned,config);assert.equal(saved.response_time_ms,650);assert.equal(saved.selected_position,2);assert.equal(saved.assigned_size,8);
 for(const extra of [{confidence:0},{selected_id:'outside'},{duration_ms:1400},{choice_onset_ms:1000},{choice_onset_ms:2300},{input_method:'script'},{final_size:10},{enlargements:[{at_ms:1600,size:10}]}])assert.throws(()=>validateResponse({...response,...extra},assigned,config));
 assert.equal(validateResponse({...response,category:'unidentified',selected_id:null,confidence:null},assigned,config).selected_position,null);
 assert.equal(interruption('blur',1700,[],config,assigned).final_size,8);assert.throws(()=>interruption('blur',1700,[{}],config,assigned));
});
test('participant configuration excludes features, alternatives and reviewer provenance',()=>{
 const result=participantConfig({...config,icons:[{icon_id:'a',image:'/image.png',label:'secret',features:{a:1}}],source:{reviewer_code:'secret'},target_px:128});
 assert.equal(result.source,undefined);assert.equal(result.icons[0].label,undefined);assert.equal(result.icons[0].features,undefined);assert.equal(result.alternatives,undefined);assert.equal(result.recorded_count,100);
});
test('CSV prevents formulas and correctly quotes embedded newlines',()=>{
 for(const text of ['=SUM(1,2)',' +1','-1','@formula','\tformula','\nformula'])assert.ok(csvCell(text).startsWith('"\''));
 assert.equal(csvCell('a,"b"\n'), '"a,""b""\n"');
});
test('chunked request body is bounded',async()=>{
 const req=new Request('https://example.test/api/pilots',{method:'POST',headers:{Origin:'https://example.test','Content-Type':'application/json'},body:JSON.stringify({x:'x'.repeat(33000)})});
 await assert.rejects(body(req),e=>e.status===413);
});

test('source duplicates are skipped with original ranks; small collisions retained',async()=>{
 const pool=icons.map(i=>({...i,image_checks:structuredClone(i.image_checks)}));
 pool[1].image_checks.source_sha256=pool[0].image_checks.source_sha256;
 for(const i of pool)i.image_checks.size_sha256[6]='f'.repeat(64);
 const r=await selectAlternatives(pool,featureIds,imageSpec,seed);
 assert.ok(!r.alternatives['00'].similar.includes('01'));
 assert.ok(r.alternatives['00'].selected_ranks.dissimilar.every(x=>x>=12&&x<=16));
 assert.equal(r.collision_diagnostics.filter(c=>c.size===6).length,200);
 assert.equal(r.collision_diagnostics.filter(c=>c.target_involved).length,80);
 const identical=pool.map(i=>({...i,image_checks:pool[0].image_checks}));
 await assert.rejects(selectAlternatives(identical,featureIds,imageSpec,seed),/00: insufficient/);
 const invalid=structuredClone(pool); delete invalid[0].image_checks.size_sha256[8];
 await assert.rejects(selectAlternatives(invalid,featureIds,imageSpec,seed),/metadata/);
 await assert.rejects(selectAlternatives(pool,featureIds,null,seed),/metadata/);
});
test('counter stream distributes seeds over all ten valid combinations',async()=>{
 const counts=Array(10).fill(0);
 for(let i=0;i<2000;i++)counts[await sampleIndex(i.toString(16).padStart(64,'0'),'target',10)]++;
 assert.ok(counts.every(n=>n>140&&n<260),counts.join(','));
});
test('legacy controlled snapshots keep independently shuffled schedules',()=>{
 const legacy={...config}; delete legacy.schedule_rule_version;
 assert.equal(schedule(icons.map(i=>i.icon_id),legacy).length,103);
});
test('band exhaustion rejects without widening and distance formula stays unchanged',async()=>{
 const baseline=await selectAlternatives(icons,featureIds,imageSpec,seed);
 const pool=structuredClone(icons);
 for(const item of baseline.alternatives['00'].ranked.filter(x=>x.rank>=12&&x.rank<=16)) pool.find(i=>i.icon_id===item.id).image_checks.source_sha256=pool[0].image_checks.source_sha256;
 await assert.rejects(selectAlternatives(pool,featureIds,imageSpec,seed),/00: no source-distinct pair in original ranks 12–16/);
 const mean=9.5, scale=Math.sqrt(icons.reduce((n,_,i)=>n+(i-mean)**2,0)/20);
 for(const entry of baseline.alternatives['00'].ranked){const i=Number(entry.id), angle=i*9;assert.ok(Math.abs(entry.distance-Math.sqrt(6*(i/scale)**2+(Math.min(angle,180-angle)/90)**2))<1e-12);}
 // Every pair in a tied five-candidate band is reachable, without replacing original ranks.
 const tied=icons.map(i=>({...i,features:Object.fromEntries(featureIds.map(f=>[f,0]))}));
 const pairs=new Set();
 for(let i=0;i<80;i++){const r=await selectAlternatives(tied,featureIds,imageSpec,i.toString(16).padStart(64,'0'));pairs.add(r.alternatives['00'].dissimilar.join(','));}
 assert.equal(pairs.size,10);
});

test('collision answers retain ID scoring and accuracy; CSV exposes pair and target flag',async()=>{
 const cfg={...config,source:{set_id:'fixture'},collision_diagnostics:[{target_id:'00',size:6,icon_pair:['00','01'],target_involved:true}]};
 const pilot={config_json:JSON.stringify(cfg)};
 const session={session_id:'s',schedule_json:JSON.stringify([{target_id:'00',assigned_size:6}]),viewport_json:'{}',debrief_json:null};
 const attempt={session_id:'s',trial_index:0,target_id:'00',phase:'recorded',state:'answered',correct:0,repeated_exposure:0,grid_json:'["00","01"]',response_json:JSON.stringify({category:'selected',selected_id:'01',assigned_size:6,final_size:6,confidence:3,enlargements:[],response_time_ms:500}),interruption_json:null};
 const db={prepare:query=>({bind(){return this;},async first(){return pilot;},async all(){return {results:query.includes('FROM recognition_sessions')?[session]:[attempt]};}})};
 const request=format=>new Request('https://example.test/api/pilot-results?pilot_id=p'+format,{headers:{Authorization:'Bearer test'}});
 const env={STUDY_ADMIN_KEY:'test',STUDY_SELECTION_DB:db};
 const result=await (await onRequestGet({request:request(''),env})).json();
 assert.equal(result.summary.eligible_recorded_answers,1);assert.equal(result.summary.eligible_collision_answers,1);assert.equal(result.summary.accuracy,0);
 const csv=await (await onRequestGet({request:request('&format=csv'),env})).text();assert.ok(csv.includes('target_involved'));assert.ok(csv.includes('"true"'));
});
