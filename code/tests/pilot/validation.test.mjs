import {test} from 'node:test';
import assert from 'node:assert/strict';
import {schedule,validLevels,validateResponse,participantConfig,body,interruption,PROTOCOL} from '../../../functions/lib/pilot.js';
import {selectAlternatives} from '../../../functions/lib/controlled-pilot.js';
import {csvCell} from '../../../functions/api/pilot-results.js';
const featureIds=['a','b','c','d','e','f','principal_axis_orientation_v2'];
const icons=Array.from({length:20},(_,i)=>({icon_id:String(i).padStart(2,'0'),features:Object.fromEntries(featureIds.map((f,j)=>[f,j===6?i*9:i*(j+1)]))}));
const config={protocol_version:PROTOCOL,size_levels:[6,8,10,12,14],exposure_ms:1500,...selectAlternatives(icons,featureIds)};
test('100 target-size combinations, 3 distinct practice targets, five distinct candidates including target',()=>{
 for(let i=0;i<50;i++){
  const s=schedule(icons.map(x=>x.icon_id),config);assert.equal(s.length,103);
  assert.equal(new Set(s.slice(0,3).map(t=>t.target_id)).size,3);
  assert.equal(new Set(s.slice(3).map(t=>`${t.target_id}:${t.assigned_size}`)).size,100);
  for(const t of s){assert.equal(t.grid.length,5);assert.equal(new Set(t.grid).size,5);assert.ok(t.grid.includes(t.target_id));assert.deepEqual(t.grid.filter(id=>id!==t.target_id).sort(),[...config.alternatives[t.target_id].similar,...config.alternatives[t.target_id].dissimilar].sort());}
 }
});
test('only fixed controlled sizes and protocol are runnable',()=>{
 assert.ok(validLevels([6,8,10,12,14]));for(const v of [[4,6,8],[],[14,12,10,8,6],[6,8,10,12],null])assert.equal(validLevels(v),false);
 assert.throws(()=>schedule(icons.map(i=>i.icon_id),{protocol_version:'icon-recognition-usability-v1'}),e=>e.status===410);
});
test('nearest/farthest selection is stable with equal values, finite and does not use labels',()=>{
 const same=icons.map(icon=>({...icon,features:Object.fromEntries(featureIds.map(f=>[f,0]))}));
 const r=selectAlternatives(same,featureIds);assert.deepEqual(r.alternatives['00'].similar,['01','02']);assert.deepEqual(r.alternatives['00'].dissimilar,['18','19']);
 assert.ok(r.distance_spec.scales.every(Number.isFinite));
 assert.throws(()=>selectAlternatives([{icon_id:'bad',features:{}}],featureIds));
});
test('axial orientation treats 0 and 180 as identical and 179 as near 0',()=>{
 const angles=[0,180,179,90,70];const points=angles.map((angle,i)=>({icon_id:String(i),features:Object.fromEntries(featureIds.map(f=>[f,f==='principal_axis_orientation_v2'?angle:0]))}));
 const r=selectAlternatives(points,featureIds).alternatives['0'];assert.equal(r.ranked[0].distance,0);assert.deepEqual(r.similar,['1','2']);assert.equal(r.ranked.at(-1).id,'3');
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
